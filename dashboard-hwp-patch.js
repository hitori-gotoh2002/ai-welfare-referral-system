(() => {
  if (typeof state === "undefined" || typeof render !== "function") return;
  if (globalThis.__DASHBOARD_HWP_PATCHED) return;
  globalThis.__DASHBOARD_HWP_PATCHED = true;

  const DRAFT_KEY = "welfare-case-draft-v2";
  const COMMON_FORM_URL = "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=14600000275";
  const ALIAS = { 서울특별시:"서울", 서울시:"서울", 서울:"서울", 부산광역시:"부산", 부산시:"부산", 부산:"부산", 대구광역시:"대구", 대구시:"대구", 대구:"대구", 인천광역시:"인천", 인천시:"인천", 인천:"인천", 광주광역시:"광주", 광주시:"광주", 광주:"광주", 대전광역시:"대전", 대전시:"대전", 대전:"대전", 울산광역시:"울산", 울산시:"울산", 울산:"울산", 세종특별자치시:"세종", 세종시:"세종", 세종:"세종", 경기도:"경기", 경기:"경기", 강원특별자치도:"강원", 강원도:"강원", 강원:"강원", 충청북도:"충북", 충북:"충북", 충청남도:"충남", 충남:"충남", 전북특별자치도:"전북", 전라북도:"전북", 전북:"전북", 전라남도:"전남", 전남:"전남", 경상북도:"경북", 경북:"경북", 경상남도:"경남", 경남:"경남", 제주특별자치도:"제주", 제주도:"제주", 제주:"제주" };
  const NATION = new Set(["", "전국", "중앙", "공통", "온라인", "복지로", "정부24"]);
  const LOCAL = new Set(["지자체", "광역", "기초", "시군구"]);

  function addStyles() {
    if (document.querySelector("#dashboard-hwp-patch-style")) return;
    const style = document.createElement("style");
    style.id = "dashboard-hwp-patch-style";
    style.textContent = `.case-table-wrap{overflow-x:auto}.case-dashboard-table{width:100%;border-collapse:separate;border-spacing:0 10px;min-width:860px}.case-dashboard-table th{color:var(--muted);font-size:12px;font-weight:800;padding:0 14px 4px;text-align:left}.case-dashboard-table td{background:#fff;border-bottom:1px solid var(--line);border-top:1px solid var(--line);padding:14px;vertical-align:middle}.case-dashboard-table td:first-child{border-left:1px solid var(--line);border-radius:8px 0 0 8px}.case-dashboard-table td:last-child{border-right:1px solid var(--line);border-radius:0 8px 8px 0}.case-dashboard-table tr.is-current td{background:#eef8f5;border-color:#a8d6cd}.table-actions{display:flex;gap:8px;white-space:nowrap}.btn.compact,.download-link-btn.compact{min-height:34px;padding:0 10px}.icon-btn.danger{color:#9f2f2f}.milestone{display:grid;gap:6px;grid-template-columns:repeat(4,minmax(54px,1fr));min-width:250px}.milestone-step{align-items:center;background:#eef1f3;border:1px solid #d7dde2;border-radius:999px;color:#6b777f;display:inline-flex;font-size:12px;font-weight:800;justify-content:center;min-height:28px;padding:0 8px}.milestone-step.done{background:#dff2ec;border-color:#93cabc;color:#245d55}.step-badge{background:#e8f4ef;border:1px solid #b9dcd2;border-radius:999px;color:#2d655d;display:inline-flex;font-size:12px;font-weight:900;padding:6px 11px}.hwp-guide-card{background:#fff;border:1px solid #cdd8df;border-radius:8px;box-shadow:0 10px 30px rgba(31,48,56,.08);margin-bottom:18px;padding:18px}.hwp-guide-head{border-bottom:2px solid #1f3038;display:flex;justify-content:space-between;gap:16px;margin-bottom:14px;padding-bottom:12px}.hwp-guide-head h3{font-size:18px;margin:8px 0 0}.hwp-guide-table{border-collapse:collapse;width:100%}.hwp-guide-table th,.hwp-guide-table td{border:1px solid #d7dde2;font-size:14px;line-height:1.55;padding:11px 12px;text-align:left;vertical-align:top}.hwp-guide-table th{background:#f2f5f6;color:#1f3038;font-weight:900;width:190px}.hwp-check{display:inline-flex;align-items:center;gap:6px;margin:2px 14px 2px 0}.application-draft-box{background:#f8faf9;border:1px solid #dde6e4;border-radius:8px;margin-top:14px;padding:14px}.application-draft-box p{color:#46535a;line-height:1.7;margin:8px 0 0}.download-link-grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}.download-link-btn{align-items:center;background:#eaf5f0;border:1px solid #b9dcd2;border-radius:8px;color:#245d55;display:inline-flex;font-weight:900;gap:8px;justify-content:center;min-height:44px;padding:0 14px;text-decoration:none}.download-link-btn span{color:#617078;font-size:12px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media(max-width:760px){.hwp-guide-head{display:block}.hwp-guide-table th,.hwp-guide-table td{display:block;width:100%}}@media print{.hwp-guide-card{border:1.5px solid #111;box-shadow:none;break-inside:avoid}.hwp-guide-table th,.hwp-guide-table td,.application-draft-box,.download-link-btn{border-color:#111;color:#111}.download-link-btn{background:#fff}}`;
    document.head.appendChild(style);
  }

  function norm(region) {
    const v = String(region || "").replace(/[()[\]{},]/g, " ").replace(/\s+/g, " ").trim();
    if (!v) return { sido:"", sigungu:"" };
    if (NATION.has(v)) return { sido:"전국", sigungu:"" };
    const t = v.split(" ");
    let sido = ALIAS[t[0]] || "";
    let sigungu = t[1] || "";
    if (!sido) {
      const k = Object.keys(ALIAS).sort((a,b)=>b.length-a.length).find((a)=>v.startsWith(a));
      if (k) { sido = ALIAS[k]; sigungu = v.slice(k.length).trim().split(" ")[0] || ""; }
    }
    if (!sido && t.length === 1) sido = ALIAS[t[0].replace(/(특별시|광역시|특별자치시|특별자치도|자치도|도|시)$/g, "")] || t[0];
    return { sido, sigungu: sigungu.replace(/(특례시|시|군|구)$/g, "") };
  }

  function regionOK(service, caseRegion = state.case.region) {
    const r = String(service?.region || "").trim();
    const s = String(service?.source || "").trim();
    if (NATION.has(r) || s === "중앙") return true;
    if (!caseRegion) return !LOCAL.has(s);
    const a = norm(caseRegion), b = norm(r);
    if (!b.sido || b.sido === "전국") return !LOCAL.has(s);
    if (!a.sido || a.sido !== b.sido) return false;
    return !(a.sigungu && b.sigungu) || a.sigungu.includes(b.sigungu) || b.sigungu.includes(a.sigungu);
  }
  globalThis.is_region_compatible = regionOK;

  try { state.case = { ...state.case, ...(JSON.parse(localStorage.getItem(DRAFT_KEY) || "null") || {}) }; } catch (_e) {}
  state.case.counselor ||= "김현장";
  recentCases = recentCases.map((c, i) => ({ counselor: ["김현장", "이연계", "박사례"][i % 3], ...c }));

  const baseUpdateCase = updateCase;
  updateCase = function(field, value, shouldRender = true) { baseUpdateCase(field, value, shouldRender); try { localStorage.setItem(DRAFT_KEY, JSON.stringify(state.case)); } catch (_e) {} };
  const baseLoadRecentCase = loadRecentCase;
  loadRecentCase = function(id) { const found = recentCases.find((c) => c.id === id); baseLoadRecentCase(id); state.case.counselor = found?.counselor || state.case.counselor || "김현장"; };
  const baseFilteredServices = filteredServices;
  filteredServices = () => baseFilteredServices().filter((service) => regionOK(service, state.case.region));

  function prunePackages() { state.packages = (state.packages || []).map((pkg) => ({ ...pkg, items: (pkg.items || []).filter((item) => { const service = services.find((s) => s.id === item.serviceId); return !service || regionOK(service); }) })); }
  if (typeof generatePackagesLocal === "function") { const base = generatePackagesLocal; generatePackagesLocal = (opt = {}) => { const result = base(opt); prunePackages(); return result; }; }
  if (typeof generatePackages === "function") { const base = generatePackages; generatePackages = async (opt = {}) => { const result = await base(opt); prunePackages(); return result; }; }

  function stage(c) { if (c.current) return state.lastReport ? 4 : state.packages.length ? 3 : state.structured ? 2 : state.case.memo ? 1 : 0; const st = String(c.status || ""); return /추천서|완료/.test(st) ? 4 : /패키지|추천/.test(st) ? 3 : /구조|분석/.test(st) ? 2 : c.memo ? 1 : 0; }
  function rowNeeds(c) { return Array.isArray(c.needs) ? c.needs : Array.isArray(c.issueTypes) ? c.issueTypes : []; }
  function milestone(c) { const n = stage(c); return `<div class="milestone">${["상담", "AI", "패키지", "추천서"].map((x,i)=>`<span class="milestone-step ${i < n ? "done" : ""}">${escapeHtml(x)}</span>`).join("")}</div>`; }
  function rows() { return [{ ...state.case, current:true, status: state.lastReport ? "추천서 생성" : state.packages.length ? "패키지 조정" : state.structured ? "AI 분석" : "상담 입력", needs: state.structured?.needs || state.case.issueTypes || [] }, ...recentCases.filter((c)=>c.id !== state.case.id)].slice(0, 9); }

  renderDashboard = function() {
    return `<div class="grid-3">${renderStat("users", `${rows().length}건`, "추적 중인 상담")}${renderStat("map-pin", state.case.region || "지역 미입력", "현재 거주 지역")}${renderStat("user-check", state.case.counselor || "담당자 미입력", "담당 상담사")}</div>
    <section class="workspace-panel"><div class="panel-head"><div><h2 class="panel-title">통합 상담 대시보드</h2><p class="panel-subtitle">사례명, 담당자, 거주 지역, 진행 단계를 한 화면에서 관리합니다.</p></div><div class="button-row"><button class="btn ghost" onclick="createNewCase()">${icon("plus")} 새 상담</button><button class="btn primary" onclick="setView('case')">${icon("arrow-right")} 현재 상담 이어서</button></div></div><div class="panel-body"><div class="case-table-wrap"><table class="case-dashboard-table"><thead><tr><th>상담 사례명</th><th>담당 상담사</th><th>거주 지역</th><th>욕구</th><th>진행도</th><th>작업</th></tr></thead><tbody>${rows().map((c)=>`<tr class="${c.current ? "is-current" : ""}"><td><strong>${escapeHtml(c.title || "제목 미입력")}</strong><span class="tiny">${escapeHtml(c.id || "NEW-CASE")}</span></td><td>${escapeHtml(c.counselor || "미배정")}</td><td>${escapeHtml(c.region || "미입력")}</td><td><div class="pill-row">${rowNeeds(c).slice(0,4).map((n)=>pill(n, needsColor(n))).join("") || pill("미분류")}</div></td><td>${milestone(c)}</td><td><div class="table-actions"><button class="btn ghost compact" onclick="continueCase('${escapeHtml(c.id || "")}')">${icon("play")} 이어서 진행</button><button class="icon-btn danger" title="삭제" onclick="deleteCase('${escapeHtml(c.id || "")}')">${icon("trash-2")}</button></div></td></tr>`).join("")}</tbody></table></div></div></section>`;
  };
  globalThis.continueCase = (id) => (!id || id === state.case.id) ? setView("case") : loadRecentCase(id);
  globalThis.deleteCase = async (id) => { if (!id) return; recentCases = recentCases.filter((c)=>c.id !== id); if (id === state.case.id) createNewCase(); try { await apiFetch(`/api/cases/${encodeURIComponent(id)}`, { method:"DELETE" }); showToast("상담 사례를 삭제했습니다."); } catch (_e) { showToast("화면에서 삭제했습니다. 서버 삭제는 다시 시도해 주세요."); } render(); };

  function insertCounselor() { if (state.view !== "case" || document.querySelector("#case-counselor")) return; const target = document.querySelector("#case-title")?.closest(".field"); if (!target) return; target.insertAdjacentHTML("afterend", `<div class="field"><label for="case-counselor">담당 상담사</label><input id="case-counselor" value="${escapeHtml(state.case.counselor || "")}" placeholder="예: 김현장" oninput="updateCase('counselor', this.value, false)" /></div>`); }
  function selectedLinks(report) { const selected = typeof selectedPackageServices === "function" ? selectedPackageServices() : []; const links = [...(report?.officialLinks || []), { label:"사회보장급여 신청(변경) 민원 안내", url: COMMON_FORM_URL }, ...selected.map((s)=>({ label:`${s.name} 공고/상세`, url:s.detailUrl || s.url }))]; const seen = new Set(); return links.filter((l)=>/^https?:\/\//i.test(l.url || "") && !seen.has(l.url) && seen.add(l.url)); }
  function localDraft() { const selected = typeof selectedPackageServices === "function" ? selectedPackageServices() : []; const needs = state.structured?.needs || state.case.issueTypes || []; const memo = String(state.case.memo || "").replace(/\s+/g," ").slice(0,180); return `신청인은 ${state.case.region || "거주지 미입력"}에 거주하는 ${state.case.targetType || "대상자"}로, 상담 결과 ${needs.join(", ") || "복지급여"} 관련 지원 필요성이 확인되었습니다. ${memo || "현재 생활 안정과 위기 완화를 위한 공적 지원 연계가 필요합니다."} 이에 ${selected.slice(0,4).map((s)=>s.name).join(", ") || "해당 복지급여"} 제공을 신청하고자 합니다.`; }
  function hwpCard(report) { const guide = report?.hwpGuide || {}; const selected = guide.services || (typeof selectedPackageServices === "function" ? selectedPackageServices().map((s)=>s.name) : []); const draft = report?.applicationDraft || guide.applicationReason || localDraft(); return `<section class="hwp-guide-card"><div class="hwp-guide-head"><div><span class="step-badge">HWP 작성 가이드</span><h3>사회보장급여 제공(변경) 신청서 [별지 제1호서식]</h3></div><span class="muted">제4페이지 신청 사유란에 초안 붙여넣기</span></div><table class="hwp-guide-table"><tbody><tr><th>① 신청인 성명</th><td>${escapeHtml(guide.applicantName || "대상자 또는 대리 신청인 성명 기재")}</td></tr><tr><th>② 주민등록번호</th><td>${escapeHtml(guide.residentNoMasked || "******-*******")}</td></tr><tr><th>③ 거주지 주소</th><td>${escapeHtml(guide.address || state.case.region || "주소 확인 필요")}</td></tr><tr><th>④ 신청 복지급여</th><td>${selected.map((n)=>`<label class="hwp-check"><input type="checkbox" checked disabled /> ${escapeHtml(n)}</label>`).join("") || "선택 서비스 확인 필요"}</td></tr><tr><th>⑤ 대상 가구 구분</th><td>${escapeHtml(guide.householdType || state.case.targetType || "가구 구분 확인 필요")}</td></tr></tbody></table><div class="application-draft-box"><strong>신청 사유 초안</strong><p>${escapeHtml(draft)}</p></div></section>`; }
  function enhanceReport() { if (state.view !== "report") return; const content = document.querySelector(".report-content"); if (!content) return; const report = state.lastReport || {}; if (!content.querySelector(".hwp-guide-card")) content.insertAdjacentHTML("afterbegin", hwpCard(report)); if (!content.querySelector(".official-link-panel")) content.insertAdjacentHTML("beforeend", `<section class="report-block official-link-panel"><h3>공식 공고문/서식 바로가기</h3><div class="download-link-grid">${selectedLinks(report).map((l)=>`<a class="download-link-btn" href="${escapeHtml(l.url)}" target="_blank" rel="noopener noreferrer">${icon("external-link")} 양식/공고 바로가기<span>${escapeHtml(l.label)}</span></a>`).join("")}</div></section>`); document.querySelectorAll(".contact-table td:last-child").forEach((td)=>{ const href = td.querySelector("a")?.href || td.textContent.trim(); if (/^https?:\/\//i.test(href)) td.innerHTML = `<a class="download-link-btn compact" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${icon("external-link")} 양식/공고 바로가기</a>`; }); window.lucide?.createIcons?.(); }
  function patchCopy() { if (copyReport.__hwpCopyPatched) return; copyReport = function() { if (!state.packages.length) generatePackagesLocal({ show:false }); const { pkg, selectedServices, needs } = reportData(); const report = state.lastReport || {}; const lines = [`[추천 패키지] ${pkg.title}`, `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`, `담당 상담사: ${state.case.counselor || "미입력"}`, `욕구: ${needs.join(", ")}`, "", "추천 서비스", ...selectedServices.map((s,i)=>`${i+1}. ${s.name} - ${s.summary}`), "", "HWP 신청서 작성 가이드", "- 신청인 성명: 대상자 또는 대리 신청인 성명", "- 주민등록번호: ******-******* 형식으로 마스킹 확인", `- 거주지 주소: ${state.case.region || "주소 확인 필요"}`, `- 신청 복지급여: ${selectedServices.map((s)=>s.name).join(", ") || "확인 필요"}`, `- 대상 가구 구분: ${state.case.targetType || "확인 필요"}`, "- 제4페이지 [신청 사유] 란: 아래 초안 붙여넣기", "", "신청 사유 초안", report.applicationDraft || localDraft(), "", "서비스별 딥링크", ...selectedLinks(report).map((l)=>`- ${l.label}: ${l.url}`)]; navigator.clipboard?.writeText(lines.join("\n")).then(()=>showToast("추천서, HWP 작성 가이드, 공식 링크를 함께 복사했습니다.")).catch(()=>showToast("복사 권한을 확인해 주세요.")); }; copyReport.__hwpCopyPatched = true; }

  const baseRender = render;
  render = function() { const result = baseRender(); addStyles(); insertCounselor(); enhanceReport(); patchCopy(); return result; };
  window.addEventListener("load", () => { patchCopy(); render(); }, { once:true });
  addStyles(); render();
})();
