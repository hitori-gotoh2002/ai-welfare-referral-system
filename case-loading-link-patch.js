(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;

  function cssOnce() {
    if (document.querySelector("#case-loading-link-patch-style")) return;
    const style = document.createElement("style");
    style.id = "case-loading-link-patch-style";
    style.textContent = `
      .inline-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #27665f;
        font-weight: 700;
        text-decoration: none;
      }
      .inline-link:hover { text-decoration: underline; }
      .analyze-loading-note { margin: 0 0 12px; }
      .btn.is-loading,
      .icon-btn.is-loading {
        cursor: progress;
        opacity: 0.72;
      }
      .btn.is-loading svg { animation: analyze-spin 1s linear infinite; }
      @keyframes analyze-spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
  }

  function safeUrl(value) {
    const url = String(value || "").trim();
    return /^https?:\/\//i.test(url) ? url : "";
  }

  function externalLink(url, label = "공식 상세 페이지 열기") {
    const href = safeUrl(url);
    if (!href) return "";
    return `<a class="inline-link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${icon("external-link")} ${escapeHtml(label)}</a>`;
  }

  function serviceFromModal() {
    const title = document.querySelector(".modal .panel-title")?.textContent?.trim();
    if (!title || !Array.isArray(services)) return null;
    return services.find((service) => service.name === title) || null;
  }

  function linkUrlFields() {
    const modalService = serviceFromModal();
    document.querySelectorAll(".detail-item").forEach((item) => {
      const title = item.querySelector("strong")?.textContent?.trim().toUpperCase();
      const span = item.querySelector("span");
      if (title !== "URL" || !span || span.querySelector("a")) return;
      const href = modalService?.detailUrl || span.textContent.trim();
      const link = externalLink(href);
      if (link) span.innerHTML = link;
    });
  }

  function reflectAnalyzeLoading() {
    const loading = Boolean(state.__analyzeLoading);
    document.querySelectorAll('button[onclick*="inferStructure"]').forEach((button) => {
      if (!button.dataset.originalAnalyzeHtml) {
        button.dataset.originalAnalyzeHtml = button.innerHTML;
      }
      button.disabled = loading;
      button.classList.toggle("is-loading", loading);
      if (loading) {
        button.innerHTML = `${icon("loader-circle")} AI 구조화 중`;
      } else {
        button.innerHTML = button.dataset.originalAnalyzeHtml;
      }
    });

    const host = document.querySelector(".content") || document.querySelector("#app");
    if (!host) return;
    let note = host.querySelector(".analyze-loading-note");
    if (loading && state.view === "case") {
      if (!note) {
        note = document.createElement("div");
        note.className = "status-note green analyze-loading-note";
        host.prepend(note);
      }
      note.innerHTML = `${icon("loader-circle")}<span>상담 내용을 AI가 구조화하고 추천 후보를 계산하고 있습니다.</span>`;
    } else if (note) {
      note.remove();
    }
  }

  const nativeRender = render;
  render = function patchedRenderCaseLoadingLink() {
    const result = nativeRender();
    cssOnce();
    linkUrlFields();
    reflectAnalyzeLoading();
    return result;
  };

  if (typeof inferStructure === "function" && !globalThis.__CASE_ANALYZE_LOADING_PATCHED) {
    globalThis.__CASE_ANALYZE_LOADING_PATCHED = true;
    const nativeInferStructure = inferStructure;
    inferStructure = async function patchedInferStructureLoading(options = {}) {
      if (state.__analyzeLoading) return;
      state.__analyzeLoading = true;
      render();
      try {
        return await nativeInferStructure(options);
      } finally {
        state.__analyzeLoading = false;
        render();
      }
    };
  }

  render();
})();
