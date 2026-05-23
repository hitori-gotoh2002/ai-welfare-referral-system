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
          ${detailItem("URL", service.url)}
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
