(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;
  if (globalThis.__CASE_LIST_PERSISTENCE_PATCHED) return;
  globalThis.__CASE_LIST_PERSISTENCE_PATCHED = true;

  let isSavingCase = false;

  try {
    recentCases = [];
  } catch (_error) {
    // The base app defines recentCases in the global lexical scope.
  }

  function installCaseListStyles() {
    if (document.querySelector("#case-list-persistence-style")) return;
    const style = document.createElement("style");
    style.id = "case-list-persistence-style";
    style.textContent = `
      .case-list-page {
        display: grid;
        gap: 18px;
      }
      .case-list-hero .panel-body {
        display: grid;
        gap: 16px;
      }
      .case-summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
      }
      .case-summary-item {
        border: 1px solid #dde6e8;
        border-radius: 8px;
        background: #f8faf9;
        display: grid;
        gap: 6px;
        min-height: 78px;
        padding: 13px 14px;
      }
      .case-summary-label {
        color: #687a81;
        font-size: 12px;
        font-weight: 900;
      }
      .case-summary-value {
        color: #172429;
        font-size: 15px;
        font-weight: 900;
        line-height: 1.35;
        overflow-wrap: anywhere;
      }
      .case-list-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .case-list-table-wrap {
        overflow-x: auto;
      }
      .case-list-table {
        border-collapse: separate;
        border-spacing: 0;
        min-width: 780px;
        width: 100%;
      }
      .case-list-table th,
      .case-list-table td {
        border-bottom: 1px solid #e4ebed;
        padding: 12px 10px;
        text-align: left;
        vertical-align: middle;
      }
      .case-list-table th {
        color: #65777d;
        font-size: 12px;
        font-weight: 900;
        background: #f7faf9;
      }
      .case-list-table td {
        color: #26383a;
        font-size: 14px;
      }
      .case-list-title {
        color: #172429;
        display: block;
        font-weight: 900;
        max-width: 280px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .case-list-memo {
        color: #78878d;
        display: block;
        font-size: 12px;
        margin-top: 3px;
        max-width: 320px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .case-list-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 6px;
        white-space: nowrap;
      }
      .case-list-empty {
        border: 1px dashed #cbd8dc;
        border-radius: 8px;
        background: #f8faf9;
        color: #66777d;
        display: grid;
        gap: 8px;
        min-height: 170px;
        place-items: center;
        padding: 28px;
        text-align: center;
      }
      .case-list-empty strong {
        color: #172429;
        font-size: 17px;
      }
      .case-list-empty p {
        margin: 0;
      }
      .case-list-note {
        border: 1px solid #dce7e9;
        border-radius: 8px;
        background: #fff;
        color: #52646b;
        line-height: 1.55;
        padding: 14px 16px;
      }
      body.commercial-ui .case-context-strip {
        display: none !important;
      }
      @media (max-width: 1100px) {
        .case-summary-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 720px) {
        .case-summary-grid {
          grid-template-columns: 1fr;
        }
        .case-list-buttons {
          justify-content: flex-start;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function workflowStatus() {
    if (state.lastReport) return "추천서 작성";
    if (state.packages?.length) return "패키지 검토";
    if (state.structured) return "AI 구조화 완료";
    if (state.case?.memo?.trim()) return "상담 입력";
    return "신규 상담";
  }

  function selectedCount() {
    try {
      return selectedPackage()?.items?.filter((item) => item.included).length || 0;
    } catch (_error) {
      return 0;
    }
  }

  function currentNeeds() {
    const needs = state.structured?.needs || state.case?.issueTypes || [];
    return Array.isArray(needs) ? needs : [];
  }

  function compactDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 16).replace("T", " ");
    return date.toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function truncate(value, limit = 80) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
  }

  function needsForRecord(item) {
    if (typeof caseNeeds === "function") return caseNeeds(item);
    return Array.isArray(item?.needs) ? item.needs : Array.isArray(item?.issueTypes) ? item.issueTypes : [];
  }

  function summaryItem(label, value) {
    return `
      <div class="case-summary-item">
        <span class="case-summary-label">${escapeHtml(label)}</span>
        <span class="case-summary-value">${escapeHtml(value || "-")}</span>
      </div>
    `;
  }

  function renderCaseRows() {
    if (!recentCases.length) {
      return `
        <div class="case-list-empty">
          <div>
            <strong>저장된 상담이 없습니다.</strong>
            <p>상담 입력 화면에서 내용을 작성한 뒤 저장하면 이곳에 상담 목록으로 쌓입니다.</p>
          </div>
          <button class="btn primary" onclick="setView('case')">${icon("clipboard-pen")} 상담 입력으로 이동</button>
        </div>
      `;
    }

    return `
      <div class="case-list-table-wrap">
        <table class="case-list-table">
          <thead>
            <tr>
              <th>상담</th>
              <th>지역</th>
              <th>대상</th>
              <th>욕구</th>
              <th>상태</th>
              <th>저장일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            ${recentCases
              .map((item) => {
                const needs = needsForRecord(item);
                return `
                  <tr>
                    <td>
                      <span class="case-list-title">${escapeHtml(item.title || "상담")}</span>
                      <span class="case-list-memo">${escapeHtml(truncate(item.memo || ""))}</span>
                    </td>
                    <td>${escapeHtml(item.region || "-")}</td>
                    <td>${escapeHtml(item.targetType || item.target || "-")}</td>
                    <td><div class="pill-row">${needs.slice(0, 4).map((need) => pill(need, needsColor(need))).join("")}</div></td>
                    <td>${pill(item.status || "상담 저장", "green")}</td>
                    <td>${escapeHtml(compactDate(item.updatedAt || item.savedAt))}</td>
                    <td>
                      <div class="case-list-buttons">
                        <button class="btn secondary" onclick="loadRecentCase('${escapeHtml(item.id)}')">${icon("folder-open")} 이어서 진행</button>
                        <button class="btn ghost" onclick="deleteSavedCase('${escapeHtml(item.id)}')">${icon("trash-2")} 삭제</button>
                      </div>
                    </td>
                  </tr>
                `;
              })
              .join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  async function refreshCaseList({ renderAfter = false } = {}) {
    try {
      const data = await apiFetch("/api/cases");
      recentCases = Array.isArray(data.cases) ? data.cases : [];
    } catch (_error) {
      recentCases = [];
    }
    if (renderAfter) render();
  }

  renderDashboard = function renderCaseListDashboard() {
    const needs = currentNeeds();
    const serviceLabel = selectedCount() ? `${selectedCount()}개 선택` : "미선택";
    return `
      <div class="case-list-page">
        <section class="workspace-panel case-list-hero">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">상담 업무 대시보드</h2>
              <p class="panel-subtitle">실제 저장된 상담을 기준으로 이어서 작업합니다.</p>
            </div>
            <div class="case-list-actions">
              <button class="btn ghost" onclick="createNewCase()">${icon("plus")} 새 상담</button>
              <button class="btn secondary" onclick="saveCase()">${icon("save")} 현재 상담 저장</button>
              <button class="btn primary" onclick="setView('case')">${icon("arrow-right")} 상담 입력</button>
            </div>
          </div>
          <div class="panel-body">
            <div class="case-summary-grid">
              ${summaryItem("현재 상담", state.case?.title || "신규 상담")}
              ${summaryItem("거주 지역", state.case?.region || "미입력")}
              ${summaryItem("진행 상태", workflowStatus())}
              ${summaryItem("선택 서비스", serviceLabel)}
            </div>
            <div class="case-list-note">
              상담 저장은 상담 메모, 지역, 대상, 선택 욕구, AI 구조화 결과와 패키지 상태를 함께 보관합니다.
              통계성 지표는 실제 운영 데이터가 쌓이기 전까지 표시하지 않습니다.
            </div>
            <div class="pill-row">
              ${needs.length ? needs.map((need) => pill(need, needsColor(need))).join("") : pill("욕구 미선택", "amber")}
            </div>
          </div>
        </section>

        <section class="workspace-panel">
          <div class="panel-head">
            <div>
              <h2 class="panel-title">상담 목록</h2>
              <p class="panel-subtitle">저장한 상담을 불러와 구조화, 검색, 패키지 추천을 이어서 진행합니다.</p>
            </div>
            <button class="btn ghost" onclick="refreshCaseList({ renderAfter: true })">${icon("refresh-cw")} 새로고침</button>
          </div>
          <div class="panel-body">
            ${renderCaseRows()}
          </div>
        </section>
      </div>
    `;
  };

  const nativeSaveCase = typeof saveCase === "function" ? saveCase : null;
  saveCase = async function saveCaseToList() {
    if (isSavingCase) return;
    const memo = String(state.case?.memo || "").trim();
    const title = String(state.case?.title || "").trim();
    if (!memo && !title) {
      showToast("저장할 상담 제목이나 메모를 입력해 주세요.");
      return;
    }

    isSavingCase = true;
    const needs = currentNeeds();
    const record = {
      ...state.case,
      needs,
      issueTypes: Array.isArray(state.case?.issueTypes) ? state.case.issueTypes : needs,
      status: workflowStatus(),
      structured: state.structured || null,
      packages: Array.isArray(state.packages) ? state.packages : [],
      selectedPackageId: state.selectedPackageId || null,
    };

    try {
      const data = await apiFetch("/api/cases", {
        method: "POST",
        body: JSON.stringify({ case: record }),
      });
      if (data.case?.id) {
        state.case.id = data.case.id;
      }
      await refreshCaseList();
      showToast("상담 목록에 저장했습니다.");
      render();
    } catch (error) {
      if (nativeSaveCase) {
        try {
          await nativeSaveCase();
        } catch (_fallbackError) {
          // Keep the user-facing message below.
        }
      }
      showToast("백엔드 저장에 실패했습니다. 서버 연결 상태를 확인해 주세요.");
    } finally {
      isSavingCase = false;
    }
  };

  loadRecentCase = function loadSavedCase(id) {
    const item = recentCases.find((entry) => entry.id === id);
    if (!item) return;
    const needs = needsForRecord(item);
    state.case = {
      ...state.case,
      ...item,
      id: item.id,
      title: item.title || "상담",
      targetType: item.targetType || item.target || state.case.targetType || "",
      region: item.region || "",
      issueTypes: needs,
      urgency: item.urgency || state.case.urgency || "",
      memo: item.memo || "",
    };
    state.structured = item.structured || null;
    state.packages = Array.isArray(item.packages) ? item.packages : [];
    state.selectedPackageId = item.selectedPackageId || state.packages[0]?.id || null;
    state.lastReport = null;
    setView("case");
  };

  deleteSavedCase = async function deleteCaseFromList(id) {
    if (!window.confirm("이 상담을 상담 목록에서 삭제할까요?")) return;
    try {
      const data = await apiFetch(`/api/cases/${encodeURIComponent(id)}`, { method: "DELETE" });
      recentCases = Array.isArray(data.cases) ? data.cases : recentCases.filter((item) => item.id !== id);
      if (state.case?.id === id) {
        state.case.id = "NEW-CASE";
      }
      showToast("상담을 삭제했습니다.");
      render();
    } catch (_error) {
      showToast("상담 삭제에 실패했습니다.");
    }
  };

  const nativeHydrateBackend = typeof hydrateBackend === "function" ? hydrateBackend : null;
  if (nativeHydrateBackend) {
    hydrateBackend = async function hydrateBackendWithCaseList(...args) {
      await nativeHydrateBackend(...args);
      await refreshCaseList();
      if (state.loggedIn) render();
    };
  }

  const nativeCreateNewCase = typeof createNewCase === "function" ? createNewCase : null;
  if (nativeCreateNewCase) {
    createNewCase = function createCleanCase() {
      nativeCreateNewCase();
      state.lastReport = null;
    };
  }

  function postProcessCaseListUi() {
    installCaseListStyles();
    document.title = "복지연계 코파일럿";
    document.querySelectorAll(".case-context-strip").forEach((node) => node.remove());
    window.lucide?.createIcons?.();
  }

  const previousRender = render;
  render = function renderWithCaseList(...args) {
    const result = previousRender.apply(this, args);
    postProcessCaseListUi();
    return result;
  };

  globalThis.refreshCaseList = refreshCaseList;
  globalThis.deleteSavedCase = deleteSavedCase;
  installCaseListStyles();
  postProcessCaseListUi();
  if (state.loggedIn) {
    refreshCaseList({ renderAfter: true });
  } else {
    render();
  }
})();
