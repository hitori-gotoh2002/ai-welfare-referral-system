(() => {
  if (typeof state === "undefined" || typeof services === "undefined") return;

  const ageTargetPatterns = {
    아동: /아동|영유아|유아|어린이|초등학생|초등|미취학/,
    청소년: /청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원/,
    청년: /청년|대학생|취업준비|구직청년/,
    중장년: /중장년|장년|중년/,
    노인: /노인|어르신|고령|독거노인|독거\s*어르신|65\s*세\s*이상/,
  };
  const targetGroupPatterns = {
    ...ageTargetPatterns,
    장애인: /장애인|발달장애|장애\s*정도|장애\s*아동/,
    임산부: /임산부|임신|출산|산모|영아/,
    한부모: /한부모|조손|미혼모|미혼부/,
    여성폭력: /가정폭력|성폭력|성매매|스토킹|여성긴급전화|1366/,
    국가유공자: /국가유공자|보훈|참전|유공자/,
  };
  const broadTargetPattern = /전\s*국민|전체|누구나|일반|저소득|취약계층|위기가구|기초생활|차상위|가구|가족|구직자/;
  const crisisPattern = /긴급|위기|체납|퇴거|노숙|폭력|학대|자살|자해|위험|실직|단전|단수|입원|응급/;
  const stopwords = new Set([
    "지원",
    "서비스",
    "복지",
    "대상",
    "가구",
    "상담",
    "필요",
    "확인",
    "연계",
    "신청",
    "제공",
    "사업",
    "운영",
    "프로그램",
    "현재",
    "최근",
    "어려움",
    "어렵고",
    "있습니다",
    "합니다",
    "대한",
    "관련",
    "가능",
  ]);

  function installPackageUxStyles() {
    if (document.querySelector("#package-search-ux-patch")) return;
    const style = document.createElement("style");
    style.id = "package-search-ux-patch";
    style.textContent = `
      .service-card.in-package,
      .package-candidate-row.in-package {
        border-color: #2f766f;
        background: #f1faf7;
      }
      .service-card.excluded-from-package,
      .package-candidate-row.excluded-from-package {
        border-color: #d7c68a;
        background: #fffaf0;
      }
      .service-card.target-mismatch,
      .package-candidate-row.target-mismatch {
        opacity: 0.62;
      }
      .package-candidate-list {
        display: grid;
        gap: 10px;
        min-width: 0;
      }
      .package-candidate-row {
        display: grid;
        grid-template-columns: 20px minmax(0, 1fr) auto;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        min-width: 0;
      }
      .package-candidate-main {
        min-width: 0;
      }
      .package-candidate-main strong,
      .package-item-main strong {
        overflow-wrap: anywhere;
      }
      .package-candidate-main .tiny {
        overflow-wrap: anywhere;
      }
      .package-candidate-actions {
        display: flex;
        align-items: center;
        gap: 6px;
        min-width: 0;
      }
      .package-candidate-row input[type="checkbox"] {
        width: 18px;
        height: 18px;
      }
      .package-search-tools {
        margin-top: 6px;
        grid-template-columns: minmax(160px, 1.4fr) repeat(3, minmax(86px, 0.7fr));
        min-width: 0;
        width: 100%;
      }
      .package-layout .package-search-tools,
      .commercial-ui .package-layout .package-search-tools {
        grid-template-columns: minmax(160px, 1.4fr) repeat(3, minmax(86px, 0.7fr)) !important;
        box-sizing: border-box;
        overflow: hidden;
      }
      .package-layout .package-search-tools > input,
      .package-layout .package-search-tools > select {
        box-sizing: border-box;
        min-width: 0;
        width: 100%;
      }
      .package-item .priority-buttons {
        flex-wrap: wrap;
      }
      .package-layout > .workspace-panel {
        min-width: 0;
      }
      .package-layout .panel-body,
      .package-layout .inline-section,
      .package-layout .source-stack {
        min-width: 0;
      }
      .package-layout .package-candidate-row {
        box-sizing: border-box;
        width: 100%;
      }
      .package-loading-note {
        color: var(--muted);
        font-size: 13px;
        font-weight: 800;
      }
      .package-loading-note .icon {
        animation: spin 1s linear infinite;
      }
      @media (max-width: 1320px) {
        .package-layout {
          grid-template-columns: minmax(280px, 0.78fr) minmax(0, 1.22fr);
        }
      }
      @media (max-width: 1180px) {
        .package-layout {
          grid-template-columns: 1fr;
        }
      }
      @media (max-width: 720px) {
        .package-candidate-row {
          grid-template-columns: 20px minmax(0, 1fr);
        }
        .package-candidate-actions {
          grid-column: 2;
          justify-content: flex-start;
        }
        .package-search-tools,
        .commercial-ui .package-search-tools {
          grid-template-columns: 1fr !important;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function ageGroupsFromText(text) {
    const value = String(text || "");
    const groups = new Set();
    Object.entries(ageTargetPatterns).forEach(([group, pattern]) => {
      if (pattern.test(value)) groups.add(group);
    });
    for (const match of value.matchAll(/(?<!\d)(\d{1,3})\s*세/g)) {
      const age = Number(match[1]);
      if (age < 13) groups.add("아동");
      else if (age < 19) groups.add("청소년");
      else if (age < 40) groups.add("청년");
      else if (age >= 65) groups.add("노인");
      else groups.add("중장년");
    }
    return groups;
  }

  function targetGroupsFromText(text) {
    const value = String(text || "");
    const groups = ageGroupsFromText(value);
    Object.entries(targetGroupPatterns).forEach(([group, pattern]) => {
      if (pattern.test(value)) groups.add(group);
    });
    return groups;
  }

  function caseContextText() {
    const checks = Array.isArray(state.structured?.riskChecks)
      ? state.structured.riskChecks.flatMap((item) => [item?.label, item?.text])
      : [];
    return [
      state.case?.title,
      state.case?.memo,
      state.case?.targetType,
      state.case?.region,
      ...(state.case?.issueTypes || []),
      state.structured?.target,
      state.structured?.region,
      state.structured?.urgency,
      ...(state.structured?.needs || []),
      ...(state.structured?.keywords || []),
      ...checks,
    ]
      .filter(Boolean)
      .join(" ");
  }

  function currentCaseAgeGroups() {
    return ageGroupsFromText(caseContextText());
  }

  function currentCaseTargetGroups() {
    return targetGroupsFromText(caseContextText());
  }

  function serviceAgeGroups(service) {
    return ageGroupsFromText(serviceText(service));
  }

  function serviceText(service) {
    return [
      service?.name,
      service?.target,
      service?.summary,
      service?.eligibility,
      service?.support,
      service?.process,
      service?.selectionCriteria,
      ...(service?.docs || []),
      ...(service?.domains || []),
    ]
      .filter(Boolean)
      .join(" ");
  }

  function serviceTargetGroups(service) {
    return targetGroupsFromText(serviceText(service));
  }

  function serviceHasBroadTarget(service) {
    return broadTargetPattern.test([service?.target, service?.eligibility, service?.summary].filter(Boolean).join(" "));
  }

  function serviceMatchesCaseTarget(service) {
    const caseGroups = currentCaseTargetGroups();
    const targetGroups = serviceTargetGroups(service);
    if (targetGroups.size && caseGroups.size) return [...caseGroups].some((group) => targetGroups.has(group));
    if (targetGroups.size && !caseGroups.size && !serviceHasBroadTarget(service)) return false;
    return true;
  }

  function meaningfulTokens(text) {
    return Array.from(
      new Set(
        String(text || "")
          .match(/[가-힣A-Za-z0-9]{2,}/g)
          ?.filter((token) => !stopwords.has(token.toLowerCase()) && !/^\d+$/.test(token)) || []
      )
    );
  }

  function caseTerms(needs) {
    const text = caseContextText().toLowerCase();
    const terms = [];
    (needs || []).forEach((need) => {
      terms.push(need);
      (keywordMap[need] || []).forEach((word) => {
        if (text.includes(String(word).toLowerCase())) terms.push(word);
      });
    });
    (state.structured?.keywords || []).forEach((keyword) => {
      if (String(keyword).length >= 2 && !stopwords.has(String(keyword).toLowerCase())) terms.push(keyword);
    });
    terms.push(...meaningfulTokens(caseContextText()).slice(0, 24));
    terms.push(...currentCaseTargetGroups());
    return Array.from(new Set(terms.filter((term) => String(term).length >= 2))).slice(0, 36);
  }

  function keywordHitCount(service, terms) {
    const haystack = serviceText(service).toLowerCase();
    return terms.filter((term) => haystack.includes(String(term).toLowerCase())).length;
  }

  function isCaseCrisis() {
    return state.case?.urgency === "긴급" || state.structured?.urgency === "긴급" || crisisPattern.test(caseContextText());
  }

  function scoreService(service, needs) {
    if (!serviceMatchesCaseTarget(service)) return -1;
    const domains = Array.isArray(service.domains) ? service.domains : [];
    const overlap = domains.filter((domain) => needs.includes(domain)).length;
    const terms = caseTerms(needs);
    const hits = keywordHitCount(service, terms);
    const caseGroups = currentCaseTargetGroups();
    const serviceGroups = serviceTargetGroups(service);
    const targetHits = [...caseGroups].filter((group) => serviceGroups.has(group)).length;
    const targetMatch = targetHits ? 1 : 0;
    const nonTargetHits = Math.max(hits - targetHits, 0);
    const externalPublic =
      Boolean(service.externalId) ||
      String(service.id || "").startsWith("중앙:") ||
      String(service.id || "").startsWith("지자체:");
    if (!overlap && !hits && !targetMatch) return -1;
    if (!overlap && !nonTargetHits) return -1;
    if (externalPublic && overlap && !hits && !targetMatch) return -1;
    const region = state.case?.region && (service.region === "전국" || state.case.region.includes(service.region)) ? 1 : 0;
    const urgentBonus = service.urgency === "긴급" && isCaseCrisis() && (overlap || hits) ? 3 : 0;
    const urgentPenalty = service.urgency === "긴급" && !isCaseCrisis() ? -4 : 0;
    const sourceBonus =
      ["기관", "민간"].includes(service.source) && needs.some((need) => ["심리", "돌봄", "안전"].includes(need)) ? 2 : 0;
    return overlap * 10 + Math.min(hits, 6) * 4 + region * 2 + targetMatch * 7 + urgentBonus + urgentPenalty + sourceBonus;
  }

  function serviceMatchesFilters(service, q) {
    const searchable = [
      service.name,
      service.summary,
      service.target,
      service.region,
      service.source,
      ...(service.domains || []),
    ]
      .join(" ")
      .toLowerCase();
    const qMatch = !q || searchable.includes(q);
    const sourceMatch = state.filters.source === "전체" || service.source === state.filters.source;
    const domainMatch = state.filters.domain === "전체" || (service.domains || []).includes(state.filters.domain);
    const urgencyMatch = state.filters.urgency === "전체" || service.urgency === state.filters.urgency;
    return qMatch && sourceMatch && domainMatch && urgencyMatch;
  }

  function compatibleRankedServices(needs) {
    return services
      .map((service) => ({ service, score: scoreService(service, needs) }))
      .filter((item) => item.score >= 0)
      .sort((a, b) => b.score - a.score)
      .map((item) => item.service);
  }

  function patchedFilteredServices() {
    const q = state.filters.q.trim().toLowerCase();
    const needs = state.structured?.needs || state.case.issueTypes || [];
    return services
      .filter((service) => serviceMatchesFilters(service, q))
      .map((service) => ({
        service,
        compatible: serviceMatchesCaseTarget(service),
        score: scoreService(service, needs),
      }))
      .filter((item) => item.compatible || q)
      .sort((a, b) => {
        if (a.compatible !== b.compatible) return a.compatible ? -1 : 1;
        if (b.score !== a.score) return b.score - a.score;
        return String(a.service.name || "").localeCompare(String(b.service.name || ""), "ko");
      })
      .map((item) => item.service);
  }

  function selectedPackageOrCreate() {
    if (!Array.isArray(state.packages) || !state.packages.length) {
      generatePackagesLocal({ show: false });
    }
    return selectedPackage();
  }

  function packageItemFor(serviceId) {
    const pkg = state.packages?.find((item) => item.id === state.selectedPackageId) || state.packages?.[0];
    return pkg?.items?.find((item) => item.serviceId === serviceId);
  }

  function packageStatus(serviceId) {
    const item = packageItemFor(serviceId);
    return {
      exists: Boolean(item),
      included: Boolean(item && item.included),
      excluded: Boolean(item && !item.included),
    };
  }

  function filterPackageItems(items, needs) {
    const selected = (items || []).filter((item) => {
      const service = services.find((entry) => entry.id === item.serviceId);
      return service && serviceMatchesCaseTarget(service);
    });
    const selectedIds = new Set(selected.map((item) => item.serviceId));
    const domains = new Set(
      selected
        .filter((item) => item.included)
        .map((item) => services.find((service) => service.id === item.serviceId))
        .filter(Boolean)
        .flatMap((service) => service.domains || [])
    );
    const ranked = compatibleRankedServices(needs);

    needs.slice(0, 4).forEach((need) => {
      if (domains.has(need)) return;
      const found = ranked.find((service) => (service.domains || []).includes(need) && !selectedIds.has(service.id));
      if (!found) return;
      selected.push({ serviceId: found.id, included: true });
      selectedIds.add(found.id);
      (found.domains || []).forEach((domain) => domains.add(domain));
    });

    while (selected.filter((item) => item.included).length < 3) {
      const found = ranked.find((service) => !selectedIds.has(service.id));
      if (!found) break;
      selected.push({ serviceId: found.id, included: true });
      selectedIds.add(found.id);
    }

    return selected;
  }

  function filterStatePackages() {
    if (!Array.isArray(state.packages) || !state.packages.length) return;
    const needs = state.structured?.needs?.length ? state.structured.needs : state.case?.issueTypes || [];
    state.packages = state.packages.map((pkg) => ({
      ...pkg,
      items: filterPackageItems(pkg.items, needs),
    }));
    if (!state.packages.some((pkg) => pkg.id === state.selectedPackageId)) {
      state.selectedPackageId = state.packages[0]?.id || null;
    }
  }

  function ensurePackageReady({ asyncRefresh = true, show = false } = {}) {
    if (!state.structured) return;
    let needsRefresh = false;
    if (!Array.isArray(state.packages) || !state.packages.length) {
      generatePackagesLocal({ show });
      state.selectedPackageId = state.packages[0]?.id || null;
      needsRefresh = true;
    } else if (!state.selectedPackageId) {
      state.selectedPackageId = state.packages[0]?.id || null;
    }
    filterStatePackages();
    if (asyncRefresh && needsRefresh) {
      Promise.resolve(generatePackages({})).catch(() => {
        filterStatePackages();
        render();
      });
    }
  }

  function toggleServiceInSelectedPackage(serviceId) {
    const service = services.find((entry) => entry.id === serviceId);
    if (!service) return;
    if (!serviceMatchesCaseTarget(service)) {
      showToast("상담 대상 연령대와 맞지 않는 서비스는 패키지에 추가하지 않았습니다.");
      return;
    }
    const pkg = selectedPackageOrCreate();
    const item = pkg.items.find((entry) => entry.serviceId === serviceId);
    if (item) {
      item.included = !item.included;
      showToast(item.included ? "패키지에 다시 포함했습니다." : "패키지에서 제외했습니다.");
    } else {
      pkg.items.push({ serviceId, included: true });
      showToast("패키지에 서비스를 추가했습니다.");
    }
    state.lastReport = null;
    filterStatePackages();
    render();
  }

  function renderSearchTools(className = "") {
    return `
      <div class="search-tools ${className}">
        <input value="${escapeHtml(state.filters.q)}" placeholder="서비스명, 대상, 키워드 검색" oninput="updateFilter('q', this.value)" />
        <select onchange="updateFilter('source', this.value)">
          ${["전체", "중앙", "지자체", "민간", "기관"].map((item) => option(item, state.filters.source)).join("")}
        </select>
        <select onchange="updateFilter('domain', this.value)">
          ${["전체", ...NEEDS].map((item) => option(item, state.filters.domain)).join("")}
        </select>
        <select onchange="updateFilter('urgency', this.value)">
          ${["전체", "긴급", "일반"].map((item) => option(item, state.filters.urgency)).join("")}
        </select>
      </div>
    `;
  }

  function renderPackageBadge(service) {
    const status = packageStatus(service.id);
    const badges = [];
    if (status.included) badges.push(pill("패키지 포함", "green"));
    if (status.excluded) badges.push(pill("패키지 제외", "amber"));
    if (!serviceMatchesCaseTarget(service)) badges.push(pill("대상 확인 필요", "red"));
    return badges.join("");
  }

  function patchedRenderServiceCard(service) {
    const status = packageStatus(service.id);
    const compatible = serviceMatchesCaseTarget(service);
    const classes = [
      "service-card",
      state.selectedServiceId === service.id ? "selected" : "",
      status.included ? "in-package" : "",
      status.excluded ? "excluded-from-package" : "",
      !compatible ? "target-mismatch" : "",
    ]
      .filter(Boolean)
      .join(" ");
    return `
      <article class="${classes}">
        <div class="service-head">
          <div class="service-title">
            <strong>${escapeHtml(service.name)}</strong>
            <div class="pill-row">
              ${pill(service.source, "blue")}
              ${pill(service.urgency, service.urgency === "긴급" ? "red" : "")}
              ${(service.domains || []).map((domain) => pill(domain, needsColor(domain))).join("")}
              ${renderPackageBadge(service)}
            </div>
          </div>
          <button class="icon-btn" title="선택" onclick="state.selectedServiceId='${service.id}'; render();">${icon("mouse-pointer-click")}</button>
        </div>
        <div class="service-summary">${escapeHtml(service.summary)}</div>
        <div class="button-row">
          <button class="btn ghost" onclick="openServiceDetail('${service.id}')">${icon("panel-top-open")} 상세</button>
          <button class="btn ${status.included ? "secondary" : "ghost"}" onclick="toggleServiceInSelectedPackage('${service.id}')">
            ${icon(status.included ? "check-square" : "square")} ${status.included ? "패키지 해제" : "패키지 선택"}
          </button>
        </div>
      </article>
    `;
  }

  function renderPackageCandidateRow(service, pkg) {
    const item = pkg.items.find((entry) => entry.serviceId === service.id);
    const included = Boolean(item?.included);
    const excluded = Boolean(item && !item.included);
    const compatible = serviceMatchesCaseTarget(service);
    const classes = [
      "package-candidate-row",
      included ? "in-package" : "",
      excluded ? "excluded-from-package" : "",
      !compatible ? "target-mismatch" : "",
    ]
      .filter(Boolean)
      .join(" ");
    return `
      <div class="${classes}">
        <input type="checkbox" ${included ? "checked" : ""} ${!compatible ? "disabled" : ""} aria-label="패키지 포함 여부" onchange="toggleServiceInSelectedPackage('${service.id}')" />
        <div class="package-candidate-main">
          <strong>${escapeHtml(service.name)}</strong>
          <div class="tiny">${escapeHtml(service.summary || "")}</div>
          <div class="pill-row">
            ${pill(service.source, "blue")}
            ${(service.domains || []).slice(0, 4).map((domain) => pill(domain, needsColor(domain))).join("")}
            ${renderPackageBadge(service)}
          </div>
        </div>
        <div class="package-candidate-actions">
          <button class="icon-btn" title="상세" onclick="openServiceDetail('${service.id}')">${icon("panel-top-open")}</button>
        </div>
      </div>
    `;
  }

  function patchedRenderPackageItem(item, pkg) {
    const service = services.find((entry) => entry.id === item.serviceId);
    if (!service) return "";
    const index = pkg.items.findIndex((entry) => entry.serviceId === item.serviceId);
    return `
      <div class="package-item ${item.included ? "" : "excluded"}">
        <input type="checkbox" ${item.included ? "checked" : ""} aria-label="포함 여부" onchange="togglePackageItem('${service.id}')" />
        <div class="package-item-main">
          <strong>${escapeHtml(service.name)}</strong>
          <span class="tiny">${escapeHtml(service.source)} · ${escapeHtml(service.contact)}</span>
        </div>
        <div class="priority-buttons">
          <button class="icon-btn" title="상세" onclick="openServiceDetail('${service.id}')">${icon("panel-top-open")}</button>
          <button class="icon-btn" title="위로" ${index === 0 ? "disabled" : ""} onclick="movePackageItem('${service.id}', -1)">${icon("arrow-up")}</button>
          <button class="icon-btn" title="아래로" ${index === pkg.items.length - 1 ? "disabled" : ""} onclick="movePackageItem('${service.id}', 1)">${icon("arrow-down")}</button>
        </div>
      </div>
    `;
  }

  function patchedRenderPackageView() {
    if (!state.packages.length) generatePackagesLocal({ show: false });
    const pkg = selectedPackage();
    const included = selectedPackageServices();
    const searchResults = patchedFilteredServices();
    return `
      <div class="package-layout">
        <section class="workspace-panel">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">추천 패키지 목록</h2>
              <p class="panel-subtitle">${state.packageLoading ? "백엔드 추천을 갱신하는 중입니다." : "욕구·긴급도 기반 상위 3개"}</p>
            </div>
            <button class="btn ghost" ${state.packageLoading ? "disabled" : ""} onclick="generatePackages()">${icon(state.packageLoading ? "loader-2" : "refresh-cw")} 재생성</button>
          </div>
          <div class="panel-body package-list">
            ${state.packageLoading ? `<div class="package-loading-note">${icon("loader-2")} 추천 패키지를 갱신하고 있습니다. 현재 선택 항목은 유지됩니다.</div>` : ""}
            ${state.packages
              .map(
                (item) => `
                  <article class="package-card ${item.id === pkg.id ? "active" : ""}">
                    <div class="package-head">
                      <div class="package-title">
                        <strong>${escapeHtml(item.title)}</strong>
                        <span class="muted">${escapeHtml(item.summary)}</span>
                      </div>
                      <div class="score">${item.score}</div>
                    </div>
                    <div class="pill-row">
                      ${uniquePackageDomains(item).map((domain) => pill(domain, needsColor(domain))).join("")}
                    </div>
                    <button class="btn ${item.id === pkg.id ? "secondary" : "ghost"}" onclick="setSelectedPackage('${item.id}')">${icon("check-circle-2")} 선택</button>
                  </article>
                `
              )
              .join("")}
          </div>
        </section>
        <section class="workspace-panel">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">패키지 편집</h2>
              <p class="panel-subtitle">${escapeHtml(pkg.title)} · 포함 ${included.length}건</p>
            </div>
            <button class="btn primary" onclick="setView('report')">${icon("file-text")} 추천서 생성</button>
          </div>
          <div class="panel-body stack">
            ${pkg.items.map((entry) => patchedRenderPackageItem(entry, pkg)).join("")}
            <div class="inline-section">
              <div class="inline-section-head">
                <div>
                  <h2 class="panel-title">통합검색 후보 선택</h2>
                  <p class="panel-subtitle">검색 결과에서 패키지 포함 여부를 바로 조정합니다.</p>
                </div>
                ${pill(`${searchResults.length}건`, "blue")}
              </div>
              ${renderSearchTools("package-search-tools")}
              <div class="package-candidate-list">
                ${searchResults.length ? searchResults.map((service) => renderPackageCandidateRow(service, pkg)).join("") : `<div class="empty-state">검색 결과가 없습니다.</div>`}
              </div>
            </div>
            <div class="inline-section">
              <div class="inline-section-head">
                <div>
                  <h2 class="panel-title">기관 연결 리스트</h2>
                  <p class="panel-subtitle">서비스 문의처와 지역 기관 API 결과</p>
                </div>
                ${state.providerMeta ? pill(state.providerMeta.fallback ? "기관 API 폴백" : "기관 API 연결", state.providerMeta.fallback ? "amber" : "green") : ""}
              </div>
              <div class="source-stack">
                ${included
                  .map(
                    (service) => `
                      <div class="source-row">
                        <div>
                          <strong>${escapeHtml(service.name)}</strong>
                          <div class="tiny">${escapeHtml(service.contact)}</div>
                        </div>
                        ${pill(service.source, "blue")}
                      </div>
                    `
                  )
                  .join("")}
                ${
                  state.providerLoading
                    ? `<div class="empty-state">지역 기관 API를 불러오는 중입니다.</div>`
                    : state.providers
                        .map(
                          (provider) => `
                            <div class="source-row">
                              <div>
                                <strong>${escapeHtml(provider.name)}</strong>
                                <div class="tiny">${escapeHtml(provider.serviceName || provider.serviceType || "기관 서비스")} · ${escapeHtml(provider.region || state.case.region || "")}</div>
                                <div class="tiny">${escapeHtml(provider.address || "")}</div>
                              </div>
                              <div class="pill-row">
                                ${pill(provider.source || "기관", provider.source === "샘플" ? "" : "blue")}
                                ${provider.contact ? pill(provider.contact) : ""}
                              </div>
                            </div>
                          `
                        )
                        .join("")
                }
              </div>
            </div>
          </div>
        </section>
      </div>
    `;
  }

  try {
    serviceScore = scoreService;
  } catch (_error) {
    // Older browsers can ignore this fallback hook; backend scoring still applies.
  }

  refreshServicesFromBackend = async function patchedRefreshServicesFromBackend(token = state.viewToken) {
    try {
      const params = new URLSearchParams({
        q: state.filters.q,
        source: state.filters.source,
        domain: state.filters.domain,
        urgency: state.filters.urgency,
        needs: (state.structured?.needs || state.case.issueTypes).join(","),
        region: state.case.region || "",
        target: state.structured?.target || state.case.targetType || "",
        keywords: (state.structured?.keywords || []).join(","),
        memo: state.case.memo || "",
      });
      const data = await apiFetch(`/api/services?${params.toString()}`);
      if (token !== state.viewToken) return;
      services = data.services || services;
      state.apiStatus = "online";
      const llmSuffix = state.llmEnabled ? "+LLM" : "";
      state.apiMessage = data.meta?.fallback
        ? `백엔드 연결됨${llmSuffix} · 공공데이터 폴백`
        : `백엔드+공공데이터${llmSuffix} 연결됨`;
      if (!services.some((service) => service.id === state.selectedServiceId)) {
        state.selectedServiceId = services[0]?.id || null;
      }
      if (state.view === "search" && token === state.viewToken) render();
    } catch (error) {
      if (token !== state.viewToken) return;
      state.apiStatus = "offline";
      state.apiMessage = "백엔드 미연결 · 로컬 샘플로 동작";
    }
  };

  const nativeGeneratePackagesLocal = generatePackagesLocal;
  generatePackagesLocal = function patchedGeneratePackagesLocal(options) {
    const result = nativeGeneratePackagesLocal(options);
    filterStatePackages();
    return result;
  };

  const nativeGeneratePackages = generatePackages;
  generatePackages = async function patchedGeneratePackages(options = {}) {
    if (state.packageLoading) return state.packages;

    const nextView = options.goTo;
    const shouldNavigateImmediately = nextView === "packages";
    state.packageLoading = true;

    if (shouldNavigateImmediately && (!Array.isArray(state.packages) || !state.packages.length)) {
      generatePackagesLocal({ show: false });
      filterStatePackages();
      setView(nextView);
    } else if (shouldNavigateImmediately) {
      filterStatePackages();
      setView(nextView);
    } else {
      render();
    }

    try {
      const result = await nativeGeneratePackages({
        ...options,
        goTo: shouldNavigateImmediately ? undefined : nextView,
      });
      filterStatePackages();
      return result;
    } finally {
      state.packageLoading = false;
      filterStatePackages();
      render();
    }
  };

  const nativeInferStructure = inferStructure;
  inferStructure = async function patchedInferStructure(options = {}) {
    const nextView = options.goTo;
    await nativeInferStructure({ ...options, goTo: undefined });
    ensurePackageReady({ asyncRefresh: false, show: false });
    if (nextView) {
      setView(nextView);
    } else {
      render();
    }
  };

  const nativeInferStructureLocal = inferStructureLocal;
  inferStructureLocal = function patchedInferStructureLocal(options = {}) {
    const result = nativeInferStructureLocal(options);
    ensurePackageReady({ asyncRefresh: false, show: false });
    return result;
  };

  const nativeSetView = setView;
  setView = function patchedSetView(view) {
    if ((view === "search" || view === "packages" || view === "report") && state.structured) {
      ensurePackageReady({ asyncRefresh: false, show: false });
    }
    return nativeSetView(view);
  };

  addServiceToPackage = function patchedAddServiceToPackage(serviceId) {
    const service = services.find((entry) => entry.id === serviceId);
    if (service && !serviceMatchesCaseTarget(service)) {
      showToast("상담 대상 연령대와 맞지 않는 서비스는 패키지에 추가하지 않았습니다.");
      return;
    }
    const pkg = selectedPackageOrCreate();
    const item = pkg.items.find((entry) => entry.serviceId === serviceId);
    if (item) {
      item.included = true;
      showToast("패키지에 다시 포함했습니다.");
    } else {
      pkg.items.push({ serviceId, included: true });
      showToast("패키지에 서비스를 추가했습니다.");
    }
    state.lastReport = null;
    filterStatePackages();
  };

  filteredServices = patchedFilteredServices;
  renderServiceCard = patchedRenderServiceCard;
  renderPackageItem = patchedRenderPackageItem;
  renderPackageView = patchedRenderPackageView;
  globalThis.toggleServiceInSelectedPackage = toggleServiceInSelectedPackage;

  const nativeRender = render;
  render = function patchedRender() {
    installPackageUxStyles();
    filterStatePackages();
    return nativeRender();
  };

  installPackageUxStyles();
  filterStatePackages();
})();
