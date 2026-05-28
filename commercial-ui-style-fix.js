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
      @media(max-width:1180px){
        .case-context-strip{grid-template-columns:repeat(2,minmax(0,1fr))}
        .case-context-item{border-bottom:1px solid #e5ebed}
        .case-context-item:nth-child(2n){border-right:0}
      }
      @media(max-width:760px){
        .case-context-strip{grid-template-columns:1fr}
        .case-context-item{border-right:0}
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
