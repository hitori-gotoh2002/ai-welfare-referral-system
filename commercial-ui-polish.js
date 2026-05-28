(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;
  if (globalThis.__COMMERCIAL_UI_POLISH_PATCHED) return;
  globalThis.__COMMERCIAL_UI_POLISH_PATCHED = true;

  const COMMERCIAL_UI_VERSION = "2026-05-26-commercial-polish";
  globalThis.COMMERCIAL_UI_VERSION = COMMERCIAL_UI_VERSION;

  function ensureCommercialStyles() {
    if (document.querySelector("#commercial-ui-polish-style")) return;
    const style = document.createElement("style");
    style.id = "commercial-ui-polish-style";
    style.textContent = `
      body.commercial-ui{background:#f4f6f7;color:#172429;-webkit-font-smoothing:antialiased}
      .commercial-ui .app-shell{grid-template-columns:260px minmax(0,1fr)}
      .commercial-ui .sidebar{background:#111d22;border-right:0;color:#dbe4e7}
      .commercial-ui .sidebar-head{border-bottom:1px solid rgba(255,255,255,.08);height:72px}
      .commercial-ui .sidebar .brand-mark{background:#2f7d72;box-shadow:0 10px 26px rgba(47,125,114,.28)}
      .commercial-ui .sidebar-title strong{color:#fff;font-size:16px}
      .commercial-ui .sidebar-title span{color:#8fa2aa}
      .commercial-ui .nav{padding:18px 12px}
      .commercial-ui .nav-button{border-radius:8px;color:#aebdc3;font-weight:800;min-height:44px}
      .commercial-ui .nav-button:hover{background:rgba(255,255,255,.08);color:#fff}
      .commercial-ui .nav-button.active{background:#e6f4f0;color:#174c46;box-shadow:0 8px 22px rgba(0,0,0,.18)}
      .commercial-ui .sidebar-foot{border-top:1px solid rgba(255,255,255,.08);padding:16px}
      .commercial-ui .operator-card{background:rgba(255,255,255,.07);border-color:rgba(255,255,255,.1);color:#fff}
      .commercial-ui .operator-card span{color:#9fb0b7}
      .commercial-ui .main{background:#f4f6f7}
      .commercial-ui .topbar{height:72px;background:rgba(255,255,255,.94);border-bottom:1px solid #dce3e6;box-shadow:0 1px 0 rgba(23,36,41,.03);padding:0 26px}
      .commercial-ui .eyebrow{color:#52646b;font-size:11px;letter-spacing:.04em;text-transform:uppercase}
      .commercial-ui .page-title{font-size:20px;font-weight:900}
      .commercial-ui .content{gap:18px;padding:20px 24px 28px}
      .commercial-ui .workspace-panel{border-color:#dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.04);overflow:hidden}
      .commercial-ui .panel-head{background:#fff;min-height:68px;padding:16px 18px}
      .commercial-ui .panel-title{font-size:17px;font-weight:900}
      .commercial-ui .panel-subtitle{color:#64747b;font-size:13px}
      .commercial-ui .panel-body{padding:18px}
      .commercial-ui .grid-2{grid-template-columns:minmax(360px,.92fr) minmax(440px,1.08fr);gap:18px}
      .commercial-ui .grid-3{gap:14px}
      .commercial-ui .btn{border-radius:7px;font-weight:900;min-height:40px;transition:background .14s ease,border-color .14s ease,box-shadow .14s ease,transform .14s ease}
      .commercial-ui .btn:hover{transform:translateY(-1px)}
      .commercial-ui .btn.primary{background:#2f6f68;box-shadow:0 8px 18px rgba(47,111,104,.18)}
      .commercial-ui .btn.primary:hover{background:#265d57}
      .commercial-ui .btn.secondary{background:#e9f5f2;border-color:#c1ddd6;color:#245d55}
      .commercial-ui .btn.ghost{background:#fff;border-color:#d6e0e3;color:#52646b}
      .commercial-ui .icon-btn{background:#fff;border-color:#d6e0e3;border-radius:7px}
      .commercial-ui input,.commercial-ui select,.commercial-ui textarea{border-color:#ccd7dc;border-radius:7px;box-shadow:inset 0 1px 0 rgba(23,36,41,.02)}
      .commercial-ui textarea{min-height:190px}
      .commercial-ui input:focus,.commercial-ui select:focus,.commercial-ui textarea:focus{border-color:#2f6f68;box-shadow:0 0 0 3px rgba(47,111,104,.14)}
      .commercial-ui .pill{border-radius:999px;font-weight:900}
      .commercial-ui .stat-card{border-color:#dce3e6;border-radius:8px;background:#fff;box-shadow:0 1px 2px rgba(23,36,41,.04)}
      .commercial-ui .stat-card strong{font-size:26px}
      .commercial-ui .metric-icon{background:#e7f3ef;color:#245d55}
      .commercial-ui .service-card,.commercial-ui .package-card,.commercial-ui .package-item,.commercial-ui .source-row,.commercial-ui .check-row,.commercial-ui .faq-row,.commercial-ui .report-block{border-color:#dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.035)}
      .commercial-ui .service-card{position:relative}
      .commercial-ui .service-card:hover,.commercial-ui .package-card:hover{border-color:#a9c9c2;box-shadow:0 10px 26px rgba(23,36,41,.08)}
      .commercial-ui .service-card.selected,.commercial-ui .package-card.active{border-color:#4b9288;box-shadow:inset 4px 0 0 #2f6f68,0 10px 24px rgba(47,111,104,.09)}
      .commercial-ui .service-card.in-package{background:linear-gradient(90deg,#effaf7 0,#fff 42%);border-color:#9bcfc4}
      .commercial-ui .package-included-badge{align-items:center;background:#dff2ec;border:1px solid #a7d5ca;border-radius:999px;color:#245d55;display:inline-flex;font-size:11px;font-weight:900;gap:5px;min-height:24px;padding:0 8px}
      .commercial-ui .search-tools{grid-template-columns:minmax(260px,1.5fr) repeat(3,minmax(128px,.7fr));background:#f8faf9;border:1px solid #dce3e6;border-radius:8px;padding:10px}
      .commercial-ui .detail-item{background:#f7f9fa;border:1px solid #edf1f2;border-radius:8px}
      .commercial-ui .report-preview{border-color:#d4dde1;border-radius:8px;box-shadow:0 16px 40px rgba(23,36,41,.08)}
      .commercial-ui .report-cover{background:#12333a;color:#fff}
      .commercial-ui .report-cover .muted{color:#c7d6da}
      .commercial-ui .report-content{padding:24px}
      .commercial-ui .hwp-guide-card{box-shadow:0 14px 34px rgba(23,36,41,.08)}
      .case-context-strip{background:#fff;border:1px solid #dce3e6;border-radius:8px;box-shadow:0 1px 2px rgba(23,36,41,.04);display:grid;grid-template-columns:minmax(220px,1.35fr) repeat(4,minmax(130px,.7fr));gap:0;overflow:hidden}
      .case-context-item{border-right:1px solid #e5ebed;display:grid;gap:5px;min-height:72px;padding:14px 16px}
      .case-context-item:last-child{border-right:0}
      .case-context-label{color:#6a7a82;font-size:11px;font-weight:900;letter-spacing:.03em;text-transform:uppercase}
      .case-context-value{align-items:center;color:#172429;display:flex;font-size:14px;font-weight:900;gap:8px;min-width:0}
      .case-context-value span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .case-stage-meter{background:#e8eef0;border-radius:999px;height:8px;overflow:hidden;width:100%}
      .case-stage-meter span{background:#2f6f68;display:block;height:100%}
      .commercial-login{background:#eef3f4;grid-template-columns:minmax(360px,460px) minmax(0,1fr)}
      .commercial-login .login-panel{border-right:1px solid #d7e0e3;box-shadow:18px 0 50px rgba(23,36,41,.08);padding:44px}
      .commercial-login .login-title{font-size:28px;font-weight:900;letter-spacing:0;line-height:1.34;word-break:keep-all}
      .commercial-login .login-subtitle{font-size:15px}
      .login-status-grid{display:grid;gap:10px;margin-top:28px}
      .login-status-row{align-items:center;background:#f7faf9;border:1px solid #dce5e3;border-radius:8px;display:flex;justify-content:space-between;min-height:48px;padding:0 14px}
      .login-product-preview{background:#fff;border:1px solid #d7e0e3;border-radius:8px;box-shadow:0 24px 70px rgba(23,36,41,.14);display:grid;gap:0;max-width:980px;overflow:hidden;width:100%}
      .login-preview-head{align-items:center;background:#12333a;color:#fff;display:flex;justify-content:space-between;padding:16px 18px}
      .login-preview-body{display:grid;grid-template-columns:1fr 1.1fr;gap:0}
      .login-preview-panel{border-right:1px solid #e1e8ea;display:grid;gap:12px;padding:18px}
      .login-preview-panel:last-child{border-right:0}
      .login-preview-list{display:grid;gap:8px}
      .login-preview-line{background:#f5f8f8;border:1px solid #e2e9eb;border-radius:8px;min-height:42px;padding:10px 12px}
      .commercial-ui .toast{border-radius:8px;box-shadow:0 16px 36px rgba(23,36,41,.22)}
      @media(max-width:1180px){.case-context-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.case-context-item{border-bottom:1px solid #e5ebed}.case-context-item:nth-child(2n){border-right:0}.commercial-ui .grid-2,.commercial-ui .package-layout{grid-template-columns:1fr}.login-preview-body{grid-template-columns:1fr}}
      @media(max-width:860px){.commercial-ui .app-shell{grid-template-columns:1fr}.commercial-ui .sidebar{background:#111d22}.commercial-ui .topbar{height:auto;min-height:64px;padding:10px 14px}.commercial-ui .content{padding:14px}.case-context-strip{grid-template-columns:1fr}.case-context-item{border-right:0}.commercial-login{grid-template-columns:1fr}.commercial-login .login-panel{min-height:auto;padding:30px 22px}.commercial-login .login-visual{padding:0 16px 24px}.login-product-preview{box-shadow:0 12px 34px rgba(23,36,41,.1)}}
      @media print{.case-context-strip,.login-status-grid,.login-product-preview{display:none!important}.commercial-ui .report-cover{background:#fff!important;color:#111!important;border-bottom:2px solid #111}.commercial-ui .report-cover .muted{color:#333!important}.commercial-ui .report-preview{box-shadow:none}}
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

  function getServiceIdFromNode(node) {
    const handler = Array.from(node.querySelectorAll("[onclick]"))
      .map((entry) => entry.getAttribute("onclick") || "")
      .find((text) => /openServiceDetail|addServiceToPackage|togglePackageItem/.test(text));
    return handler?.match(/'(.*?)'/)?.[1] || "";
  }

  function markPackageState() {
    const pkg = typeof selectedPackage === "function" ? selectedPackage() : null;
    const included = new Set((pkg?.items || []).filter((item) => item.included).map((item) => item.serviceId));
    document.querySelectorAll(".service-card").forEach((card) => {
      const serviceId = getServiceIdFromNode(card);
      if (!serviceId || !included.has(serviceId)) return;
      card.classList.add("in-package");
      const title = card.querySelector(".service-title");
      if (title && !title.querySelector(".package-included-badge")) {
        title.insertAdjacentHTML("beforeend", `<span class="package-included-badge">${icon("check")} 패키지 포함</span>`);
      }
    });
    document.querySelectorAll(".package-item").forEach((item) => {
      const serviceId = getServiceIdFromNode(item);
      const buttons = item.querySelector(".priority-buttons");
      const hasDetailButton = Array.from(buttons?.querySelectorAll("[onclick]") || []).some((button) =>
        (button.getAttribute("onclick") || "").includes("openServiceDetail")
      );
      if (!serviceId || !buttons || buttons.querySelector("[data-commercial-detail]") || hasDetailButton) return;
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
