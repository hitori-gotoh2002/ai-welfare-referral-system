(() => {
  if (globalThis.__COMMERCIAL_UI_STYLE_FIX_APPLIED) return;
  globalThis.__COMMERCIAL_UI_STYLE_FIX_APPLIED = true;

  function ensureCommercialStyleFix() {
    if (document.querySelector("#commercial-ui-style-fix")) return;
    const style = document.createElement("style");
    style.id = "commercial-ui-style-fix";
    style.textContent = `
      .case-context-strip{
        background:#fff;
        border:1px solid #dce3e6;
        border-radius:8px;
        box-shadow:0 1px 2px rgba(23,36,41,.04);
        display:grid;
        grid-template-columns:minmax(220px,1.35fr) repeat(4,minmax(130px,.7fr));
        overflow:hidden;
        width:100%;
      }
      .case-context-item{
        border-right:1px solid #e5ebed;
        display:grid;
        gap:5px;
        min-height:72px;
        padding:14px 16px;
      }
      .case-context-item:last-child{border-right:0}
      .case-context-label{
        color:#6a7a82;
        font-size:11px;
        font-weight:900;
        letter-spacing:.03em;
        text-transform:uppercase;
      }
      .case-context-value{
        align-items:center;
        color:#172429;
        display:flex;
        font-size:14px;
        font-weight:900;
        gap:8px;
        min-width:0;
      }
      .case-context-value .icon{width:17px;height:17px;flex:0 0 auto}
      .case-context-value span{
        overflow:hidden;
        text-overflow:ellipsis;
        white-space:nowrap;
      }
      .case-stage-meter{
        background:#e8eef0;
        border-radius:999px;
        height:8px;
        overflow:hidden;
        width:100%;
      }
      .case-stage-meter span{
        background:#2f6f68;
        display:block;
        height:100%;
      }
      .commercial-login{
        background:#eef3f4;
        grid-template-columns:minmax(360px,460px) minmax(0,1fr);
      }
      .commercial-login .login-panel{
        border-right:1px solid #d7e0e3;
        box-shadow:18px 0 50px rgba(23,36,41,.08);
        padding:44px;
      }
      .commercial-login .login-title{
        font-size:28px;
        font-weight:900;
        letter-spacing:0;
        line-height:1.34;
        word-break:keep-all;
      }
      .commercial-login .login-subtitle{
        font-size:15px;
      }
      .login-status-grid{
        display:grid;
        gap:10px;
        margin-top:28px;
      }
      .login-status-row{
        align-items:center;
        background:#f7faf9;
        border:1px solid #dce5e3;
        border-radius:8px;
        display:flex;
        justify-content:space-between;
        min-height:48px;
        padding:0 14px;
      }
      .login-product-preview{
        background:#fff;
        border:1px solid #d7e0e3;
        border-radius:8px;
        box-shadow:0 24px 70px rgba(23,36,41,.14);
        display:grid;
        gap:0;
        max-width:980px;
        overflow:hidden;
        width:100%;
      }
      .login-preview-head{
        align-items:center;
        background:#12333a;
        color:#fff;
        display:flex;
        justify-content:space-between;
        padding:16px 18px;
      }
      .login-preview-body{
        display:grid;
        gap:0;
        grid-template-columns:1fr 1.1fr;
      }
      .login-preview-panel{
        border-right:1px solid #e1e8ea;
        display:grid;
        gap:12px;
        padding:18px;
      }
      .login-preview-panel:last-child{border-right:0}
      .login-preview-list{
        display:grid;
        gap:8px;
      }
      .login-preview-line{
        background:#f5f8f8;
        border:1px solid #e2e9eb;
        border-radius:8px;
        line-height:1.45;
        min-height:42px;
        padding:10px 12px;
      }
      @media(max-width:1180px){
        .case-context-strip{grid-template-columns:repeat(2,minmax(0,1fr))}
        .case-context-item{border-bottom:1px solid #e5ebed}
        .case-context-item:nth-child(2n){border-right:0}
        .login-preview-body{grid-template-columns:1fr}
      }
      @media(max-width:760px){
        .case-context-strip{grid-template-columns:1fr}
        .case-context-item{border-right:0}
        .commercial-login{grid-template-columns:1fr}
        .commercial-login .login-panel{min-height:auto;padding:30px 22px}
        .commercial-login .login-visual{padding:0 16px 24px}
        .login-product-preview{box-shadow:0 12px 34px rgba(23,36,41,.1)}
      }
    `;
    document.head.appendChild(style);
  }

  ensureCommercialStyleFix();
  const originalRender = globalThis.render;
  if (typeof originalRender === "function" && !originalRender.__styleFixWrapped) {
    globalThis.render = function renderWithCommercialStyleFix(...args) {
      const result = originalRender.apply(this, args);
      ensureCommercialStyleFix();
      window.lucide?.createIcons?.();
      return result;
    };
    globalThis.render.__styleFixWrapped = true;
  }
})();
