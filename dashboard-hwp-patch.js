(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;
  if (globalThis.__DASHBOARD_HWP_PATCHED) return;
  globalThis.__DASHBOARD_HWP_PATCHED = true;

  const DRAFT_KEY = "welfare-case-draft-v2";
  const SIDO_ALIASES = {
    서울특별시: "서울", 서울시: "서울", 서울: "서울",
    부산광역시: "부산", 부산시: "부산", 부산: "부산",
    대구광역시: "대구", 대구시: "대구", 대구: "대구",
    인천광역시: "인천", 인천시: "인천", 인천: "인천",
    광주광역시: "광주", 광주시: "광주", 광주: "광주",
    대전광역시: "대전", 대전시: "대전", 대전: "대전",
    울산광역시: "울산", 울산시: "울산", 울산: "울산",
    세종특별자치시: "세종", 세종시: "세종", 세종: "세종",
    경기도: "경기", 경기: "경기",
    강원특별자치도: "강원", 강원도: "강원", 강원: "강원",
    충청북도: "충북", 충북: "충북",
    충청남도: "충남", 충남: "충남",
    전북특별자치도: "전북", 전라북도: "전북", 전북: "전북",
    전라남도: "전남", 전남: "전남",
    경상북도: "경북", 경북: "경북",
    경상남도: "경남", 경남: "경남",
    제주특별자치도: "제주", 제주도: "제주", 제주: "제주",
  };
  const NATIONWIDE = new Set(["", "전국", "중앙", "공통", "온라인", "복지로", "정부24"]);
  const LOCAL_SOURCES = new Set(["지자체", "광역", "기초", "시군구"]);
  const COMMON_FORM_URL = "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=14600000275";

  function ensureFeatureStyles() {
    // Dashboard/HWP styles now live in styles.css; keep this as a no-op for compatibility.
    return;
    if (document.querySelector("#dashboard-hwp-patch-style")) return;
    const style = document.createElement("style");
    style.id = "dashboard-hwp-patch-style";
    style.textContent = `
      .case-table-wrap{overflow-x:auto}.case-dashboard-table{width:100%;border-collapse:separate;border-spacing:0 10px;min-width:860px}.case-dashboard-table th{color:var(--muted);font-size:12px;font-weight:800;padding:0 14px 4px;text-align:left}.case-dashboard-table td{background:#fff;border-bottom:1px solid var(--line);border-top:1px solid var(--line);padding:14px;vertical-align:middle}.case-dashboard-table td:first-child{border-left:1px solid var(--line);border-radius:8px 0 0 8px}.case-dashboard-table td:last-child{border-right:1px solid var(--line);border-radius:0 8px 8px 0}.case-dashboard-table tr.is-current td{background:#eef8f5;border-color:#a8d6cd}.case-dashboard-table strong{display:block;margin-bottom:4px}.table-actions{display:flex;align-items:center;gap:8px;white-space:nowrap}.btn.compact,.download-link-btn.compact{min-height:34px;padding:0 10px}.icon-btn.danger{color:#9f2f2f}.milestone{display:grid;gap:6px;grid-template-columns:repeat(4,minmax(54px,1fr));min-width:250px}.milestone-step{align-items:center;background:#eef1f3;border:1px solid #d7dde2;border-radius:999px;color:#6b777f;display:inline-flex;font-size:12px;font-weight:800;justify-content:center;min-height:28px;padding:0 8px}.milestone-step.done{background:#dff2ec;border-color:#93cabc;color:#245d55}.step-badge{align-items:center;background:#e8f4ef;border:1px solid #b9dcd2;border-radius:999px;color:#2d655d;display:inline-flex;font-size:12px;font-weight:900;min-height:28px;padding:0 11px}.hwp-guide-card{background:#fff;border:1px solid #cdd8df;border-radius:8px;box-shadow:0 10px 30px rgba(31,48,56,.08);margin-bottom:18px;padding:18px}.hwp-guide-head{align-items:flex-start;border-bottom:2px solid #1f3038;display:flex;justify-content:space-between;gap:16px;margin-bottom:14px;padding-bottom:12px}.hwp-guide-head h3{font-size:18px;margin:8px 0 0}.hwp-guide-table{border-collapse:collapse;width:100%}.hwp-guide-table th,.hwp-guide-table td{border:1px solid #d7dde2;font-size:14px;line-height:1.55;padding:11px 12px;text-align:left;vertical-align:top}.hwp-guide-table th{background:#f2f5f6;color:#1f3038;font-weight:900;width:190px}.hwp-check{display:inline-flex;align-items:center;gap:6px;margin:2px 14px 2px 0}.application-draft-box{background:#f8faf9;border:1px solid #dde6e4;border-radius:8px;margin-top:14px;padding:14px}.application-draft-box strong{display:block;margin-bottom:8px}.application-draft-box p{color:#46535a;line-height:1.7;margin:0}.download-link-grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}.download-link-btn{align-items:center;background:#eaf5f0;border:1px solid #b9dcd2;border-radius:8px;color:#245d55;display:inline-flex;font-weight:900;gap:8px;justify-content:center;min-height:44px;padding:0 14px;text-decoration:none}.download-link-btn:hover{background:#dff2ec}.download-link-btn span{color:#617078;font-size:12px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media(max-width:760px){.hwp-guide-head{display:block}.hwp-guide-table th,.hwp-guide-table td{display:block;width:100%}}@media print{.case-dashboard-table,.download-link-grid{min-width:0}.hwp-guide-card{border:1.5px solid #111;box-shadow:none;break-inside:avoid;page-break-inside:avoid}.hwp-guide-head{border-bottom-color:#111}.hwp-guide-table th,.hwp-guide-table td{border-color:#111;color:#111}.application-draft-box{border-color:#111}.download-link-btn{background:#fff;border-color:#111;color:#111}}
    `;
    document.head.appendChild(style);
  }

  function normalizeRegion(region) {
    const value = String(region || "").replace(/[()[\]{},]/g, " ").replace(/\s+/g, " ").trim();
    if (!value) return { sido: "", sigungu: "" };
    if (NATIONWIDE.has(value)) return { sido: "전국", sigungu: "" };
    const tokens = value.split(" ");
    let sido = SIDO_ALIASES[tokens[0]] || "";
    let sigungu = tokens[1] || "";
    if (!sido) {
      const alias = Object.keys(SIDO_ALIASES).sort((a, b) => b.length - a.length).find((item) => value.startsWith(item));
      if (alias) {
        sido = SIDO_ALIASES[alias];
        sigungu = value.slice(alias.length).trim().split(" ")[0] || "";
      }
    }
    if (!sido && tokens.length === 1) {
      const bare = tokens[0].replace(/(특별시|광역시|특별자치시|특별자치도|자치도|도|시)$/g, "");
      sido = SIDO_ALIASES[bare] || bare;
    }
    return { sido, sigungu: sigungu.replace(/(특례시|시|군|구)$/g, "") };
  }

  function isRegionCompatible(service, caseRegion = state.case.region) {
    const serviceRegion = String(service?.region || "").trim();
    const source = String(service?.source || "").trim();
    if (NATIONWIDE.has(serviceRegion) || source === "중앙") return true;
    if (!caseRegion) return !LOCAL_SOURCES.has(source);
    const caseNorm = normalizeRegion(caseRegion);
    const serviceNorm = normalizeRegion(serviceRegion);
    if (!serviceNorm.sido || serviceNorm.sido === "전국") return !LOCAL_SOURCES.has(source);
    if (!caseNorm.sido || caseNorm.sido !== serviceNorm.sido) return false;
    if (caseNorm.sigungu && serviceNorm.sigungu) {
      return caseNorm.sigungu.includes(serviceNorm.sigungu) || serviceNorm.sigungu.includes(caseNorm.sigungu);
    }
    return true;
  }

  globalThis.is_region_compatible = isRegionCompatible;

  function saveDraft() {
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify(state.case));
    } catch (_error) {}
  }

  function loadDraft() {
    try {
      const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
      if (draft && typeof draft === "object") {
        state.case = { ...state.case, ...draft };
      }
    } catch (_error) {}
  }

  loadDraft();
  state.case.counselor ||= "김현장";
  recentCases = recentCases.map((item, index) => ({ counselor: ["김현장", "이연계", "박사례"][index % 3], ...item }));

  const nativeUpdateCase = updateCase;
  updateCase = function patchedUpdateCase(field, value, shouldRender = true) {
    nativeUpdateCase(field, value, shouldRender);
    saveDraft();
  };

  const nativeCreateNewCase = createNewCase;
  createNewCase = function patchedCreateNewCase() {
    nativeCreateNewCase();
    state.case.counselor = state.case.counselor || "김현장";
    saveDraft();
  };

  const nativeLoadRecentCase = loadRecentCase;
  loadRecentCase = function patchedLoadRecentCase(id) {
    const found = recentCases.find((item) => item.id === id);
    nativeLoadRecentCase(id);
    state.case.counselor = found?.counselor || state.case.counselor || "김현장";
    saveDraft();
  };

  const nativeFilteredServices = filteredServices;
  filteredServices = function patchedFilteredServices() {
    return nativeFilteredServices().filter((service) => isRegionCompatible(service, state.case.region));
  };

  function prunePackages() {
    if (!Array.isArray(state.packages)) return;
    state.packages = state.packages.map((pkg) => ({
      ...pkg,
      items: (pkg.items || []).filter((item) => {
        const service = services.find((entry) => entry.id === item.serviceId);
        return !service || isRegionCompatible(service, state.case.region);
      }),
    }));
  }

  if (typeof generatePackagesLocal === "function") {
    const nativeGeneratePackagesLocal = generatePackagesLocal;
    generatePackagesLocal = function patchedGeneratePackagesLocal(options = {}) {
      const result = nativeGeneratePackagesLocal(options);
      prunePackages();
      return result;
    };
  }

  if (typeof generatePackages === "function") {
    const nativeGeneratePackages = generatePackages;
    generatePackages = async function patchedGeneratePackages(options = {}) {
      const result = await nativeGeneratePackages(options);
      prunePackages();
      return result;
    };
  }

  function caseRows() {
    const current = {
      ...state.case,
      status: state.lastReport ? "추천서 생성" : state.packages.length ? "패키지 조정" : state.structured ? "AI 분석" : state.case.memo ? "상담 입력" : "신규",
      needs: state.structured?.needs || state.case.issueTypes || [],
      current: true,
    };
    const rows = [current, ...recentCases.filter((item) => item.id !== state.case.id)];
    return rows.slice(0, 9);
  }

  function stageIndex(item) {
    if (item.current) {
      if (state.lastReport) return 4;
      if (state.packages.length) return 3;
      if (state.structured) return 2;
      return state.case.memo ? 1 : 0;
    }
    const status = String(item.status || "");
    if (/추천서|완료/.test(status)) return 4;
    if (/패키지|추천/.test(status)) return 3;
    if (/구조|분석/.test(status)) return 2;
    return item.memo ? 1 : 0;
  }

  function milestone(item) {
    const currentStage = stageIndex(item);
    const labels = ["상담", "AI", "패키지", "추천서"];
    return `<div class="milestone">${labels.map((label, index) => `<span class="milestone-step ${index < currentStage ? "done" : ""}">${escapeHtml(label)}</span>`).join("")}</div>`;
  }

  function needsFor(item) {
    return Array.isArray(item.needs) ? item.needs : Array.isArray(item.issueTypes) ? item.issueTypes : [];
  }

  renderDashboard = function patchedRenderDashboard() {
    return `
      <div class="grid-3">
        ${renderStat("users", `${caseRows().length}건`, "추적 중인 상담")}
        ${renderStat("map-pin", state.case.region || "지역 미입력", "현재 거주 지역")}
        ${renderStat("user-check", state.case.counselor || "담당자 미입력", "담당 상담사")}
      </div>
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">통합 상담 대시보드</h2>
            <p class="panel-subtitle">사례명, 담당자, 거주 지역, 진행 단계를 한 화면에서 관리합니다.</p>
          </div>
          <div class="button-row">
            <button class="btn ghost" onclick="createNewCase()">${icon("plus")} 새 상담</button>
            <button class="btn primary" onclick="setView('case')">${icon("arrow-right")} 현재 상담 이어서</button>
          </div>
        </div>
        <div class="panel-body">
          <div class="case-table-wrap">
            <table class="case-dashboard-table">
              <thead>
                <tr>
                  <th>상담 사례명</th>
                  <th>담당 상담사</th>
                  <th>거주 지역</th>
                  <th>욕구</th>
                  <th>진행도</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                ${caseRows().map((item) => `
                  <tr class="${item.current ? "is-current" : ""}">
                    <td><strong>${escapeHtml(item.title || "제목 미입력")}</strong><span class="tiny">${escapeHtml(item.id || "NEW-CASE")}</span></td>
                    <td>${escapeHtml(item.counselor || "미배정")}</td>
                    <td>${escapeHtml(item.region || "미입력")}</td>
                    <td><div class="pill-row">${needsFor(item).slice(0, 4).map((need) => pill(need, needsColor(need))).join("") || pill("미분류")}</div></td>
                    <td>${milestone(item)}</td>
                    <td>
                      <div class="table-actions">
                        <button class="btn ghost compact" onclick="continueCase('${escapeHtml(item.id || "")}')">${icon("play")} 이어서 진행</button>
                        <button class="icon-btn danger" title="삭제" onclick="deleteCase('${escapeHtml(item.id || "")}')">${icon("trash-2")}</button>
                      </div>
                    </td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    `;
  };

  globalThis.continueCase = function continueCase(id) {
    if (!id || id === state.case.id) {
      setView("case");
      return;
    }
    loadRecentCase(id);
  };

  globalThis.deleteCase = async function deleteCase(id) {
    if (!id) return;
    recentCases = recentCases.filter((item) => item.id !== id);
    if (id === state.case.id) createNewCase();
    try {
      await apiFetch(`/api/cases/${encodeURIComponent(id)}`, { method: "DELETE" });
      showToast("상담 사례를 삭제했습니다.");
    } catch (_error) {
      showToast("화면에서 삭제했습니다. 서버 삭제는 다시 시도해 주세요.");
    }
    render();
  };

  function insertCounselorField() {
    if (state.view !== "case" || document.querySelector("#case-counselor")) return;
    const titleField = document.querySelector("#case-title")?.closest(".field");
    if (!titleField) return;
    titleField.insertAdjacentHTML(
      "afterend",
      `<div class="field">
        <label for="case-counselor">담당 상담사</label>
        <input id="case-counselor" value="${escapeHtml(state.case.counselor || "")}" placeholder="예: 김현장" oninput="updateCase('counselor', this.value, false)" />
      </div>`
    );
  }

  function serviceLinks(report) {
    const selected = typeof selectedPackageServices === "function" ? selectedPackageServices() : [];
    const links = [
      ...(report?.officialLinks || []),
      { label: "사회보장급여 신청(변경) 민원 안내", url: COMMON_FORM_URL, type: "common-form" },
      ...selected.map((service) => ({ label: `${service.name} 공고/상세`, url: service.detailUrl || service.url, type: "service-detail" })),
    ];
    const seen = new Set();
    return links.filter((link) => {
      const url = String(link.url || "");
      if (!/^https?:\/\//i.test(url) || seen.has(url)) return false;
      seen.add(url);
      return true;
    });
  }

  function localApplicationDraft() {
    const services = typeof selectedPackageServices === "function" ? selectedPackageServices() : [];
    const names = services.slice(0, 4).map((service) => service.name).join(", ");
    const needs = state.structured?.needs || state.case.issueTypes || [];
    const memo = String(state.case.memo || "").replace(/\s+/g, " ").slice(0, 180);
    return `신청인은 ${state.case.region || "거주지 미입력"}에 거주하는 ${state.case.targetType || "대상자"}로, 상담 결과 ${needs.join(", ") || "복지급여"} 관련 지원 필요성이 확인되었습니다. ${memo || "현재 생활 안정과 위기 완화를 위한 공적 지원 연계가 필요합니다."} 이에 ${names || "해당 복지급여"} 제공을 신청하고자 합니다.`;
  }

  function hwpGuideHtml(report) {
    const guide = report?.hwpGuide || {};
    const services = guide.services || (typeof selectedPackageServices === "function" ? selectedPackageServices().map((service) => service.name) : []);
    const draft = report?.applicationDraft || guide.applicationReason || localApplicationDraft();
    return `
      <section class="hwp-guide-card">
        <div class="hwp-guide-head">
          <div>
            <span class="step-badge">HWP 작성 가이드</span>
            <h3>사회보장급여 제공(변경) 신청서 [별지 제1호서식]</h3>
          </div>
          <span class="muted">제4페이지 신청 사유란에 초안 붙여넣기</span>
        </div>
        <table class="hwp-guide-table">
          <tbody>
            <tr><th>① 신청인 성명</th><td>${escapeHtml(guide.applicantName || "대상자 또는 대리 신청인 성명 기재")}</td></tr>
            <tr><th>② 주민등록번호</th><td>${escapeHtml(guide.residentNoMasked || "******-*******")}</td></tr>
            <tr><th>③ 거주지 주소</th><td>${escapeHtml(guide.address || state.case.region || "주소 확인 필요")}</td></tr>
            <tr><th>④ 신청 복지급여</th><td>${services.map((name) => `<label class="hwp-check"><input type="checkbox" checked disabled /> ${escapeHtml(name)}</label>`).join("") || "선택 서비스 확인 필요"}</td></tr>
            <tr><th>⑤ 대상 가구 구분</th><td>${escapeHtml(guide.householdType || state.case.targetType || "가구 구분 확인 필요")}</td></tr>
          </tbody>
        </table>
        <div class="application-draft-box">
          <strong>신청 사유 초안</strong>
          <p>${escapeHtml(draft)}</p>
        </div>
      </section>
    `;
  }

  function linkButtonsHtml(report) {
    const links = serviceLinks(report);
    if (!links.length) return "";
    return `
      <section class="report-block official-link-panel">
        <h3>공식 공고문/서식 바로가기</h3>
        <div class="download-link-grid">
          ${links.map((link) => `<a class="download-link-btn" href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer">${icon("external-link")} 양식/공고 바로가기<span>${escapeHtml(link.label)}</span></a>`).join("")}
        </div>
      </section>
    `;
  }

  function enhanceReportDom() {
    if (state.view !== "report") return;
    const content = document.querySelector(".report-content");
    if (!content) return;
    const report = state.lastReport || {};
    if (!content.querySelector(".hwp-guide-card")) {
      content.insertAdjacentHTML("afterbegin", hwpGuideHtml(report));
    }
    if (!content.querySelector(".official-link-panel")) {
      content.insertAdjacentHTML("beforeend", linkButtonsHtml(report));
    }
    document.querySelectorAll(".contact-table td:last-child").forEach((cell) => {
      const href = cell.querySelector("a")?.href || cell.textContent.trim();
      if (!/^https?:\/\//i.test(href)) return;
      cell.innerHTML = `<a class="download-link-btn compact" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${icon("external-link")} 양식/공고 바로가기</a>`;
    });
    window.lucide?.createIcons?.();
  }

  function installCopyPatch() {
    if (copyReport.__hwpCopyPatched) return;
    copyReport = function patchedCopyReport() {
      if (!state.packages.length) generatePackagesLocal({ show: false });
      const { pkg, selectedServices, needs } = reportData();
      const report = state.lastReport || {};
      const links = serviceLinks(report);
      const draft = report.applicationDraft || localApplicationDraft();
      const lines = [
        `[추천 패키지] ${pkg.title}`,
        `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`,
        `담당 상담사: ${state.case.counselor || "미입력"}`,
        `욕구: ${needs.join(", ")}`,
        "",
        "추천 서비스",
        ...selectedServices.map((service, index) => `${index + 1}. ${service.name} - ${service.summary}`),
        "",
        "HWP 신청서 작성 가이드",
        "- 신청인 성명: 대상자 또는 대리 신청인 성명",
        "- 주민등록번호: ******-******* 형식으로 마스킹 확인",
        `- 거주지 주소: ${state.case.region || "주소 확인 필요"}`,
        `- 신청 복지급여: ${selectedServices.map((service) => service.name).join(", ") || "선택 서비스 확인 필요"}`,
        `- 대상 가구 구분: ${state.case.targetType || "확인 필요"}`,
        "- 제4페이지 [신청 사유] 란: 아래 초안 붙여넣기",
        "",
        "신청 사유 초안",
        draft,
        "",
        "서비스별 딥링크",
        ...links.map((link) => `- ${link.label}: ${link.url}`),
      ];
      navigator.clipboard?.writeText(lines.join("\n")).then(() => showToast("추천서, HWP 작성 가이드, 공식 링크를 함께 복사했습니다.")).catch(() => showToast("복사 권한을 확인해 주세요."));
    };
    copyReport.__hwpCopyPatched = true;
  }

  const nativeRender = render;
  render = function patchedRenderDashboardHwp() {
    const result = nativeRender();
    ensureFeatureStyles();
    insertCounselorField();
    enhanceReportDom();
    installCopyPatch();
    return result;
  };

  window.addEventListener("load", () => {
    installCopyPatch();
    render();
  }, { once: true });

  ensureFeatureStyles();
  render();
})();

(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;
  if (globalThis.__COMMERCIAL_UI_POLISH_PATCHED) return;
  globalThis.__COMMERCIAL_UI_POLISH_PATCHED = true;

  const COMMERCIAL_UI_VERSION = "2026-05-26-commercial-polish";
  globalThis.COMMERCIAL_UI_VERSION = COMMERCIAL_UI_VERSION;

  function ensureCommercialStyles() {
    // Commercial UI styles now live in styles.css; keep this as a no-op for compatibility.
    return;
    if (document.querySelector("#commercial-ui-polish-style")) return;
    const style = document.createElement("style");
    style.id = "commercial-ui-polish-style";
    style.textContent = `
      body.commercial-ui{background:#f4f6f7;color:#172429;-webkit-font-smoothing:antialiased}.commercial-ui .app-shell{grid-template-columns:260px minmax(0,1fr)}.commercial-ui .sidebar{background:#111d22;border-right:0;color:#dbe4e7}.commercial-ui .sidebar-head{border-bottom:1px solid rgba(255,255,255,.08);height:72px}.commercial-ui .sidebar .brand-mark{background:#2f7d72;box-shadow:0 10px 26px rgba(47,125,114,.28)}.commercial-ui .sidebar-title strong{color:#fff;font-size:16px}.commercial-ui .sidebar-title span{color:#8fa2aa}.commercial-ui .nav{padding:18px 12px}.commercial-ui .nav-button{border-radius:8px;color:#aebdc3;font-weight:800;min-height:44px}.commercial-ui .nav-button:hover{background:rgba(255,255,255,.08);color:#fff}.commercial-ui .nav-button.active{background:#e6f4f0;color:#174c46;box-shadow:0 8px 22px rgba(0,0,0,.18)}.commercial-ui .sidebar-foot{border-top:1px solid rgba(255,255,255,.08);padding:16px}.commercial-ui .operator-card{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.1);color:#fff}.commercial-ui .operator-card span{color:#9fb0b7}.commercial-ui .main{background:#f4f6f7}.commercial-ui .topbar{height:72px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce3e6;box-shadow:0 1px 0 rgba(23,36,41,.03);padding:0 26px}.commercial-ui .eyebrow{color:#52646b;font-size:11px;letter-spacing:.04em;text-transform:uppercase}.commercial-ui .page-title{font-size:20px;font-weight:900}.commercial-ui .content{gap:18px;padding:20px 24px 28px}.commercial-ui .workspace-panel{border-color:#dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.04);overflow:hidden}.commercial-ui .panel-head{background:#fff;min-height:68px;padding:16px 18px}.commercial-ui .panel-title{font-size:17px;font-weight:900}.commercial-ui .panel-subtitle{color:#64747b;font-size:13px}.commercial-ui .panel-body{padding:18px}.commercial-ui .grid-2{grid-template-columns:minmax(360px,.92fr) minmax(440px,1.08fr);gap:18px}.commercial-ui .grid-3{gap:14px}.commercial-ui .btn{border-radius:7px;font-weight:900;min-height:40px;transition:background .14s ease,border-color .14s ease,box-shadow .14s ease,transform .14s ease}.commercial-ui .btn:hover{transform:translateY(-1px)}.commercial-ui .btn.primary{background:#2f6f68;box-shadow:0 8px 18px rgba(47,111,104,.18)}.commercial-ui .btn.primary:hover{background:#265d57}.commercial-ui .btn.secondary{background:#e9f5f2;border-color:#c1ddd6;color:#245d55}.commercial-ui .btn.ghost{background:#fff;border-color:#d6e0e3;color:#52646b}.commercial-ui .icon-btn{background:#fff;border-color:#d6e0e3;border-radius:7px}.commercial-ui input,.commercial-ui select,.commercial-ui textarea{border-color:#ccd7dc;border-radius:7px;box-shadow:inset 0 1px 0 rgba(23,36,41,.02)}.commercial-ui textarea{min-height:190px}.commercial-ui input:focus,.commercial-ui select:focus,.commercial-ui textarea:focus{border-color:#2f6f68;box-shadow:0 0 0 3px rgba(47,111,104,.14)}.commercial-ui .pill{border-radius:999px;font-weight:900}.commercial-ui .stat-card{border-color:#dce3e6;border-radius:8px;background:#fff;box-shadow:0 1px 2px rgba(23,36,41,.04)}.commercial-ui .stat-card strong{font-size:26px}.commercial-ui .metric-icon{background:#e7f3ef;color:#245d55}.commercial-ui .service-card,.commercial-ui .package-card,.commercial-ui .package-item,.commercial-ui .source-row,.commercial-ui .check-row,.commercial-ui .faq-row,.commercial-ui .report-block{border-color:#dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.035)}.commercial-ui .service-card{position:relative}.commercial-ui .service-card:hover,.commercial-ui .package-card:hover{border-color:#a9c9c2;box-shadow:0 10px 26px rgba(23,36,41,.08)}.commercial-ui .service-card.selected,.commercial-ui .package-card.active{border-color:#4b9288;box-shadow:inset 4px 0 0 #2f6f68,0 10px 24px rgba(47,111,104,.09)}.commercial-ui .service-card.in-package{background:linear-gradient(90deg,#effaf7 0,#fff 42%);border-color:#9bcfc4}.commercial-ui .package-included-badge{align-items:center;background:#dff2ec;border:1px solid #a7d5ca;border-radius:999px;color:#245d55;display:inline-flex;font-size:11px;font-weight:900;gap:5px;min-height:24px;padding:0 8px}.commercial-ui .search-tools{grid-template-columns:minmax(260px,1.5fr) repeat(3,minmax(128px,.7fr));background:#f8faf9;border:1px solid #dce3e6;border-radius:8px;padding:10px}.commercial-ui .detail-item{background:#f7f9fa;border:1px solid #edf1f2;border-radius:8px}.commercial-ui .report-preview{border-color:#d4dde1;border-radius:8px;box-shadow:0 16px 40px rgba(23,36,41,.08)}.commercial-ui .report-cover{background:#12333a;color:#fff}.commercial-ui .report-cover .muted{color:#c7d6da}.commercial-ui .report-content{padding:24px}.commercial-ui .hwp-guide-card{box-shadow:0 14px 34px rgba(23,36,41,.08)}.case-context-strip{background:#fff;border:1px solid #dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.04);display:grid;grid-template-columns:minmax(220px,1.35fr) repeat(4,minmax(130px,.7fr));gap:0;overflow:hidden}.case-context-item{border-right:1px solid #e5ebed;display:grid;gap:5px;min-height:72px;padding:14px 16px}.case-context-item:last-child{border-right:0}.case-context-label{color:#6a7a82;font-size:11px;font-weight:900;letter-spacing:.03em;text-transform:uppercase}.case-context-value{align-items:center;color:#172429;display:flex;font-size:14px;font-weight:900;gap:8px;min-width:0}.case-context-value span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.case-stage-meter{background:#e8eef0;border-radius:999px;height:8px;overflow:hidden;width:100%}.case-stage-meter span{background:#2f6f68;display:block;height:100%}.commercial-login{background:#eef3f4;grid-template-columns:minmax(360px,460px) minmax(0,1fr)}.commercial-login .login-panel{border-right:1px solid #d7e0e3;box-shadow:18px 0 50px rgba(23,36,41,.08);padding:44px}.commercial-login .login-title{font-size:28px;font-weight:900;letter-spacing:0;line-height:1.34;word-break:keep-all}.commercial-login .login-subtitle{font-size:15px}.login-status-grid{display:grid;gap:10px;margin-top:28px}.login-status-row{align-items:center;background:#f7faf9;border:1px solid #dce5e3;border-radius:8px;display:flex;justify-content:space-between;min-height:48px;padding:0 14px}.login-product-preview{background:#fff;border:1px solid #d7e0e3;border-radius:8px;box-shadow:0 24px 70px rgba(23,36,41,.14);display:grid;gap:0;max-width:980px;overflow:hidden;width:100%}.login-preview-head{align-items:center;background:#12333a;color:#fff;display:flex;justify-content:space-between;padding:16px 18px}.login-preview-body{display:grid;grid-template-columns:1fr 1.1fr;gap:0}.login-preview-panel{border-right:1px solid #e1e8ea;display:grid;gap:12px;padding:18px}.login-preview-panel:last-child{border-right:0}.login-preview-list{display:grid;gap:8px}.login-preview-line{background:#f5f8f8;border:1px solid #e2e9eb;border-radius:8px;min-height:42px;padding:10px 12px}.commercial-ui .toast{border-radius:8px;box-shadow:0 16px 36px rgba(23,36,41,.22)}@media(max-width:1180px){.case-context-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.case-context-item{border-bottom:1px solid #e5ebed}.case-context-item:nth-child(2n){border-right:0}.commercial-ui .grid-2,.commercial-ui .package-layout{grid-template-columns:1fr}.login-preview-body{grid-template-columns:1fr}}@media(max-width:860px){.commercial-ui .app-shell{grid-template-columns:1fr}.commercial-ui .sidebar{background:#111d22}.commercial-ui .topbar{height:auto;min-height:64px;padding:10px 14px}.commercial-ui .content{padding:14px}.case-context-strip{grid-template-columns:1fr}.case-context-item{border-right:0}.commercial-login{grid-template-columns:1fr}.commercial-login .login-panel{min-height:auto;padding:30px 22px}.commercial-login .login-visual{padding:0 16px 24px}.login-product-preview{box-shadow:0 12px 34px rgba(23,36,41,.1)}}@media print{.case-context-strip,.login-status-grid,.login-product-preview{display:none!important}.commercial-ui .report-cover{background:#fff!important;color:#111!important;border-bottom:2px solid #111}.commercial-ui .report-cover .muted{color:#333!important}.commercial-ui .report-preview{box-shadow:none}}
    `;
    document.head.appendChild(style);
  }

  function stageInfo() {
    if (state.lastReport) return { label: "추천서 생성", pct: 100 };
    if (state.packages?.length) return { label: "패키지 조정", pct: 74 };
    if (state.structured) return { label: "AI 구조화", pct: 48 };
    if (state.case?.memo) return { label: "상담 입력", pct: 24 };
    return { label: "신규 상담", pct: 8 };
  }

  function selectedServiceCount() {
    try {
      return selectedPackage()?.items?.filter((item) => item.included).length || 0;
    } catch (_error) {
      return 0;
    }
  }

  function topNeeds() {
    const needs = state.structured?.needs?.length ? state.structured.needs : state.case?.issueTypes || [];
    return needs.length ? needs.slice(0, 4).join(" · ") : "욕구 미분류";
  }

  function insertContextStrip() {
    if (!state.loggedIn) return;
    const content = document.querySelector(".content");
    if (!content || content.querySelector(".case-context-strip")) return;
    const stage = stageInfo();
    content.insertAdjacentHTML(
      "afterbegin",
      `<section class="case-context-strip" aria-label="현재 상담 요약">
        <div class="case-context-item">
          <span class="case-context-label">Case</span>
          <strong class="case-context-value">${icon("folder-open")}<span>${escapeHtml(state.case?.title || "상담 제목 미입력")}</span></strong>
        </div>
        <div class="case-context-item">
          <span class="case-context-label">담당자</span>
          <strong class="case-context-value">${icon("user-check")}<span>${escapeHtml(state.case?.counselor || "미배정")}</span></strong>
        </div>
        <div class="case-context-item">
          <span class="case-context-label">지역</span>
          <strong class="case-context-value">${icon("map-pin")}<span>${escapeHtml(state.case?.region || "지역 미입력")}</span></strong>
        </div>
        <div class="case-context-item">
          <span class="case-context-label">추천 후보</span>
          <strong class="case-context-value">${icon("check-square")}<span>${selectedServiceCount()}개 선택</span></strong>
        </div>
        <div class="case-context-item">
          <span class="case-context-label">진행 단계</span>
          <strong class="case-context-value"><span>${escapeHtml(stage.label)}</span></strong>
          <div class="case-stage-meter"><span style="width:${stage.pct}%"></span></div>
        </div>
      </section>`
    );
  }

  function getServiceIdFromCard(card) {
    const handler = Array.from(card.querySelectorAll("[onclick]"))
      .map((node) => node.getAttribute("onclick") || "")
      .find((text) => /openServiceDetail|addServiceToPackage|togglePackageItem/.test(text));
    if (!handler) return "";
    const match = handler.match(/'(.*?)'/);
    return match?.[1] || "";
  }

  function markPackageState() {
    const pkg = typeof selectedPackage === "function" ? selectedPackage() : null;
    const included = new Set((pkg?.items || []).filter((item) => item.included).map((item) => item.serviceId));
    document.querySelectorAll(".service-card").forEach((card) => {
      const serviceId = getServiceIdFromCard(card);
      if (!serviceId || !included.has(serviceId)) return;
      card.classList.add("in-package");
      const title = card.querySelector(".service-title");
      if (title && !title.querySelector(".package-included-badge")) {
        title.insertAdjacentHTML("beforeend", `<span class="package-included-badge">${icon("check")} 패키지 포함</span>`);
      }
    });
    document.querySelectorAll(".package-item").forEach((item) => {
      const serviceId = getServiceIdFromCard(item);
      const buttons = item.querySelector(".priority-buttons");
      if (!serviceId || !buttons || buttons.querySelector("[data-commercial-detail]")) return;
      buttons.insertAdjacentHTML("afterbegin", `<button class="icon-btn" data-commercial-detail title="상세 보기" onclick="openServiceDetail('${escapeHtml(serviceId)}')">${icon("panel-top-open")}</button>`);
    });
  }

  function makeUrlsClickable() {
    document.querySelectorAll(".detail-item").forEach((item) => {
      const label = item.querySelector("strong")?.textContent?.trim();
      const value = item.querySelector("span");
      const url = value?.textContent?.trim();
      if (label !== "URL" || !/^https?:\/\//i.test(url) || value.querySelector("a")) return;
      value.innerHTML = `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>`;
    });
  }

  function postProcessCommercialUi() {
    document.body.classList.add("commercial-ui");
    ensureCommercialStyles();
    insertContextStrip();
    markPackageState();
    makeUrlsClickable();
    window.lucide?.createIcons?.();
  }

  const originalRenderLogin = renderLogin;
  renderLogin = function commercialRenderLogin() {
    return `
      <main class="login-shell commercial-login">
        <section class="login-panel">
          <div>
            <div class="brand-lockup">
              <div class="brand-mark">${icon("heart-handshake")}</div>
              <div>복지연계 코파일럿</div>
            </div>
            <h1 class="login-title">상담부터 신청서 초안까지 한 흐름으로 관리합니다</h1>
            <p class="login-subtitle">현장 종사자가 상담 사례, 복지서비스 후보, 기관 연결, 추천서를 같은 화면 흐름에서 검토할 수 있는 업무용 웹입니다.</p>
            <form class="login-form" onsubmit="event.preventDefault(); state.loggedIn = true; render(); hydrateBackend();">
              <div class="field">
                <label for="login-id">아이디</label>
                <input id="login-id" value="case.worker" autocomplete="username" />
              </div>
              <div class="field">
                <label for="login-pw">비밀번호</label>
                <input id="login-pw" value="demo2026" type="password" autocomplete="current-password" />
              </div>
              <button class="btn primary" type="submit">${icon("log-in")} 업무 화면으로 이동</button>
            </form>
            <div class="login-status-grid">
              <div class="login-status-row"><strong>공공데이터</strong>${pill("연결 확인", "green")}</div>
              <div class="login-status-row"><strong>AI 구조화</strong>${pill("Gemini 연동", "blue")}</div>
              <div class="login-status-row"><strong>추천서</strong>${pill("HWP 가이드 포함", "amber")}</div>
            </div>
          </div>
          <div class="login-meta">
            ${pill("현장 상담")}
            ${pill("복지서비스 검색")}
            ${pill("추천서 생성")}
          </div>
        </section>
        <section class="login-visual" aria-label="제품 미리보기">
          <div class="login-product-preview">
            <div class="login-preview-head">
              <strong>통합 상담 대시보드</strong>
              <span>CASE 2026-WF-001</span>
            </div>
            <div class="login-preview-body">
              <div class="login-preview-panel">
                <strong>상담 진행 현황</strong>
                <div class="login-preview-list">
                  <div class="login-preview-line">상담 입력 · 담당자/지역 확인</div>
                  <div class="login-preview-line">AI 구조화 · 욕구/위험 신호 추출</div>
                  <div class="login-preview-line">패키지 추천 · 후보 4건 선택</div>
                </div>
              </div>
              <div class="login-preview-panel">
                <strong>추천서 프리뷰</strong>
                <div class="login-preview-list">
                  <div class="login-preview-line">사례 요약과 우선순위 판단</div>
                  <div class="login-preview-line">서비스별 신청 경로와 구비서류</div>
                  <div class="login-preview-line">신청 사유 초안 및 공식 링크</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    `;
  };
  renderLogin.__original = originalRenderLogin;

  const previousRender = render;
  render = function commercialRender() {
    const result = previousRender();
    postProcessCommercialUi();
    return result;
  };

  ensureCommercialStyles();
  render();
})();

