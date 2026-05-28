(function () {
  if (typeof state === "undefined") return;

  function installStatusStyles() {
    if (document.querySelector("#status-feedback-patch")) return;
    const style = document.createElement("style");
    style.id = "status-feedback-patch";
    style.textContent = `
      .status-note {
        min-height: 42px;
        padding: 10px 12px;
        border: 1px solid var(--line);
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 9px;
        color: #344649;
        background: var(--surface-2);
        line-height: 1.45;
        font-size: 13px;
        font-weight: 700;
      }
      .status-note .icon {
        width: 18px;
        height: 18px;
        flex: 0 0 18px;
      }
      .status-note.green {
        border-color: rgba(20, 92, 61, 0.18);
        color: #145c3d;
        background: var(--green-soft);
      }
      .status-note.amber {
        border-color: #f1d295;
        color: #805205;
        background: var(--amber-soft);
      }
      .status-note.red {
        border-color: rgba(155, 46, 42, 0.18);
        color: #9b2e2a;
        background: var(--red-soft);
      }
      .detail-brief {
        border: 1px solid #c8ddd7;
        border-radius: 8px;
        background: #f5fbf9;
        padding: 14px;
        display: grid;
        gap: 12px;
      }
      .detail-brief-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .detail-brief h3,
      .related-provider-block h3 {
        margin: 0 0 4px;
        font-size: 16px;
      }
      .detail-brief p {
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }
      .brief-list {
        margin: 0;
        padding-left: 18px;
        color: #26383a;
        line-height: 1.55;
      }
      .brief-list li + li {
        margin-top: 6px;
      }
      .raw-detail {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
      }
      .raw-detail summary {
        cursor: pointer;
        padding: 12px 14px;
        font-weight: 800;
        color: #33484b;
      }
      .raw-detail .detail-grid {
        padding: 0 12px 12px;
      }
      .related-provider-block {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px;
        background: var(--surface-2);
      }
      .related-provider-block .source-stack {
        margin-top: 10px;
      }
    `;
    document.head.appendChild(style);
  }

  function note(kind, text) {
    const iconName = kind === "green" ? "check-circle-2" : kind === "red" ? "triangle-alert" : "info";
    return `
      <div class="status-note ${kind}">
        ${icon(iconName)}
        <span>${escapeHtml(text)}</span>
      </div>
    `;
  }

  function structuredStatus() {
    if (!state.structured) return "";
    if (state.structureLoading) {
      return note("green", state.structureLoadingText || "AI 구조화와 추천 준비를 진행하고 있습니다.");
    }
    if (state.structured.llmUsed) {
      return note("green", "AI 구조화와 추천 준비가 완료되었습니다. 최종 판단은 상담자가 확인해야 합니다.");
    }
    if (state.structured.llmError) {
      const reason = state.structured.llmErrorReason ? ` 원인: ${state.structured.llmErrorReason}` : "";
      return note("amber", `Gemini 응답 실패로 규칙 기반 분석을 사용했습니다.${reason}`);
    }
    return note("amber", "규칙 기반 분석을 사용했습니다. 핵심 욕구와 대상이 맞는지 확인해 주세요.");
  }

  function serviceDataStatus() {
    const meta = state.serviceMeta;
    if (!meta) return "";
    const errors = Array.isArray(meta.errors) ? meta.errors.filter(Boolean) : [];
    if (meta.fallback || errors.length) {
      const reason = errors.length ? ` (${errors.slice(0, 2).join(" / ")})` : "";
      return note("amber", `일부 공공데이터 API 응답이 제한되어 로컬·대체 후보를 함께 표시합니다.${reason}`);
    }
    return note("green", "공공데이터 API 결과를 반영한 후보 목록입니다.");
  }

  function detailStatus(service) {
    if (state.modalLoading) return "";
    if (service.detailLoaded) return note("green", "공공데이터 상세조회 API 정보를 반영했습니다.");
    if (["중앙", "지자체"].includes(service.source)) {
      if (service.detailMeta?.reason === "external_portal_detail") {
        return note("amber", "이 서비스는 복지로 상세조회 API 대상이 아니어서 공식 외부 포털의 기본 정보를 표시합니다.");
      }
      const detailErrors = service.detailMeta && Array.isArray(service.detailMeta.errors) ? service.detailMeta.errors : [];
      const errors = detailErrors.length ? ` (${detailErrors.slice(0, 2).join(" / ")})` : "";
      return note("amber", `상세조회 API 정보를 불러오지 못해 목록·기본 정보를 표시합니다.${errors}`);
    }
    return note("amber", "기관·민간 항목은 공공 복지서비스 상세조회 대상이 아니어서 기본 정보를 표시합니다.");
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function linkHref(value) {
    const url = String(value || "").trim();
    if (!/^https?:\/\//i.test(url)) return "";
    return url;
  }

  function externalLink(value, label = "공식 상세 페이지 열기") {
    const url = linkHref(value);
    if (!url) return escapeHtml(value || "");
    return `<a class="inline-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
  }

  function detailHtmlItem(title, html) {
    return `<div class="detail-item"><strong>${escapeHtml(title)}</strong><span>${html || "-"}</span></div>`;
  }

  function jsString(value) {
    return String(value ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
  }

  function renderBriefList(items) {
    const list = asArray(items).filter(Boolean);
    if (!list.length) return "";
    return `<ul class="brief-list">${list.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function renderDetailBrief(service) {
    const brief = service.detailBrief;
    if (!brief) return "";
    const sourceLabel = brief.llmUsed ? "Gemini 요약" : "요약";
    return `
      <section class="detail-brief">
        <div class="detail-brief-head">
          <div>
            <h3>핵심 요약</h3>
            <p>${escapeHtml(brief.headline || service.summary || "")}</p>
          </div>
          ${pill(sourceLabel, brief.llmUsed ? "green" : "")}
        </div>
        ${renderBriefList(brief.keyPoints)}
        ${renderBriefList(brief.checkBeforeApply)}
        ${brief.caseworkerNote ? `<p><strong>상담 메모:</strong> ${escapeHtml(brief.caseworkerNote)}</p>` : ""}
      </section>
    `;
  }

  function renderRelatedProviders(service) {
    const providers = asArray(service.relatedProviders);
    if (!providers.length) return "";
    const meta = service.relatedProvidersMeta || {};
    return `
      <section class="related-provider-block">
        <div class="detail-brief-head">
          <div>
            <h3>민간·지역 연계 후보</h3>
            <p>상세 서비스와 함께 확인할 수 있는 기관 API 후보입니다.</p>
          </div>
          ${pill(meta.fallback ? "기관 후보" : "기관 API", meta.fallback ? "" : "green")}
        </div>
        <div class="source-stack">
          ${providers
            .map(
              (provider) => `
                <div class="source-row">
                  <div>
                    <strong>${escapeHtml(provider.name || "기관명 확인 필요")}</strong>
                    <div class="tiny">${escapeHtml(provider.serviceName || provider.serviceType || "연계 서비스")} · ${escapeHtml(provider.region || service.region || "")}</div>
                    <div class="tiny">${escapeHtml(provider.address || "")}</div>
                  </div>
                  <div class="pill-row">
                    ${pill(provider.source || "기관", provider.source === "샘플" ? "" : "blue")}
                    ${provider.contact ? pill(provider.contact) : ""}
                  </div>
                </div>
              `
            )
            .join("")}
        </div>
      </section>
    `;
  }

  function renderRawDetails(service) {
    const docs = asArray(service.docs).join(", ");
    const laws = asArray(service.laws);
    const open = service.detailBrief ? "" : " open";
    return `
      <details class="raw-detail"${open}>
        <summary>원문 상세 필드 보기</summary>
        <div class="detail-grid">
          ${detailItem("지원대상/기준", service.eligibility)}
          ${service.selectionCriteria ? detailItem("선정기준", service.selectionCriteria) : ""}
          ${detailItem("지원내용", service.support)}
          ${detailItem("신청절차", service.process)}
          ${detailItem("준비서류", docs)}
          ${detailItem("문의처", service.contact)}
          ${detailHtmlItem("URL", externalLink(service.detailUrl || service.url))}
          ${laws.length ? detailItem("근거법령", laws.join(", ")) : ""}
        </div>
      </details>
    `;
  }

  const nativeApiFetch = apiFetch;
  apiFetch = async function patchedApiFetch(path, options = {}) {
    const data = await nativeApiFetch(path, options);
    if (typeof path === "string" && path.startsWith("/api/services")) {
      if (path === "/api/services" || path.startsWith("/api/services?")) {
        state.serviceMeta = data.meta || null;
      } else if (data.service) {
        data.service.detailMeta = data.meta && data.meta.detail ? data.meta.detail : null;
      }
    }
    return data;
  };

  if (typeof renderStructured === "function") {
    const nativeRenderStructured = renderStructured;
    renderStructured = function patchedRenderStructured() {
      return nativeRenderStructured().replace('<div class="stack">', `<div class="stack">${structuredStatus()}`);
    };
  }

  if (typeof renderSearchView === "function") {
    const nativeRenderSearchView = renderSearchView;
    renderSearchView = function patchedRenderSearchView() {
      return nativeRenderSearchView().replace('<div class="grid-2">', `${serviceDataStatus()}<div class="grid-2">`);
    };
  }

  if (typeof renderServiceModal === "function") {
    renderServiceModal = function patchedRenderServiceModal(serviceId) {
      const service = services.find((item) => item.id === serviceId);
      if (!service) return "";
      return `
        <div class="modal-backdrop" onclick="if(event.target === this){ state.modalServiceId = null; render(); }">
          <article class="modal">
            <div class="modal-head">
              <div>
                <h2 class="panel-title">${escapeHtml(service.name)}</h2>
                <p class="panel-subtitle">${escapeHtml(service.source)} · ${escapeHtml(service.region)} · ${escapeHtml(service.updated)}</p>
              </div>
              <button class="icon-btn" title="닫기" onclick="state.modalServiceId = null; render();">${icon("x")}</button>
            </div>
            <div class="modal-body stack">
              ${state.modalLoading ? `<div class="empty-state">상세조회 API를 불러오는 중입니다.</div>` : ""}
              ${detailStatus(service)}
              <div class="pill-row">
                ${asArray(service.domains).map((domain) => pill(domain, needsColor(domain))).join("")}
                ${pill(service.target, "blue")}
                ${pill(service.urgency, service.urgency === "긴급" ? "red" : "")}
                ${service.detailLoaded ? pill("상세조회 API", "green") : ""}
              </div>
              ${renderDetailBrief(service)}
              <p class="service-summary">${escapeHtml(service.summary)}</p>
              ${renderRawDetails(service)}
              ${renderRelatedProviders(service)}
              ${
                asArray(service.applicationSteps).length
                  ? `<div class="report-block"><h3>연계 단계</h3><ol>${service.applicationSteps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol></div>`
                  : ""
              }
              <div class="button-row">
                <button class="btn secondary" onclick="generatePackages().then(() => { addServiceToPackage('${jsString(service.id)}'); state.modalServiceId = null; render(); })">${icon("plus")} 패키지 추가</button>
                <button class="btn ghost" onclick="state.modalServiceId = null; render();">${icon("check")} 확인</button>
              </div>
            </div>
          </article>
        </div>
      `;
    };
  }

  installStatusStyles();
})();

(function () {
  if (typeof state === "undefined" || typeof inferStructure !== "function" || typeof render !== "function") return;
  if (globalThis.__CASE_ANALYZE_LOADING_PATCHED) return;
  globalThis.__CASE_ANALYZE_LOADING_PATCHED = true;

  state.structureLoading = false;
  state.structureLoadingText = "";
  state.structureLoadingToken = 0;

  function installAnalyzeStyles() {
    if (document.querySelector("#case-analyze-loading-patch")) return;
    const style = document.createElement("style");
    style.id = "case-analyze-loading-patch";
    style.textContent = `
      .analyze-loading-note {
        margin-bottom: 12px;
      }
      .btn.is-loading,
      .icon-btn.is-loading {
        cursor: progress;
        opacity: 0.72;
      }
      .inline-link {
        color: #17645b;
        font-weight: 800;
        text-decoration: underline;
        text-underline-offset: 3px;
      }
    `;
    document.head.appendChild(style);
  }

  function reflectAnalyzeLoading() {
    installAnalyzeStyles();
    document.querySelectorAll('button[onclick*="inferStructure"]').forEach((button) => {
      button.disabled = Boolean(state.structureLoading);
      button.classList.toggle("is-loading", Boolean(state.structureLoading));
      if (state.structureLoading && !button.dataset.originalLabel) {
        button.dataset.originalLabel = button.innerHTML;
        button.innerHTML = `${icon("loader-circle")} AI 구조화 중`;
      } else if (!state.structureLoading && button.dataset.originalLabel) {
        button.innerHTML = button.dataset.originalLabel;
        delete button.dataset.originalLabel;
      }
    });

    const oldNote = document.querySelector(".analyze-loading-note");
    if (oldNote) oldNote.remove();
    if (!state.structureLoading || state.view !== "case") {
      lucide?.createIcons?.();
      return;
    }
    const content = document.querySelector(".content");
    if (content) {
      content.insertAdjacentHTML(
        "afterbegin",
        `<div class="status-note green analyze-loading-note">${icon("loader-circle")}<span>${escapeHtml(
          state.structureLoadingText || "AI가 상담 메모를 구조화하고 있습니다. 잠시만 기다려 주세요."
        )}</span></div>`
      );
    }
    lucide?.createIcons?.();
  }

  const nativeRender = render;
  render = function patchedRenderAnalyzeLoading() {
    const result = nativeRender();
    reflectAnalyzeLoading();
    return result;
  };

  const nativeShowToast = showToast;
  showToast = function patchedShowToastDuringWorkflow(message) {
    if (state.structureLoading && /구조화|패키지|추천서|생성|분석/.test(String(message || ""))) {
      state.deferredWorkflowToast = message;
      return;
    }
    return nativeShowToast(message);
  };

  async function runAnalyzeWorkflow(options = {}, token) {
    const nextView = options.goTo;

    state.structureLoadingText = "1/4 AI가 상담 메모를 구조화하고 있습니다.";
    render();
    await nativeInferStructure({ ...options, goTo: undefined });
    if (state.structureLoadingToken !== token) return;

    state.structureLoadingText = "2/4 통합검색 후보를 공공데이터 기준으로 갱신하고 있습니다.";
    render();
    await refreshServicesFromBackend(state.viewToken);
    if (state.structureLoadingToken !== token) return;

    state.structureLoadingText = "3/4 상담 내용에 맞는 추천 패키지를 생성하고 있습니다.";
    render();
    state.packageLoading = true;
    try {
      const packageData = await apiFetch("/api/packages", {
        method: "POST",
        body: JSON.stringify({ case: state.case, structured: state.structured, services }),
      });
      state.packages = packageData.packages || [];
      state.selectedPackageId = state.packages[0]?.id || null;
      state.lastReport = null;
    } catch (_error) {
      generatePackagesLocal({ show: false });
    } finally {
      state.packageLoading = false;
    }
    if (state.structureLoadingToken !== token) return;

    state.structureLoadingText = "4/4 추천서 초안을 생성하고 기관 연결 정보를 정리하고 있습니다.";
    render();
    await refreshProvidersFromBackend(state.viewToken);
    if (state.structureLoadingToken !== token) return;
    await refreshReportFromBackend(state.viewToken);
    if (state.structureLoadingToken !== token) return;

    state.packageLoading = false;
    state.providerLoading = false;
    state.reportLoading = false;
    if (nextView) {
      state.viewToken = (state.viewToken || 0) + 1;
      state.view = nextView;
      state.mobileNav = false;
    }
    render();
  }

  const nativeInferStructure = inferStructure;
  inferStructure = async function patchedInferStructureLoading(options = {}) {
    if (state.structureLoading) {
      nativeShowToast("AI 구조화와 추천서 생성이 진행 중입니다. 잠시만 기다려 주세요.");
      return;
    }
    const token = (state.structureLoadingToken || 0) + 1;
    state.structureLoadingToken = token;
    state.structureLoading = true;
    state.deferredWorkflowToast = "";
    state.structureLoadingText = "1/4 AI가 상담 메모를 구조화하고 있습니다.";
    render();
    try {
      const result = await runAnalyzeWorkflow(options, token);
      if (state.structureLoadingToken === token) {
        state.deferredWorkflowToast = "";
        state.structureLoading = false;
        state.structureLoadingText = "";
        render();
        nativeShowToast("AI 구조화, 통합검색 후보, 패키지 추천, 추천서 초안 생성이 완료되었습니다.");
      }
      return result;
    } finally {
      if (state.structureLoadingToken === token && state.structureLoading) {
        state.structureLoading = false;
        state.structureLoadingText = "";
        render();
      }
    }
  };

  installAnalyzeStyles();
})();

(function () {
  if (typeof state === "undefined") return;

  function installRichReportStyles() {
    if (document.querySelector("#rich-report-patch")) return;
    const style = document.createElement("style");
    style.id = "rich-report-patch";
    style.textContent = `
      .report-emphasis {
        border-color: #c8ddd7;
        background: #f5fbf9;
      }
      .report-card-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .report-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .report-mini-card,
      .service-plan-card,
      .timeline-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface-2);
        padding: 12px;
      }
      .report-mini-card {
        display: grid;
        gap: 8px;
      }
      .report-mini-card strong,
      .timeline-card strong {
        color: var(--text);
        font-size: 14px;
      }
      .report-mini-card span,
      .service-plan-card p,
      .timeline-card li {
        color: var(--muted);
        line-height: 1.55;
      }
      .service-plan-list,
      .timeline-list {
        display: grid;
        gap: 12px;
      }
      .service-plan-card {
        display: grid;
        gap: 12px;
      }
      .service-plan-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .service-plan-head div {
        display: grid;
        gap: 4px;
      }
      .service-plan-head span,
      .service-plan-card .tiny {
        color: var(--muted);
      }
      .service-plan-card h4 {
        margin: 0 0 6px;
        font-size: 13px;
      }
      .service-plan-card ul,
      .timeline-card ul {
        margin: 0;
        padding-left: 18px;
      }
      .empty-state.compact {
        min-height: auto;
        padding: 10px;
        font-size: 13px;
      }
      @media (max-width: 900px) {
        .report-card-grid,
        .report-grid-2 {
          grid-template-columns: 1fr;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function list(value) {
    return Array.isArray(value) ? value.filter(Boolean) : [];
  }

  function htmlList(items) {
    const values = list(items);
    if (!values.length) return `<div class="empty-state compact">표시할 항목이 없습니다.</div>`;
    return `<ul>${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function fallbackServicePlans(selectedServices) {
    return selectedServices.map((service) => ({
      service: service.name,
      priority: service.urgency === "긴급" ? "높음" : "중간",
      purpose: list(service.domains).join(", ") || "지원 가능성 확인",
      whyRecommended: service.summary || "상담 메모와 연결되는 후보 서비스입니다.",
      eligibilityToCheck: [service.eligibility || "대상, 소득, 재산, 거주지 확인"],
      applicationPath: [service.process || "관할 기관 문의 후 접수 가능 여부 확인"],
      requiredDocs: service.docs || [],
      contactAction: service.contact || "공식 문의처 확인",
      cautions: ["최종 선정은 접수기관 심사로 결정됩니다."],
    }));
  }

  function renderPriorityAssessment(items) {
    const values = list(items);
    const cards = values.length
      ? values
      : [{ level: "확인", text: "소득, 재산, 가구원, 거주지, 중복지원 여부를 확인한 뒤 판단합니다." }];
    return `
      <div class="report-card-grid">
        ${cards
          .map(
            (item) => `
              <div class="report-mini-card">
                <strong>${escapeHtml(item.level || "확인")}</strong>
                <span>${escapeHtml(item.text || "")}</span>
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderServicePlans(plans, selectedServices) {
    const values = list(plans).length ? list(plans) : fallbackServicePlans(selectedServices);
    return `
      <div class="service-plan-list">
        ${values
          .map(
            (plan) => `
              <article class="service-plan-card">
                <div class="service-plan-head">
                  <div>
                    <strong>${escapeHtml(plan.service || "서비스")}</strong>
                    <span>${escapeHtml(plan.purpose || "지원 가능성 확인")}</span>
                  </div>
                  ${pill(plan.priority || "중간", plan.priority === "높음" ? "amber" : "")}
                </div>
                <p>${escapeHtml(plan.whyRecommended || "")}</p>
                <div class="report-grid-2">
                  <div>
                    <h4>확인 조건</h4>
                    ${htmlList(plan.eligibilityToCheck)}
                  </div>
                  <div>
                    <h4>신청·문의 경로</h4>
                    ${htmlList(plan.applicationPath)}
                  </div>
                  <div>
                    <h4>준비 서류</h4>
                    ${htmlList(plan.requiredDocs)}
                  </div>
                  <div>
                    <h4>문의 액션</h4>
                    <p>${escapeHtml(plan.contactAction || "관할 기관 확인")}</p>
                  </div>
                </div>
                ${list(plan.cautions).length ? `<div class="tiny">${escapeHtml(list(plan.cautions).join(" / "))}</div>` : ""}
              </article>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderActionPlan(plan) {
    const values = list(plan);
    if (!values.length) return htmlList([]);
    return `
      <div class="timeline-list">
        ${values
          .map(
            (phase) => `
              <div class="timeline-card">
                <strong>${escapeHtml(phase.timing || "확인")}</strong>
                ${htmlList(phase.tasks)}
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderChecklist(checklist) {
    const values = list(checklist);
    if (!values.length) return htmlList([]);
    return `
      <div class="report-card-grid">
        ${values
          .map(
            (group) => `
              <div class="report-mini-card">
                <strong>${escapeHtml(group.title || "확인")}</strong>
                ${htmlList(group.items)}
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderProviderPlan(plan) {
    const values = list(plan);
    if (!values.length) return "";
    return `
      <section class="report-block">
        <h3>민간·지역기관 연계 계획</h3>
        <div class="source-stack">
          ${values
            .map(
              (item) => `
                <div class="source-row">
                  <div>
                    <strong>${escapeHtml(item.name || "연계기관")}</strong>
                    <div class="tiny">${escapeHtml(item.reason || "")}</div>
                    <div class="tiny">${escapeHtml(item.contactAction || "")}</div>
                  </div>
                  ${pill("연계 후보", "blue")}
                </div>
              `
            )
            .join("")}
        </div>
      </section>
    `;
  }

  if (typeof copyReport === "function") {
    copyReport = function patchedCopyReport() {
      const { pkg, selectedServices, needs } = reportData();
      const report = state.lastReport;
      const servicePlans = report?.servicePlans || fallbackServicePlans(selectedServices);
      const actionPlan = report?.actionPlan || [];
      const lines = report
        ? [
            `[추천 패키지] ${report.packageTitle}`,
            `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`,
            `핵심 욕구: ${list(report.needs).join(", ")}`,
            "",
            "사례 요약",
            report.caseSummary || report.reason || "",
            "",
            "우선순위 판단",
            ...list(report.priorityAssessment).map((item) => `- ${item.level}: ${item.text}`),
            "",
            "서비스별 실행계획",
            ...servicePlans.flatMap((plan, index) => [
              `${index + 1}. ${plan.service} [${plan.priority}] ${plan.purpose}`,
              `   추천 이유: ${plan.whyRecommended}`,
              ...list(plan.eligibilityToCheck).map((item) => `   확인: ${item}`),
              ...list(plan.applicationPath).map((item) => `   경로: ${item}`),
              ...list(plan.requiredDocs).map((item) => `   서류: ${item}`),
              `   문의: ${plan.contactAction || "관할 기관 확인"}`,
            ]),
            "",
            "단계별 실행계획",
            ...list(actionPlan).flatMap((phase) => [`- ${phase.timing}`, ...list(phase.tasks).map((task) => `  · ${task}`)]),
            "",
            "추가 상담 질문",
            ...list(report.followUpQuestions).map((question) => `- ${question}`),
            "",
            "사례기록 메모",
            report.caseNote || "",
          ]
        : [
            `[추천 패키지] ${pkg.title}`,
            `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`,
            `핵심 욕구: ${needs.join(", ")}`,
            "",
            "추천 서비스",
            ...selectedServices.map((service, index) => `${index + 1}. ${service.name} - ${service.summary}`),
          ];

      navigator.clipboard
        ?.writeText(lines.join("\n"))
        .then(() => showToast("추천서 텍스트를 복사했습니다."))
        .catch(() => showToast("복사 권한을 확인해 주세요."));
    };
  }

  if (typeof renderReportView === "function") {
    renderReportView = function patchedRenderReportView() {
      if (!state.packages.length) generatePackagesLocal({ show: false });
      const { pkg, selectedServices, needs, contacts } = reportData();
      const docs = Array.from(new Set(selectedServices.flatMap((service) => service.docs || [])));
      const report = state.lastReport;
      const reportNeeds = report?.needs || needs;
      const reportReason =
        report?.reason ||
        `${pkg.summary}. 상담 메모에서 ${needs.join(", ")} 욕구가 확인되어 관련 제도와 기관을 조합했습니다. 최종 신청 가능성은 접수기관 심사로 확인합니다.`;
      const reportDocs = report?.docs || docs;
      const reportContacts =
        report?.contacts || contacts.map((service) => ({ service: service.name, contact: service.contact, url: service.url }));
      const reportCaseSummary =
        report?.caseSummary ||
        `${state.case.targetType} / ${state.case.region || "지역 미입력"} 사례입니다. ${pkg.title}를 우선 검토합니다.`;
      const priorityAssessment =
        report?.priorityAssessment || [{ level: state.case.urgency || "주의", text: "소득·재산·가구원·거주지 기준 확인 후 최종 판단합니다." }];
      const actionPlan =
        report?.actionPlan || [
          { timing: "오늘", tasks: ["1순위 서비스 문의처와 신청 자격을 확인합니다.", "공통 증빙 자료 보유 여부를 점검합니다."] },
          { timing: "3일 이내", tasks: ["서비스별 접수기관과 신청 경로를 정리합니다.", "누락 서류와 중복지원 제한을 확인합니다."] },
          { timing: "1~2주", tasks: ["접수 결과와 보완 요청을 추적하고 대체 자원을 확인합니다."] },
        ];
      const checklist =
        report?.eligibilityChecklist || [
          { title: "공통 확인", items: ["신분 확인", "가구 구성", "실거주지", "소득·재산 변동"] },
          { title: "신청 가능성", items: ["서비스별 대상 기준", "중복지원 제한", "관할기관 접수 가능 여부"] },
        ];
      const dataLimitations =
        report?.dataLimitations || [
          "추천서는 상담 보조 자료이며 최종 수급 가능성은 접수기관 심사로 결정됩니다.",
          "공공데이터와 기관 정보는 갱신 시점 차이가 있을 수 있어 신청 전 최신 공고를 확인합니다.",
        ];

      return `
        <section class="workspace-panel">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">설명형 추천서</h2>
              <p class="panel-subtitle">${escapeHtml(pkg.title)} · ${escapeHtml(state.case.title)}</p>
              <p class="panel-subtitle">${state.reportLoading ? "추천서 생성 중" : report?.llmUsed ? "Gemini 추천서 엔진 사용" : report?.generatedBy ? "백엔드 추천서 엔진 사용" : "로컬 추천서 미리보기"}</p>
            </div>
            <div class="button-row">
              <button class="btn ghost" onclick="copyReport()">${icon("copy")} 텍스트 복사</button>
              <button class="btn primary" onclick="window.print()">${icon("printer")} 인쇄/PDF</button>
            </div>
          </div>
          <div class="panel-body">
            <article class="report-preview">
              <div class="report-cover">
                <div class="pill-row">
                  ${pill(state.case.urgency, state.case.urgency === "긴급" ? "red" : "amber")}
                  ${reportNeeds.map((need) => pill(need, needsColor(need))).join("")}
                </div>
                <h2>${escapeHtml(state.case.title)}</h2>
                <div class="muted">${escapeHtml(state.case.targetType)} · ${escapeHtml(state.case.region || "지역 미입력")} · ${new Date(report?.generatedAt || Date.now()).toLocaleDateString("ko-KR")}</div>
              </div>
              <div class="report-content">
                <section class="report-block report-emphasis">
                  <h3>사례 요약</h3>
                  <p>${escapeHtml(reportCaseSummary)}</p>
                </section>
                <section class="report-block">
                  <h3>우선순위 판단</h3>
                  ${renderPriorityAssessment(priorityAssessment)}
                </section>
                <section class="report-block">
                  <h3>추천 이유</h3>
                  <p>${escapeHtml(reportReason)}</p>
                </section>
                <section class="report-block">
                  <h3>서비스별 실행 계획</h3>
                  ${renderServicePlans(report?.servicePlans, selectedServices)}
                </section>
                <section class="report-block">
                  <h3>신청 전 확인 체크리스트</h3>
                  ${renderChecklist(checklist)}
                </section>
                <section class="report-block">
                  <h3>공통 준비 서류</h3>
                  <div class="pill-row">${reportDocs.map((doc) => pill(doc)).join("") || pill("서비스별 서류 확인")}</div>
                </section>
                <section class="report-block">
                  <h3>단계별 실행계획</h3>
                  ${renderActionPlan(actionPlan)}
                </section>
                ${renderProviderPlan(report?.providerPlan)}
                ${
                  list(report?.followUpQuestions).length
                    ? `<section class="report-block"><h3>추가 상담 질문</h3>${htmlList(report.followUpQuestions)}</section>`
                    : ""
                }
                ${
                  report?.counselorScript || report?.caseNote
                    ? `<section class="report-block report-emphasis"><h3>설명·기록 문구</h3>
                        ${report?.counselorScript ? `<p><strong>대상자 설명:</strong> ${escapeHtml(report.counselorScript)}</p>` : ""}
                        ${report?.caseNote ? `<p><strong>사례기록:</strong> ${escapeHtml(report.caseNote)}</p>` : ""}
                      </section>`
                    : ""
                }
                <section class="report-block">
                  <h3>문의처</h3>
                  <table class="contact-table">
                    <thead>
                      <tr><th>서비스</th><th>문의처</th><th>URL</th></tr>
                    </thead>
                    <tbody>
                      ${reportContacts
                        .map(
                          (contact) => `
                            <tr>
                              <td>${escapeHtml(contact.service || "")}</td>
                              <td>${escapeHtml(contact.contact || "")}</td>
                              <td>${escapeHtml(contact.url || "")}</td>
                            </tr>
                          `
                        )
                        .join("")}
                    </tbody>
                  </table>
                </section>
                <section class="report-block">
                  <h3>확인 필요 사항</h3>
                  ${htmlList(dataLimitations)}
                </section>
              </div>
            </article>
          </div>
        </section>
      `;
    };
  }

  installRichReportStyles();
})();
