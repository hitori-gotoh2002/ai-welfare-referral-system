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
    if (state.structured.llmUsed) {
      return note("green", "Gemini가 상담 메모를 구조화했습니다. 최종 판단은 상담자가 확인해야 합니다.");
    }
    if (state.structured.llmError) {
      return note("amber", "Gemini 응답 실패로 규칙 기반 분석을 사용했습니다. 추천은 계속 가능하지만 AI 구조화 품질은 낮을 수 있습니다.");
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
      const detailErrors = service.detailMeta && Array.isArray(service.detailMeta.errors) ? service.detailMeta.errors : [];
      const errors = detailErrors.length ? ` (${detailErrors.slice(0, 2).join(" / ")})` : "";
      return note("amber", `상세조회 API 정보를 불러오지 못해 목록·기본 정보를 표시합니다.${errors}`);
    }
    return note("amber", "기관·민간 항목은 공공 복지서비스 상세조회 대상이 아니어서 기본 정보를 표시합니다.");
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
    const nativeRenderServiceModal = renderServiceModal;
    renderServiceModal = function patchedRenderServiceModal(serviceId) {
      const service = services.find((item) => item.id === serviceId);
      const html = nativeRenderServiceModal(serviceId);
      if (!service || !html) return html;
      return html.replace('<p class="service-summary">', `${detailStatus(service)}<p class="service-summary">`);
    };
  }

  installStatusStyles();
})();
