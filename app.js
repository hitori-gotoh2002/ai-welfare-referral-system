const NEEDS = ["주거", "생계", "심리", "취업", "의료", "돌봄", "안전", "교육"];

const sampleMemo =
  "청년 1인가구. 최근 근로시간 감소로 소득이 줄었고 월세 2개월 체납 우려가 있음. 식비 부담이 크며 우울감과 수면 문제가 있어 상담 연계를 희망함. 구직도 함께 알아보고 싶다고 함.";

const keywordMap = {
  주거: ["월세", "임대료", "체납", "퇴거", "주거", "거처", "보증금"],
  생계: ["소득", "생활비", "식비", "생계", "실직", "근로시간", "긴급지원"],
  심리: ["우울", "불안", "수면", "자살", "정신", "상담", "고립"],
  취업: ["구직", "취업", "일자리", "직업", "훈련", "근로"],
  의료: ["치료비", "의료비", "병원", "진료", "약값", "간병"],
  돌봄: ["돌봄", "양육", "보호자", "아동", "청소년", "노인"],
  안전: ["폭력", "학대", "자해", "자살", "위험", "가출"],
  교육: ["학교", "학습", "장학", "검정고시", "교육"],
};

let services = [
  {
    id: "svc-1",
    name: "긴급복지 생계지원",
    source: "중앙",
    region: "전국",
    target: "저소득",
    domains: ["생계", "주거"],
    urgency: "긴급",
    summary: "갑작스러운 위기 상황으로 생계 유지가 어려운 가구에 생계비와 주거비 등을 신속 지원합니다.",
    eligibility: "소득·재산 기준, 위기사유, 금융재산 기준 확인 필요",
    support: "생계비, 의료비, 주거지원, 사회복지시설 이용 지원",
    process: "읍면동 상담 → 위기사유 확인 → 현장 확인 → 지원 결정",
    docs: ["신분증", "소득 감소 증빙", "임대차계약서", "통장 사본"],
    contact: "보건복지상담센터 129 / 관할 읍면동",
    url: "https://www.bokjiro.go.kr",
    updated: "2026 기준",
    group: "emergency-basic",
  },
  {
    id: "svc-2",
    name: "서울형 긴급복지",
    source: "지자체",
    region: "서울",
    target: "저소득",
    domains: ["생계", "주거"],
    urgency: "긴급",
    summary: "서울 거주 위기가구에 생계비, 주거비, 의료비를 보완 지원합니다.",
    eligibility: "서울 거주, 위기사유, 소득·재산 기준 확인",
    support: "생계비, 주거비, 의료비, 교육비 일부",
    process: "동주민센터 접수 → 구청 심의 → 지급",
    docs: ["주민등록등본", "위기사유 증빙", "임대료 체납 내역"],
    contact: "다산콜센터 120 / 관할 동주민센터",
    url: "https://wis.seoul.go.kr",
    updated: "2026 기준",
    group: "emergency-basic",
  },
  {
    id: "svc-3",
    name: "주거취약계층 주거상향 지원",
    source: "중앙",
    region: "전국",
    target: "주거취약",
    domains: ["주거"],
    urgency: "일반",
    summary: "고시원·쪽방·반지하 등 주거취약 상태의 가구가 공공임대주택으로 이전할 수 있도록 지원합니다.",
    eligibility: "주거취약 형태, 소득·자산 기준, 무주택 여부",
    support: "공공임대 연계, 이주비·보증금 상담, 정착 지원",
    process: "주거복지센터 상담 → 자격 확인 → LH/SH 신청 → 입주 지원",
    docs: ["임대차계약서", "주거환경 확인 자료", "소득 증빙"],
    contact: "마이홈 1600-1004 / 지역 주거복지센터",
    url: "https://www.myhome.go.kr",
    updated: "2026 기준",
    group: "housing-upgrade",
  },
  {
    id: "svc-4",
    name: "청년월세 한시 특별지원",
    source: "중앙",
    region: "전국",
    target: "청년",
    domains: ["주거", "생계"],
    urgency: "일반",
    summary: "부모와 별도 거주하는 무주택 청년에게 월세 일부를 한시 지원합니다.",
    eligibility: "연령, 거주, 소득·재산, 임차료 기준 확인",
    support: "월세 일부를 일정 기간 지원",
    process: "복지로 또는 주민센터 신청 → 소득·재산 조사 → 지급",
    docs: ["임대차계약서", "월세 이체 증빙", "가족관계증명서"],
    contact: "복지로 / 관할 주민센터",
    url: "https://www.bokjiro.go.kr",
    updated: "2026 기준",
    group: "youth-rent",
  },
  {
    id: "svc-5",
    name: "청년 마음건강 지원사업",
    source: "중앙",
    region: "전국",
    target: "청년",
    domains: ["심리"],
    urgency: "일반",
    summary: "심리·정서적 어려움이 있는 청년에게 전문 심리상담 서비스를 제공합니다.",
    eligibility: "연령 기준, 지역별 모집 여부, 우선순위 대상 확인",
    support: "전문 심리상담 바우처, 사전·사후 검사",
    process: "주민센터 신청 → 대상자 선정 → 제공기관 선택 → 상담 진행",
    docs: ["신분증", "신청서", "우선순위 증빙"],
    contact: "관할 읍면동 / 지역사회서비스지원단",
    url: "https://www.socialservice.or.kr",
    updated: "2026 기준",
    group: "mental-youth",
  },
  {
    id: "svc-6",
    name: "정신건강복지센터 상담 연계",
    source: "기관",
    region: "서울",
    target: "전국민",
    domains: ["심리", "안전"],
    urgency: "긴급",
    summary: "우울, 불안, 자살위험 등 정신건강 어려움에 대해 지역 센터 상담과 위기 개입을 연결합니다.",
    eligibility: "지역 거주 또는 생활권, 위기 수준 확인",
    support: "초기 상담, 사례관리, 치료 연계, 응급 개입",
    process: "센터 전화 → 초기 평가 → 상담 일정 배정 → 필요 시 의료기관 연계",
    docs: ["상담 의뢰서", "보호자 연락처", "위험 신호 기록"],
    contact: "정신건강위기상담 1577-0199 / 지역 정신건강복지센터",
    url: "https://www.mentalhealth.go.kr",
    updated: "2026 기준",
    group: "mental-youth",
  },
  {
    id: "svc-7",
    name: "국민취업지원제도",
    source: "중앙",
    region: "전국",
    target: "구직자",
    domains: ["취업", "생계"],
    urgency: "일반",
    summary: "취업 취약계층에게 취업지원서비스와 구직촉진수당 또는 취업활동비용을 지원합니다.",
    eligibility: "연령, 소득·재산, 취업경험, 구직 의사 확인",
    support: "취업상담, 직업훈련, 일경험, 수당",
    process: "고용24 신청 → 자격 심사 → 취업활동계획 수립 → 서비스 참여",
    docs: ["신분증", "소득 관련 자료", "구직 신청 정보"],
    contact: "고용노동부 1350 / 고용복지플러스센터",
    url: "https://www.work24.go.kr",
    updated: "2026 기준",
    group: "employment",
  },
  {
    id: "svc-8",
    name: "지역 푸드마켓·푸드뱅크",
    source: "민간",
    region: "서울",
    target: "저소득",
    domains: ["생계"],
    urgency: "긴급",
    summary: "식료품과 생필품 지원이 필요한 가구에 지역 나눔 자원을 연계합니다.",
    eligibility: "기초생활수급, 차상위, 긴급 위기가구 등 지역 기준",
    support: "식료품, 생필품, 정기·긴급 물품 지원",
    process: "동주민센터 또는 복지관 추천 → 이용 등록 → 물품 수령",
    docs: ["추천서", "신분 확인 자료", "위기상황 기록"],
    contact: "지역 사회복지관 / 푸드뱅크",
    url: "https://www.foodbank1377.org",
    updated: "2026 기준",
    group: "food",
  },
  {
    id: "svc-9",
    name: "의료비 긴급지원",
    source: "중앙",
    region: "전국",
    target: "저소득",
    domains: ["의료", "생계"],
    urgency: "긴급",
    summary: "중대한 질병 또는 부상으로 의료비 부담이 큰 위기가구에 의료비를 지원합니다.",
    eligibility: "위기사유, 의료 필요성, 소득·재산 기준",
    support: "검사·치료비, 입원비 일부",
    process: "병원 사회사업팀 상담 → 주민센터 또는 시군구 신청 → 지원 결정",
    docs: ["진단서", "진료비 내역서", "소득 증빙"],
    contact: "보건복지상담센터 129 / 병원 사회사업팀",
    url: "https://www.bokjiro.go.kr",
    updated: "2026 기준",
    group: "medical",
  },
  {
    id: "svc-10",
    name: "위기청소년 통합지원",
    source: "기관",
    region: "전국",
    target: "청소년",
    domains: ["돌봄", "교육", "안전", "심리"],
    urgency: "긴급",
    summary: "위기 청소년에게 상담, 보호, 교육, 자립 서비스를 통합 연계합니다.",
    eligibility: "청소년 위기상황, 보호 필요성, 학교·가정 상황 확인",
    support: "상담, 긴급보호, 학업 복귀, 자립 지원",
    process: "청소년상담복지센터 의뢰 → 위기 평가 → 통합지원회의 → 서비스 연계",
    docs: ["상담기록", "보호자 동의", "학교 협조 자료"],
    contact: "청소년상담 1388 / 지역 청소년상담복지센터",
    url: "https://www.kyci.or.kr",
    updated: "2026 기준",
    group: "youth-crisis",
  },
];

let recentCases = [
  {
    id: "case-20260522-01",
    title: "청년 1인가구 월세 체납 우려",
    region: "서울 관악구",
    status: "추천서 생성",
    needs: ["주거", "생계", "심리", "취업"],
    memo: sampleMemo,
  },
  {
    id: "case-20260521-03",
    title: "치료비 부담 환자 보호자 상담",
    region: "경기 성남시",
    status: "패키지 조정",
    needs: ["의료", "생계"],
    memo: "입원 치료비 부담이 크고 보호자 소득이 일정하지 않음. 의료비와 생계 지원을 함께 확인하고 싶음.",
  },
  {
    id: "case-20260520-02",
    title: "위기 청소년 보호체계 연계",
    region: "서울 은평구",
    status: "구조화 완료",
    needs: ["돌봄", "심리", "안전", "교육"],
    memo: "가정 내 갈등과 등교 거부가 지속됨. 상담과 보호, 학습 지원이 필요함.",
  },
];

const state = {
  loggedIn: false,
  view: "dashboard",
  mobileNav: false,
  toast: "",
  apiStatus: "checking",
  apiMessage: "백엔드 연결 확인 중",
  llmEnabled: false,
  viewToken: 0,
  reportLoading: false,
  lastReport: null,
  providers: [],
  providerMeta: null,
  providerLoading: false,
  modalLoading: false,
  modalServiceId: null,
  selectedServiceId: "svc-1",
  case: {
    id: "NEW-CASE",
    title: "신규 상담",
    targetType: "청년",
    region: "서울 관악구",
    issueTypes: ["주거", "생계", "심리"],
    urgency: "긴급",
    memo: sampleMemo,
  },
  structured: null,
  filters: {
    q: "",
    source: "전체",
    domain: "전체",
    urgency: "전체",
  },
  packages: [],
  selectedPackageId: null,
};

const views = [
  ["dashboard", "대시보드", "layout-dashboard"],
  ["case", "상담 입력", "clipboard-pen"],
  ["search", "통합 검색", "search"],
  ["packages", "패키지 추천", "boxes"],
  ["report", "추천서", "file-text"],
  ["settings", "도움말/설정", "settings"],
];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function icon(name, className = "icon") {
  return `<i data-lucide="${name}" class="${className}"></i>`;
}

const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:5173" : window.location.origin;

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}`);
  }
  return response.json();
}

async function hydrateBackend() {
  try {
    const [health, serviceData, caseData] = await Promise.all([
      apiFetch("/api/health"),
      apiFetch("/api/services"),
      apiFetch("/api/cases/recent"),
    ]);
    services = serviceData.services || services;
    recentCases = caseData.cases || recentCases;
    state.apiStatus = health.ok ? "online" : "offline";
    state.llmEnabled = !!health.llm?.enabled;
    const llmSuffix = state.llmEnabled ? "+LLM" : "";
    state.apiMessage = serviceData.meta?.fallback
      ? `백엔드 연결됨${llmSuffix} · 공공데이터 폴백`
      : `백엔드+공공데이터${llmSuffix} 연결됨`;
    render();
  } catch (error) {
    state.apiStatus = "offline";
    state.apiMessage = "백엔드 미연결 · 로컬 샘플로 동작";
    render();
  }
}

function needsColor(need) {
  const map = {
    주거: "blue",
    생계: "green",
    심리: "violet",
    취업: "amber",
    의료: "red",
    돌봄: "green",
    안전: "red",
    교육: "blue",
  };
  return map[need] || "";
}

function pill(label, className = "") {
  return `<span class="pill ${className}">${escapeHtml(label)}</span>`;
}

function caseNeeds(item) {
  return Array.isArray(item?.needs) ? item.needs : Array.isArray(item?.issueTypes) ? item.issueTypes : [];
}

function showToast(message) {
  state.toast = message;
  render();
  window.setTimeout(() => {
    state.toast = "";
    render();
  }, 1900);
}

function setView(view) {
  const token = state.viewToken + 1;
  state.viewToken = token;
  state.view = view;
  state.mobileNav = false;
  if ((view === "packages" || view === "report") && !state.packages.length) {
    generatePackagesLocal({ show: false });
  }
  render();
  if (view === "packages" || view === "report") {
    refreshProvidersFromBackend(token).then(() => {
      if (state.view === "report" && state.viewToken === token) refreshReportFromBackend(token);
    });
  }
  if (view === "search") {
    refreshServicesFromBackend(token);
  }
}

function updateCase(field, value, shouldRender = true) {
  state.case[field] = value;
  state.lastReport = null;
  if (field === "memo") {
    const counter = document.querySelector("#memo-count");
    if (counter) counter.textContent = `${value.length}자`;
  }
  if (shouldRender) render();
}

function toggleIssue(issue) {
  const exists = state.case.issueTypes.includes(issue);
  state.case.issueTypes = exists
    ? state.case.issueTypes.filter((item) => item !== issue)
    : [...state.case.issueTypes, issue];
  render();
}

function inferStructureLocal({ show = true } = {}) {
  const memo = `${state.case.memo} ${state.case.issueTypes.join(" ")}`.toLowerCase();
  const detected = new Set(state.case.issueTypes);
  const keywords = [];

  Object.entries(keywordMap).forEach(([need, words]) => {
    const matched = words.filter((word) => memo.includes(word.toLowerCase()));
    if (matched.length) {
      detected.add(need);
      keywords.push(...matched.slice(0, 3));
    }
  });

  const urgentSignals = [];
  if (/체납|퇴거|식비|긴급|소득|실직/.test(memo)) {
    urgentSignals.push({
      label: "경제·주거 위기",
      text: "체납, 식비 부담, 소득 감소 표현이 있어 긴급복지와 주거비 지원을 먼저 확인합니다.",
    });
  }
  if (/자살|자해|폭력|학대|위험/.test(memo)) {
    urgentSignals.push({
      label: "즉시 안전 확인",
      text: "위험 신호가 포함되어 보호자·응급기관·위기상담 연결 여부를 확인합니다.",
    });
  }
  if (/우울|불안|수면|고립/.test(memo)) {
    urgentSignals.push({
      label: "정신건강 확인",
      text: "우울감 또는 수면 문제 표현이 있어 정신건강복지센터와 상담 바우처를 함께 검토합니다.",
    });
  }

  state.structured = {
    needs: Array.from(detected),
    keywords: Array.from(new Set(keywords)).slice(0, 10),
    urgency: urgentSignals.length || state.case.urgency === "긴급" ? "긴급" : state.case.urgency,
    target: state.case.targetType,
    region: state.case.region,
    riskChecks: urgentSignals.length
      ? urgentSignals
      : [{ label: "일반 확인", text: "소득·재산·거주지·연령 기준을 상담 중 확인합니다." }],
  };
  state.packages = [];
  state.selectedPackageId = null;
  state.lastReport = null;
  if (show) showToast("상담 메모를 구조화했습니다.");
  return state.structured;
}

async function inferStructure({ goTo } = {}) {
  try {
    const data = await apiFetch("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ case: state.case }),
    });
    state.structured = data.structured;
    state.packages = [];
    state.selectedPackageId = null;
    state.lastReport = null;
    showToast("백엔드에서 상담 메모를 구조화했습니다.");
  } catch (error) {
    inferStructureLocal({ show: true });
  }
  if (goTo) {
    setView(goTo);
  } else {
    render();
  }
}

function toggleStructuredNeed(need) {
  if (!state.structured) inferStructureLocal({ show: false });
  const exists = state.structured.needs.includes(need);
  state.structured.needs = exists
    ? state.structured.needs.filter((item) => item !== need)
    : [...state.structured.needs, need];
  state.packages = [];
  state.lastReport = null;
  render();
}

function loadRecentCase(id) {
  const recent = recentCases.find((item) => item.id === id);
  if (!recent) return;
  const needs = caseNeeds(recent);
  state.case = {
    id: recent.id,
    title: recent.title,
    targetType: needs.includes("교육") ? "청소년" : needs.includes("의료") ? "의료취약" : recent.targetType || "청년",
    region: recent.region,
    issueTypes: needs,
    urgency: recent.urgency || (needs.includes("안전") || needs.includes("의료") ? "긴급" : "주의"),
    memo: recent.memo,
  };
  state.structured = null;
  state.packages = [];
  setView("case");
}

function createNewCase() {
  state.case = {
    id: "NEW-CASE",
    title: "신규 상담",
    targetType: "청년",
    region: "",
    issueTypes: [],
    urgency: "주의",
    memo: "",
  };
  state.structured = null;
  state.packages = [];
  setView("case");
}

async function saveCase() {
  try {
    const data = await apiFetch("/api/cases", {
      method: "POST",
      body: JSON.stringify({ case: state.case }),
    });
    state.case.id = data.case?.id || state.case.id;
    await hydrateBackend();
    showToast("백엔드에 사례를 임시저장했습니다.");
  } catch (error) {
    showToast("사례가 로컬에서 임시저장되었습니다.");
  }
}

function useTemplate(type) {
  const templates = {
    주거: "현재 거주 형태, 임대료 체납 여부, 퇴거 위험, 보증금·월세 수준, 동거가구 여부를 확인함.",
    생계: "최근 소득 변화, 식비·공과금 부담, 기존 수급 여부, 긴급 지출 항목을 확인함.",
    심리: "우울감, 불안, 수면, 자살사고 여부, 기존 상담·치료 경험, 보호자 지지체계를 확인함.",
    의료: "진단명, 치료 일정, 진료비 내역, 보험 상태, 보호자 부담 가능성을 확인함.",
    돌봄: "돌봄 공백, 보호자 상황, 안전 위험, 학교·기관 협조 가능성을 확인함.",
  };
  const next = `${state.case.memo ? `${state.case.memo}\n` : ""}${templates[type] || ""}`;
  state.case.memo = next.trim();
  if (!state.case.issueTypes.includes(type)) state.case.issueTypes.push(type);
  render();
}

function filteredServices() {
  const q = state.filters.q.trim().toLowerCase();
  const structuredNeeds = state.structured?.needs || state.case.issueTypes;
  return services
    .filter((service) => {
      const qMatch =
        !q ||
        [service.name, service.summary, service.target, service.region, service.source, ...(service.domains || [])]
          .join(" ")
          .toLowerCase()
          .includes(q);
      const sourceMatch = state.filters.source === "전체" || service.source === state.filters.source;
      const domainMatch = state.filters.domain === "전체" || service.domains.includes(state.filters.domain);
      const urgencyMatch = state.filters.urgency === "전체" || service.urgency === state.filters.urgency;
      return qMatch && sourceMatch && domainMatch && urgencyMatch;
    })
    .sort((a, b) => serviceScore(b, structuredNeeds) - serviceScore(a, structuredNeeds));
}

const ageTargetPatterns = {
  아동: /아동|영유아|유아|어린이|초등학생|초등|미취학/,
  청소년: /청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원/,
  청년: /청년|대학생|사회초년생/,
  노인: /노인|어르신|고령|독거노인|기초연금|장기요양/,
};

function ageGroupsFromText(text) {
  const value = String(text || "");
  const groups = new Set();

  Object.entries(ageTargetPatterns).forEach(([group, pattern]) => {
    if (pattern.test(value)) groups.add(group);
  });

  [...value.matchAll(/(?<!\d)(\d{1,3})\s*세/g)].forEach((match) => {
    const age = Number(match[1]);
    if (!Number.isFinite(age)) return;
    if (age >= 65) groups.add("노인");
    else if (age >= 19) groups.add("청년");
    else if (age >= 13) groups.add("청소년");
    else groups.add("아동");
  });

  return groups;
}

function currentCaseAgeGroups() {
  const caseTextGroups = ageGroupsFromText([state.case.title, state.case.memo].filter(Boolean).join(" "));
  if (caseTextGroups.size) return caseTextGroups;

  const structuredGroups = ageGroupsFromText(state.structured?.target || "");
  if (structuredGroups.size) return structuredGroups;

  return ageGroupsFromText(state.case.targetType || "");
}

function serviceAgeGroups(service) {
  return ageGroupsFromText(
    [service.name, service.target, service.summary, service.eligibility, service.support, service.process].filter(Boolean).join(" ")
  );
}

function serviceMatchesCaseTarget(service) {
  const caseGroups = currentCaseAgeGroups();
  const targetGroups = serviceAgeGroups(service);
  if (!caseGroups.size || !targetGroups.size) return true;
  return [...caseGroups].some((group) => targetGroups.has(group));
}

function serviceScore(service, needs) {
  if (!serviceMatchesCaseTarget(service)) return 0;

  const overlap = service.domains.filter((domain) => needs.includes(domain)).length;
  const urgent = service.urgency === "긴급" ? 1 : 0;
  const region = state.case.region && (service.region === "전국" || (service.region && state.case.region.includes(service.region))) ? 1 : 0;
  const targetMatch = [...currentCaseAgeGroups()].some((group) => serviceAgeGroups(service).has(group)) ? 1 : 0;
  return overlap * 4 + urgent * 2 + region + targetMatch;
}

function generatePackagesLocal({ show = true } = {}) {
  if (!state.structured) inferStructureLocal({ show: false });
  const needs = state.structured.needs.length ? state.structured.needs : ["생계", "주거"];
  const ranked = services
    .map((service) => ({ service, score: serviceScore(service, needs) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((item) => item.service);

  const urgentFirst = ranked.filter((service) => service.urgency === "긴급");
  const general = ranked.filter((service) => service.urgency !== "긴급");
  const mixed = uniqueServices([...urgentFirst, ...general]);

  const topA = ensureCoverage(mixed.slice(0, 4), needs);
  const topB = ensureCoverage(
    uniqueServices([
      ...ranked.filter((service) => service.domains.includes("취업") || service.domains.includes("심리")),
      ...ranked,
    ]).slice(0, 4),
    needs
  );
  const topC = ensureCoverage(
    uniqueServices([
      ...ranked.filter((service) => service.source === "기관" || service.source === "민간"),
      ...ranked,
    ]).slice(0, 4),
    needs
  );

  state.packages = [
    buildPackage("pkg-1", "긴급 안정 패키지", "체납·생계·심리 위험을 먼저 낮추는 조합", topA, 94),
    buildPackage("pkg-2", "회복·자립 패키지", "단기 지원 이후 취업과 마음건강을 함께 연결", topB, 88),
    buildPackage("pkg-3", "지역기관 연계 패키지", "공공 제도와 민간·지역기관 접점을 병합", topC, 83),
  ];
  state.selectedPackageId = state.packages[0]?.id || null;
  state.lastReport = null;
  if (show) showToast("상위 패키지 3개를 생성했습니다.");
  return state.packages;
}

async function generatePackages({ goTo } = {}) {
  if (!state.structured) inferStructureLocal({ show: false });
  try {
    const data = await apiFetch("/api/packages", {
      method: "POST",
      body: JSON.stringify({ case: state.case, structured: state.structured, services }),
    });
    state.packages = data.packages || [];
    state.selectedPackageId = state.packages[0]?.id || null;
    state.lastReport = null;
    showToast("백엔드에서 상위 패키지 3개를 생성했습니다.");
  } catch (error) {
    generatePackagesLocal({ show: true });
  }
  if (goTo) {
    setView(goTo);
  } else {
    render();
  }
}

function uniqueServices(items) {
  const seen = new Set();
  return items.filter((item) => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });
}

function ensureCoverage(items, needs) {
  const selected = [...items];
  const domains = new Set(selected.flatMap((item) => item.domains));
  needs.slice(0, 4).forEach((need) => {
    if (!domains.has(need)) {
      const found = services.find(
        (service) => serviceMatchesCaseTarget(service) && service.domains.includes(need) && !selected.some((item) => item.id === service.id)
      );
      if (found) selected.push(found);
    }
  });
  if (new Set(selected.flatMap((item) => item.domains)).size < 2) {
    const add = services.find((service) => serviceMatchesCaseTarget(service) && !selected.some((item) => item.id === service.id));
    if (add) selected.push(add);
  }
  return selected.slice(0, 5);
}

function buildPackage(id, title, summary, items, score) {
  return {
    id,
    title,
    summary,
    score,
    items: items.map((service) => ({ serviceId: service.id, included: true })),
  };
}

function selectedPackage() {
  if (!state.packages.length) generatePackagesLocal({ show: false });
  return state.packages.find((item) => item.id === state.selectedPackageId) || state.packages[0];
}

function setSelectedPackage(id) {
  state.selectedPackageId = id;
  state.lastReport = null;
  render();
}

function togglePackageItem(serviceId) {
  const pkg = selectedPackage();
  const item = pkg.items.find((entry) => entry.serviceId === serviceId);
  if (item) item.included = !item.included;
  state.lastReport = null;
  render();
}

function movePackageItem(serviceId, direction) {
  const pkg = selectedPackage();
  const index = pkg.items.findIndex((entry) => entry.serviceId === serviceId);
  const next = index + direction;
  if (index < 0 || next < 0 || next >= pkg.items.length) return;
  [pkg.items[index], pkg.items[next]] = [pkg.items[next], pkg.items[index]];
  state.lastReport = null;
  render();
}

function addServiceToPackage(serviceId) {
  const pkg = selectedPackage();
  if (!pkg.items.some((item) => item.serviceId === serviceId)) {
    pkg.items.push({ serviceId, included: true });
    state.lastReport = null;
    showToast("패키지에 서비스를 추가했습니다.");
  } else {
    showToast("이미 패키지에 포함된 서비스입니다.");
  }
}

async function openServiceDetail(serviceId) {
  state.modalServiceId = serviceId;
  state.modalLoading = true;
  render();
  try {
    const params = new URLSearchParams({
      q: state.filters.q,
      source: state.filters.source,
      domain: state.filters.domain,
      urgency: state.filters.urgency,
      needs: (state.structured?.needs || state.case.issueTypes).join(","),
      region: state.case.region || "",
      target: state.structured?.target || state.case.targetType || "",
    });
    const data = await apiFetch(`/api/services/${encodeURIComponent(serviceId)}?${params.toString()}`);
    if (data.service) {
      const index = services.findIndex((service) => service.id === serviceId);
      if (index >= 0) {
        services[index] = data.service;
      } else {
        services.push(data.service);
      }
    }
  } catch (error) {
    showToast("상세조회 API 응답을 불러오지 못했습니다.");
  } finally {
    state.modalLoading = false;
    render();
  }
}

function selectedPackageServices() {
  const pkg = selectedPackage();
  return pkg.items
    .filter((item) => item.included)
    .map((item) => services.find((service) => service.id === item.serviceId))
    .filter(Boolean);
}

function reportData() {
  const pkg = selectedPackage();
  const selectedServices = selectedPackageServices();
  const needs = state.structured?.needs || state.case.issueTypes;
  const contacts = Array.from(
    new Map(selectedServices.map((service) => [service.contact, service])).values()
  );
  return { pkg, selectedServices, needs, contacts };
}

async function refreshReportFromBackend(token = state.viewToken) {
  if (state.reportLoading) return;
  state.reportLoading = true;
  try {
    const data = await apiFetch("/api/report", {
      method: "POST",
      body: JSON.stringify({ case: state.case, structured: state.structured, package: selectedPackage(), services, providers: state.providers }),
    });
    if (token !== state.viewToken) return;
    state.lastReport = data.report;
  } catch (error) {
    if (token !== state.viewToken) return;
    state.lastReport = null;
  } finally {
    state.reportLoading = false;
    if (state.view === "report" && token === state.viewToken) render();
  }
}

async function refreshProvidersFromBackend(token = state.viewToken) {
  if (state.providerLoading) return;
  state.providerLoading = true;
  try {
    const params = new URLSearchParams({
      q: state.filters.q,
      domain: state.filters.domain,
      needs: (state.structured?.needs || state.case.issueTypes).join(","),
      region: state.case.region || "",
      numOfRows: "30",
    });
    const data = await apiFetch(`/api/providers?${params.toString()}`);
    if (token !== state.viewToken) return;
    state.providers = data.providers || [];
    state.providerMeta = data.meta || null;
  } catch (error) {
    if (token !== state.viewToken) return;
    state.providers = [];
    state.providerMeta = { fallback: true };
  } finally {
    state.providerLoading = false;
    if (["packages", "report"].includes(state.view) && token === state.viewToken) render();
  }
}

function copyReport() {
  const { pkg, selectedServices, needs } = reportData();
  const report = state.lastReport;
  const servicePlans = report?.servicePlans || selectedServices.map((service) => ({
    service: service.name,
    priority: service.urgency === "긴급" ? "높음" : "중간",
    purpose: service.domains.join(", "),
    whyRecommended: service.summary,
    eligibilityToCheck: [service.eligibility],
    applicationPath: [service.process],
    requiredDocs: service.docs,
    contactAction: service.contact,
    cautions: ["최신 기준과 관할 기관 심사 결과 확인 필요"],
  }));
  const actionPlan = report?.actionPlan || [
    { timing: "오늘", tasks: ["위험 수준과 1순위 서비스 문의처를 확인합니다."] },
    { timing: "3일 이내", tasks: ["공통 증빙자료와 서비스별 신청 경로를 정리합니다."] },
    { timing: "1~2주", tasks: ["접수 결과와 보완서류를 점검하고 대체 자원을 확인합니다."] },
  ];
  const lines = report
    ? [
        `[추천 패키지] ${report.packageTitle}`,
        `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`,
        `핵심 욕구: ${(report.needs || []).join(", ")}`,
        "",
        "사례 요약",
        report.caseSummary || report.reason,
        "",
        "추천 서비스",
        ...servicePlans.map((plan, index) => `${index + 1}. ${plan.service} [${plan.priority}] ${plan.purpose} - ${plan.whyRecommended}`),
        "",
        "서비스별 확인 조건",
        ...servicePlans.flatMap((plan) => [`- ${plan.service}`, ...(plan.eligibilityToCheck || []).map((item) => `  · ${item}`)]),
        "",
        "준비 서류",
        ...report.docs.map((doc) => `- ${doc}`),
        "",
        "단계별 실행계획",
        ...actionPlan.flatMap((phase) => [`- ${phase.timing}`, ...(phase.tasks || []).map((task) => `  · ${task}`)]),
        "",
        "추가 확인 질문",
        ...(report.followUpQuestions || []).map((question) => `- ${question}`),
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
    "",
    "확인 조건",
    ...selectedServices.map((service) => `- ${service.name}: ${service.eligibility}`),
    "",
    "준비 서류",
    ...Array.from(new Set(selectedServices.flatMap((service) => service.docs))).map((doc) => `- ${doc}`),
    "",
    "연결 순서",
    ...selectedServices.map((service, index) => `${index + 1}. ${service.process}`),
  ];

  navigator.clipboard
    ?.writeText(lines.join("\n"))
    .then(() => showToast("추천서 텍스트를 복사했습니다."))
    .catch(() => showToast("복사 권한을 확인해 주세요."));
}

function reportArray(value) {
  return Array.isArray(value) ? value : [];
}

function renderReportBullets(items) {
  const list = reportArray(items).filter(Boolean);
  if (!list.length) return `<div class="empty-state compact">표시할 항목이 없습니다.</div>`;
  return `<ul>${list.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderPriorityAssessment(items) {
  const list = reportArray(items);
  return `
    <div class="report-card-grid">
      ${
        list.length
          ? list
              .map(
                (item) => `
                  <div class="report-mini-card">
                    <strong>${escapeHtml(item.level || "확인")}</strong>
                    <span>${escapeHtml(item.text || "")}</span>
                  </div>
                `
              )
              .join("")
          : `<div class="report-mini-card"><strong>확인</strong><span>소득·재산·거주지·연령 기준 확인 후 판단합니다.</span></div>`
      }
    </div>
  `;
}

function renderServicePlans(plans, fallbackServices) {
  const list = reportArray(plans).length
    ? reportArray(plans)
    : fallbackServices.map((service) => ({
        service: service.name,
        priority: service.urgency === "긴급" ? "높음" : "중간",
        purpose: service.domains.join(", "),
        whyRecommended: service.summary,
        eligibilityToCheck: [service.eligibility],
        applicationPath: [service.process],
        requiredDocs: service.docs,
        contactAction: service.contact,
        cautions: ["최신 기준과 관할 기관 심사 결과 확인 필요"],
      }));
  return `
    <div class="service-plan-list">
      ${list
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
                  ${renderReportBullets(plan.eligibilityToCheck)}
                </div>
                <div>
                  <h4>신청·문의 경로</h4>
                  ${renderReportBullets(plan.applicationPath)}
                </div>
                <div>
                  <h4>준비 서류</h4>
                  ${renderReportBullets(plan.requiredDocs)}
                </div>
                <div>
                  <h4>문의 액션</h4>
                  <p>${escapeHtml(plan.contactAction || "관할 기관 확인")}</p>
                </div>
              </div>
              ${reportArray(plan.cautions).length ? `<div class="tiny">${escapeHtml(plan.cautions.join(" / "))}</div>` : ""}
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderActionPlan(plan) {
  return `
    <div class="timeline-list">
      ${reportArray(plan)
        .map(
          (phase) => `
            <div class="timeline-card">
              <strong>${escapeHtml(phase.timing || "확인")}</strong>
              ${renderReportBullets(phase.tasks)}
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderChecklist(checklist) {
  return `
    <div class="report-card-grid">
      ${reportArray(checklist)
        .map(
          (group) => `
            <div class="report-mini-card">
              <strong>${escapeHtml(group.title || "확인")}</strong>
              ${renderReportBullets(group.items)}
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderProviderPlan(plan) {
  const list = reportArray(plan);
  if (!list.length) return "";
  return `
    <section class="report-block">
      <h3>민간·지역기관 연계 계획</h3>
      <div class="source-stack">
        ${list
          .map(
            (item) => `
              <div class="source-row">
                <div>
                  <strong>${escapeHtml(item.name || "기관")}</strong>
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

let serviceRefreshTimer = null;

async function refreshServicesFromBackend(token = state.viewToken) {
  try {
    const params = new URLSearchParams({
      q: state.filters.q,
      source: state.filters.source,
      domain: state.filters.domain,
      urgency: state.filters.urgency,
      needs: (state.structured?.needs || state.case.issueTypes).join(","),
      region: state.case.region || "",
      target: state.structured?.target || state.case.targetType || "",
    });
    const data = await apiFetch(`/api/services?${params.toString()}`);
    if (token !== state.viewToken) return;
    services = data.services || services;
    state.apiStatus = "online";
    const llmSuffix = state.llmEnabled ? "+LLM" : "";
    state.apiMessage = data.meta?.fallback ? `백엔드 연결됨${llmSuffix} · 공공데이터 폴백` : `백엔드+공공데이터${llmSuffix} 연결됨`;
    if (!services.some((service) => service.id === state.selectedServiceId)) {
      state.selectedServiceId = services[0]?.id || null;
    }
    if (state.view === "search" && token === state.viewToken) render();
  } catch (error) {
    if (token !== state.viewToken) return;
    state.apiStatus = "offline";
    state.apiMessage = "백엔드 미연결 · 로컬 샘플로 동작";
  }
}

function updateFilter(field, value) {
  state.filters[field] = value;
  render();
  window.clearTimeout(serviceRefreshTimer);
  const token = state.viewToken;
  serviceRefreshTimer = window.setTimeout(() => refreshServicesFromBackend(token), 180);
}

function logout() {
  state.loggedIn = false;
  state.view = "dashboard";
  render();
}

function render() {
  const app = document.querySelector("#app");
  app.innerHTML = state.loggedIn ? renderShell() : renderLogin();
  if (state.toast) {
    app.insertAdjacentHTML("beforeend", `<div class="toast show">${escapeHtml(state.toast)}</div>`);
  }
  if (state.modalServiceId) {
    app.insertAdjacentHTML("beforeend", renderServiceModal(state.modalServiceId));
  }
  if (window.lucide) window.lucide.createIcons();
}

function renderLogin() {
  return `
    <main class="login-shell">
      <section class="login-panel">
        <div>
          <div class="brand-lockup">
            <div class="brand-mark">${icon("heart-handshake")}</div>
            <div>복지연계 코파일럿</div>
          </div>
          <h1 class="login-title">현장 상담을 추천서까지 연결합니다</h1>
          <p class="login-subtitle">상담 메모를 구조화하고, 공공·지자체·민간 서비스를 패키지로 묶어 실무자가 바로 확인할 수 있는 추천서를 생성합니다.</p>
          <form class="login-form" onsubmit="event.preventDefault(); state.loggedIn = true; render(); hydrateBackend();">
            <div class="field">
              <label for="login-id">아이디</label>
              <input id="login-id" value="case.worker" autocomplete="username" />
            </div>
            <div class="field">
              <label for="login-pw">비밀번호</label>
              <input id="login-pw" value="demo2026" type="password" autocomplete="current-password" />
            </div>
            <button class="btn primary" type="submit">${icon("log-in")} 로그인</button>
          </form>
        </div>
        <div class="login-meta">
          ${pill("웹 PC")}
          ${pill("모바일 웹")}
          ${pill("현장 종사자")}
        </div>
      </section>
      <section class="login-visual" aria-label="업무 흐름">
        <div class="flow-board">
          ${renderFlowStep("clipboard-pen", "상담 입력", "대상·지역·문제·메모")}
          ${renderFlowStep("sparkles", "AI 구조화", "욕구·키워드·긴급 신호")}
          ${renderFlowStep("database", "통합 검색", "중앙·지자체·민간·기관")}
          ${renderFlowStep("boxes", "패키지 추천", "다중 욕구 기반 조합")}
          ${renderFlowStep("file-check-2", "추천서 생성", "조건·서류·연결 순서")}
        </div>
      </section>
    </main>
  `;
}

function renderFlowStep(iconName, title, text) {
  return `
    <div class="flow-step">
      ${icon(iconName)}
      <div>
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(text)}</span>
      </div>
    </div>
  `;
}

function renderShell() {
  const current = views.find(([key]) => key === state.view);
  return `
    <div class="app-shell">
      <aside class="sidebar ${state.mobileNav ? "open" : ""}">
        <div class="sidebar-head">
          <div class="brand-mark">${icon("heart-handshake")}</div>
          <div class="sidebar-title">
            <strong>복지연계 코파일럿</strong>
            <span>AI 추천·연계 시스템</span>
          </div>
        </div>
        <nav class="nav">
          ${views
            .map(
              ([key, label, iconName]) => `
                <button type="button" class="nav-button ${state.view === key ? "active" : ""}" data-view="${key}">
                  ${icon(iconName)}
                  <span>${label}</span>
                </button>
              `
            )
            .join("")}
        </nav>
        <div class="sidebar-foot">
          <div class="operator-card">
            <strong>김현장 주무관</strong>
            <span>관악구 통합사례관리</span>
          </div>
          <button class="btn ghost" onclick="logout()">${icon("log-out")} 로그아웃</button>
        </div>
      </aside>
      <main class="main">
        <header class="topbar">
          <button class="icon-btn mobile-menu" title="메뉴" onclick="state.mobileNav = !state.mobileNav; render();">${icon("menu")}</button>
          <div class="topbar-left">
            <div class="eyebrow">CASE ${escapeHtml(state.case.id)}</div>
            <h1 class="page-title">${escapeHtml(current?.[1] || "대시보드")}</h1>
          </div>
          <div class="topbar-actions">
            ${pill(state.apiMessage, state.apiStatus === "online" ? "green" : "amber")}
            <button class="btn ghost" onclick="saveCase()">${icon("save")} 임시저장</button>
            <button class="btn primary" onclick="setView('report')">${icon("file-text")} 추천서</button>
          </div>
        </header>
        <section class="content">
          ${renderCurrentView()}
        </section>
      </main>
    </div>
  `;
}

function renderCurrentView() {
  if (state.view === "dashboard") return renderDashboard();
  if (state.view === "case") return renderCaseView();
  if (state.view === "search") return renderSearchView();
  if (state.view === "packages") return renderPackageView();
  if (state.view === "report") return renderReportView();
  return renderSettingsView();
}

function renderDashboard() {
  const structuredNeeds = state.structured?.needs || state.case.issueTypes;
  return `
    <div class="grid-3">
      ${renderStat("timer", "18분", "평균 탐색·정리 시간")}
      ${renderStat("file-check-2", "72%", "추천서 활용률")}
      ${renderStat("link", "61%", "연계 접수 완료율")}
    </div>
    <section class="workspace-panel">
      <div class="panel-head">
        <div>
          <h2 class="panel-title">진행 중인 상담</h2>
          <p class="panel-subtitle">${escapeHtml(state.case.title)} · ${escapeHtml(state.case.region || "지역 미입력")}</p>
        </div>
        <div class="button-row">
          <button class="btn ghost" onclick="createNewCase()">${icon("plus")} 새 상담</button>
          <button class="btn primary" onclick="setView('case')">${icon("arrow-right")} 이어서 입력</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="timeline">
          ${renderTimelineStep("상담 입력", "기본정보·메모", state.case.memo ? "current" : "")}
          ${renderTimelineStep("AI 구조화", structuredNeeds.length ? structuredNeeds.join(" · ") : "대기", state.structured ? "current" : "")}
          ${renderTimelineStep("통합 검색", "후보군 확인", state.view === "search" ? "current" : "")}
          ${renderTimelineStep("패키지 추천", state.packages.length ? `${state.packages.length}개 생성` : "대기", state.packages.length ? "current" : "")}
          ${renderTimelineStep("추천서", selectedPackage()?.title || "대기", state.view === "report" ? "current" : "")}
        </div>
      </div>
    </section>
    <div class="grid-2">
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">최근 상담</h2>
            <p class="panel-subtitle">불러오면 현재 작업 사례로 전환됩니다</p>
          </div>
        </div>
        <div class="panel-body stack">
          ${recentCases
            .map(
              (item) => `
                <div class="recent-row">
                  <div class="recent-main">
                    <strong>${escapeHtml(item.title)}</strong>
                    <span class="tiny">${escapeHtml(item.region)} · ${escapeHtml(item.status)}</span>
                    <div class="pill-row">${caseNeeds(item).map((need) => pill(need, needsColor(need))).join("")}</div>
                  </div>
                  <button class="icon-btn" title="불러오기" onclick="loadRecentCase('${item.id}')">${icon("folder-open")}</button>
                </div>
              `
            )
            .join("")}
        </div>
      </section>
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">우선 확인 항목</h2>
            <p class="panel-subtitle">긴급 신호와 조건 확인을 상담 흐름에 맞춰 표시합니다</p>
          </div>
        </div>
        <div class="panel-body stack">
          ${(state.structured?.riskChecks || [
            { label: "메모 구조화 필요", text: "상담 입력 화면에서 구조화 버튼을 눌러 욕구와 긴급 신호를 확인합니다." },
          ])
            .map(
              (item) => `
                <div class="check-row">
                  <strong>${icon("badge-alert")} ${escapeHtml(item.label)}</strong>
                  <p>${escapeHtml(item.text)}</p>
                </div>
              `
            )
            .join("")}
        </div>
      </section>
    </div>
  `;
}

function renderStat(iconName, value, label) {
  return `
    <div class="stat-card">
      <div class="metric-icon">${icon(iconName)}</div>
      <strong>${escapeHtml(value)}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

function renderTimelineStep(title, text, className) {
  return `
    <div class="timeline-step ${className}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(text)}</span>
    </div>
  `;
}

function renderCaseView() {
  return `
    <div class="grid-2">
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">상담 입력</h2>
            <p class="panel-subtitle">대상·지역·문제·긴급도·상담 메모</p>
          </div>
          <div class="button-row">
            <button class="btn ghost" onclick="createNewCase()">${icon("plus")} 새 상담</button>
            <button class="btn secondary" onclick="saveCase()">${icon("save")} 저장</button>
          </div>
        </div>
        <div class="panel-body stack">
          <div class="form-grid">
            <div class="field">
              <label for="case-title">사례 제목</label>
              <input id="case-title" value="${escapeHtml(state.case.title)}" oninput="updateCase('title', this.value, false)" />
            </div>
            <div class="field">
              <label for="target-type">대상 유형</label>
              <select id="target-type" onchange="updateCase('targetType', this.value)">
                ${["청년", "아동·청소년", "노인", "장애인", "의료취약", "저소득", "다문화"].map((item) => option(item, state.case.targetType)).join("")}
              </select>
            </div>
            <div class="field">
              <label for="region">지역</label>
              <input id="region" value="${escapeHtml(state.case.region)}" placeholder="예: 서울 관악구" oninput="updateCase('region', this.value, false)" />
            </div>
            <div class="field">
              <div class="field-label">긴급도</div>
              <div class="segmented">
                ${["일반", "주의", "긴급"]
                  .map(
                    (level) => `<button class="segment ${state.case.urgency === level ? "active" : ""}" onclick="updateCase('urgency', '${level}')">${level}</button>`
                  )
                  .join("")}
              </div>
            </div>
            <div class="field full">
              <div class="label-row">
                <span class="field-label">문제 유형</span>
                <span class="tiny">다중 선택</span>
              </div>
              <div class="pill-row">
                ${NEEDS.map(
                  (need) =>
                    `<button class="pill toggle ${needsColor(need)} ${state.case.issueTypes.includes(need) ? "active" : ""}" onclick="toggleIssue('${need}')">${escapeHtml(need)}</button>`
                ).join("")}
              </div>
            </div>
            <div class="field full">
              <div class="label-row">
                <label for="memo">상담 메모</label>
                <span id="memo-count" class="tiny">${state.case.memo.length}자</span>
              </div>
              <textarea id="memo" oninput="updateCase('memo', this.value, false)" placeholder="상담 내용을 입력하세요">${escapeHtml(state.case.memo)}</textarea>
            </div>
          </div>
          <div class="button-row">
            ${["주거", "생계", "심리", "의료", "돌봄"].map((item) => `<button class="btn ghost" onclick="useTemplate('${item}')">${icon("wand-sparkles")} ${item} 템플릿</button>`).join("")}
          </div>
          <div class="button-row">
            <button class="btn primary" onclick="inferStructure()">${icon("sparkles")} AI 구조화</button>
            <button class="btn secondary" onclick="inferStructure({ goTo: 'search' })">${icon("search")} 통합 검색으로</button>
          </div>
        </div>
      </section>
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">AI 구조화 결과</h2>
            <p class="panel-subtitle">욕구 태그·키워드·긴급 신호</p>
          </div>
          <button class="btn ghost" onclick="inferStructure()">${icon("refresh-cw")} 다시 분석</button>
        </div>
        <div class="panel-body">
          ${state.structured ? renderStructured() : `<div class="empty-state">상담 메모를 입력하고 AI 구조화를 실행하세요.</div>`}
        </div>
      </section>
    </div>
  `;
}

function option(value, selected) {
  return `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>${escapeHtml(value)}</option>`;
}

function renderStructured() {
  return `
    <div class="stack">
      <div>
        <div class="field-label">핵심 욕구</div>
        <div class="pill-row" style="margin-top: 8px;">
          ${NEEDS.map(
            (need) =>
              `<button class="pill toggle ${needsColor(need)} ${state.structured.needs.includes(need) ? "active" : ""}" onclick="toggleStructuredNeed('${need}')">${escapeHtml(need)}</button>`
          ).join("")}
        </div>
      </div>
      <div>
        <div class="field-label">추출 키워드</div>
        <div class="pill-row" style="margin-top: 8px;">
          ${state.structured.keywords.length ? state.structured.keywords.map((word) => pill(word)).join("") : pill("키워드 없음")}
        </div>
      </div>
      <div class="detail-grid">
        <div class="detail-item">
          <strong>대상</strong>
          <span>${escapeHtml(state.structured.target)}</span>
        </div>
        <div class="detail-item">
          <strong>지역</strong>
          <span>${escapeHtml(state.structured.region || "미입력")}</span>
        </div>
        <div class="detail-item">
          <strong>긴급도</strong>
          <span>${escapeHtml(state.structured.urgency)}</span>
        </div>
        <div class="detail-item">
          <strong>후속 단계</strong>
          <span>검색 후보 생성 및 패키지 추천</span>
        </div>
      </div>
      <div class="stack">
        ${state.structured.riskChecks
          .map(
            (item) => `
              <div class="check-row">
                <strong>${icon(item.label.includes("즉시") ? "siren" : "shield-check")} ${escapeHtml(item.label)}</strong>
                <p>${escapeHtml(item.text)}</p>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="button-row">
        <button class="btn primary" onclick="setView('search')">${icon("search")} 검색 후보 보기</button>
        <button class="btn secondary" onclick="generatePackages({ goTo: 'packages' })">${icon("boxes")} 패키지 생성</button>
      </div>
    </div>
  `;
}

function renderSearchView() {
  const results = filteredServices();
  const groups = results.reduce((acc, service) => {
    acc[service.group] = acc[service.group] || [];
    acc[service.group].push(service);
    return acc;
  }, {});

  return `
    <section class="workspace-panel">
      <div class="panel-head">
        <div>
          <h2 class="panel-title">복지·기관 통합 검색</h2>
          <p class="panel-subtitle">중앙·지자체·민간·기관 데이터 후보 ${results.length}건</p>
        </div>
        <button class="btn primary" onclick="generatePackages({ goTo: 'packages' })">${icon("boxes")} 패키지 추천</button>
      </div>
      <div class="panel-body stack">
        <div class="search-tools">
          <input value="${escapeHtml(state.filters.q)}" placeholder="서비스명, 대상, 키워드 검색" oninput="updateFilter('q', this.value)" />
          <select onchange="updateFilter('source', this.value)">
            ${["전체", "중앙", "지자체", "민간", "기관"].map((item) => option(item, state.filters.source)).join("")}
          </select>
          <select onchange="updateFilter('domain', this.value)">
            ${["전체", ...NEEDS].map((item) => option(item, state.filters.domain)).join("")}
          </select>
          <select onchange="updateFilter('urgency', this.value)">
            ${["전체", "긴급", "일반"].map((item) => option(item, state.filters.urgency)).join("")}
          </select>
        </div>
        <div class="grid-2">
          <div class="service-list">
            ${results.length ? results.map(renderServiceCard).join("") : `<div class="empty-state">검색 결과가 없습니다.</div>`}
          </div>
          <div class="stack">
            <section class="workspace-panel">
              <div class="panel-head">
                <div>
                  <h2 class="panel-title">중복 묶음</h2>
                  <p class="panel-subtitle">대표 서비스와 출처별 유사 항목</p>
                </div>
              </div>
              <div class="panel-body source-stack">
                ${Object.values(groups)
                  .filter((items) => items.length > 1)
                  .map(
                    (items) => `
                      <div class="source-row">
                        <div>
                          <strong>${escapeHtml(items[0].name)}</strong>
                          <div class="tiny">${items.map((item) => `${item.source} · ${item.region}`).join(" / ")}</div>
                        </div>
                        ${pill(`${items.length}개 출처`, "blue")}
                      </div>
                    `
                  )
                  .join("") || `<div class="empty-state">현재 필터에서는 중복 후보가 없습니다.</div>`}
              </div>
            </section>
            ${renderSelectedServiceDetail()}
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderServiceCard(service) {
  return `
    <article class="service-card ${state.selectedServiceId === service.id ? "selected" : ""}">
      <div class="service-head">
        <div class="service-title">
          <strong>${escapeHtml(service.name)}</strong>
          <div class="pill-row">
            ${pill(service.source, "blue")}
            ${pill(service.urgency, service.urgency === "긴급" ? "red" : "")}
            ${service.domains.map((domain) => pill(domain, needsColor(domain))).join("")}
          </div>
        </div>
        <button class="icon-btn" title="선택" onclick="state.selectedServiceId='${service.id}'; render();">${icon("mouse-pointer-click")}</button>
      </div>
      <div class="service-summary">${escapeHtml(service.summary)}</div>
      <div class="button-row">
        <button class="btn ghost" onclick="openServiceDetail('${service.id}')">${icon("panel-top-open")} 상세</button>
        <button class="btn secondary" onclick="generatePackages().then(() => addServiceToPackage('${service.id}'))">${icon("plus")} 패키지 추가</button>
      </div>
    </article>
  `;
}

function renderSelectedServiceDetail() {
  const service = services.find((item) => item.id === state.selectedServiceId) || filteredServices()[0];
  if (!service) return "";
  return `
    <section class="workspace-panel">
      <div class="panel-head">
        <div>
          <h2 class="panel-title">서비스 핵심 필드</h2>
          <p class="panel-subtitle">${escapeHtml(service.name)}</p>
        </div>
        <button class="icon-btn" title="상세" onclick="openServiceDetail('${service.id}')">${icon("external-link")}</button>
      </div>
      <div class="panel-body">
        <div class="detail-grid">
          ${detailItem("지원대상", service.eligibility)}
          ${detailItem("지원내용", service.support)}
          ${detailItem("신청절차", service.process)}
          ${detailItem("문의처", service.contact)}
          ${detailItem("출처", `${service.source} · ${service.updated}`)}
          ${detailItem("URL", service.url)}
        </div>
      </div>
    </section>
  `;
}

function detailItem(title, text) {
  return `<div class="detail-item"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span></div>`;
}

function renderPackageView() {
  if (!state.packages.length) generatePackagesLocal({ show: false });
  const pkg = selectedPackage();
  const included = selectedPackageServices();
  return `
    <div class="package-layout">
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">추천 패키지 목록</h2>
            <p class="panel-subtitle">욕구·긴급도 기반 상위 3개</p>
          </div>
          <button class="btn ghost" onclick="generatePackages()">${icon("refresh-cw")} 재생성</button>
        </div>
        <div class="panel-body package-list">
          ${state.packages
            .map(
              (item) => `
                <article class="package-card ${item.id === pkg.id ? "active" : ""}">
                  <div class="package-head">
                    <div class="package-title">
                      <strong>${escapeHtml(item.title)}</strong>
                      <span class="muted">${escapeHtml(item.summary)}</span>
                    </div>
                    <div class="score">${item.score}</div>
                  </div>
                  <div class="pill-row">
                    ${uniquePackageDomains(item).map((domain) => pill(domain, needsColor(domain))).join("")}
                  </div>
                  <button class="btn ${item.id === pkg.id ? "secondary" : "ghost"}" onclick="setSelectedPackage('${item.id}')">${icon("check-circle-2")} 선택</button>
                </article>
              `
            )
            .join("")}
        </div>
      </section>
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">패키지 편집</h2>
            <p class="panel-subtitle">${escapeHtml(pkg.title)} · 포함 ${included.length}건</p>
          </div>
          <button class="btn primary" onclick="setView('report')">${icon("file-text")} 추천서 생성</button>
        </div>
        <div class="panel-body stack">
          ${pkg.items.map((item) => renderPackageItem(item, pkg)).join("")}
          <div class="inline-section">
            <div class="inline-section-head">
              <div>
                <h2 class="panel-title">기관 연결 리스트</h2>
                <p class="panel-subtitle">서비스 문의처와 지역 기관 API 결과</p>
              </div>
              ${state.providerMeta ? pill(state.providerMeta.fallback ? "기관 API 폴백" : "기관 API 연결", state.providerMeta.fallback ? "amber" : "green") : ""}
            </div>
            <div class="source-stack">
              ${included
                .map(
                  (service) => `
                    <div class="source-row">
                      <div>
                        <strong>${escapeHtml(service.name)}</strong>
                        <div class="tiny">${escapeHtml(service.contact)}</div>
                      </div>
                      ${pill(service.source, "blue")}
                    </div>
                  `
                )
                .join("")}
              ${
                state.providerLoading
                  ? `<div class="empty-state">지역 기관 API를 불러오는 중입니다.</div>`
                  : state.providers
                      .map(
                        (provider) => `
                          <div class="source-row">
                            <div>
                              <strong>${escapeHtml(provider.name)}</strong>
                              <div class="tiny">${escapeHtml(provider.serviceName || provider.serviceType || "기관 서비스")} · ${escapeHtml(provider.region || state.case.region || "")}</div>
                              <div class="tiny">${escapeHtml(provider.address || "")}</div>
                            </div>
                            <div class="pill-row">
                              ${pill(provider.source || "기관", provider.source === "샘플" ? "" : "blue")}
                              ${provider.contact ? pill(provider.contact) : ""}
                            </div>
                          </div>
                        `
                      )
                      .join("")
              }
            </div>
          </div>
        </div>
      </section>
    </div>
  `;
}

function uniquePackageDomains(pkg) {
  return Array.from(
    new Set(
      pkg.items
        .map((item) => services.find((service) => service.id === item.serviceId))
        .filter(Boolean)
        .flatMap((service) => service.domains)
    )
  );
}

function renderPackageItem(item, pkg) {
  const service = services.find((entry) => entry.id === item.serviceId);
  if (!service) return "";
  return `
    <div class="package-item ${item.included ? "" : "excluded"}">
      <input type="checkbox" ${item.included ? "checked" : ""} aria-label="포함 여부" onchange="togglePackageItem('${service.id}')" />
      <div class="package-item-main">
        <strong>${escapeHtml(service.name)}</strong>
        <span class="tiny">${escapeHtml(service.source)} · ${escapeHtml(service.contact)}</span>
      </div>
      <div class="priority-buttons">
        <button class="icon-btn" title="상세" onclick="openServiceDetail('${service.id}')">${icon("panel-top-open")}</button>
      </div>
    </div>
  `;
}

function renderReportView() {
  if (!state.packages.length) generatePackagesLocal({ show: false });
  const { pkg, selectedServices, needs, contacts } = reportData();
  const docs = Array.from(new Set(selectedServices.flatMap((service) => service.docs)));
  const report = state.lastReport;
  const reportNeeds = report?.needs || needs;
  const reportReason =
    report?.reason ||
    `${pkg.summary}. 상담 메모에서 ${needs.join(", ")} 욕구가 확인되어 관련 제도와 지역 기관을 조합했습니다. 최종 신청 가능성은 소득·재산·거주 요건 확인 후 판단합니다.`;
  const reportServices =
    report?.services ||
    selectedServices.map((service) => ({
      name: service.name,
      summary: service.summary,
      source: service.source,
      updated: service.updated,
    }));
  const reportConditions =
    report?.conditions || selectedServices.map((service) => ({ service: service.name, text: service.eligibility }));
  const reportDocs = report?.docs || docs;
  const reportSteps = report?.steps || selectedServices.map((service) => service.process);
  const reportContacts =
    report?.contacts || contacts.map((service) => ({ service: service.name, contact: service.contact, url: service.url }));
  const reportCaseSummary =
    report?.caseSummary ||
    `${state.case.targetType} / ${state.case.region || "지역 미입력"} 사례입니다. 상담 메모에서 ${reportNeeds.join(", ")} 욕구가 확인되어 ${pkg.title}를 우선 검토합니다.`;
  const priorityAssessment =
    report?.priorityAssessment || [{ level: state.case.urgency || "주의", text: "소득·재산·거주지·연령 기준 확인 후 최종 신청 가능성을 판단합니다." }];
  const servicePlans = report?.servicePlans || [];
  const actionPlan =
    report?.actionPlan || [
      { timing: "오늘", tasks: ["위험 수준과 1순위 서비스 문의처를 확인합니다."] },
      { timing: "3일 이내", tasks: ["공통 증빙자료와 서비스별 신청 경로를 정리합니다."] },
      { timing: "1~2주", tasks: ["접수 결과와 보완서류를 점검하고 대체 자원을 확인합니다."] },
    ];
  const checklist =
    report?.eligibilityChecklist || [
      { title: "공통 확인", items: ["신분 확인", "주민등록상 주소와 실거주지", "가구원 구성", "소득·재산 변동"] },
      { title: "신청 가능성", items: ["서비스별 대상 기준", "중복 수급 제한", "최근 지원 이력", "관할 기관 접수 가능 여부"] },
    ];
  const followUpQuestions = report?.followUpQuestions || [];
  const dataLimitations =
    report?.dataLimitations || [
      "본 추천서는 상담 보조 자료이며 최종 수급 가능 여부는 접수기관 심사로 확인합니다.",
      "공공데이터 기준일과 관할 지자체 운영 기준이 다를 수 있어 신청 전 최신 공고를 확인합니다.",
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
              ${renderServicePlans(servicePlans, selectedServices)}
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
              followUpQuestions.length
                ? `<section class="report-block"><h3>추가 상담 질문</h3>${renderReportBullets(followUpQuestions)}</section>`
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
                          <td>${escapeHtml(contact.service)}</td>
                          <td>${escapeHtml(contact.contact)}</td>
                          <td>${escapeHtml(contact.url)}</td>
                        </tr>
                      `
                    )
                    .join("")}
                </tbody>
              </table>
            </section>
            <section class="report-block">
              <h3>확인 필요 사항</h3>
              ${renderReportBullets(dataLimitations)}
            </section>
          </div>
        </article>
      </div>
    </section>
  `;
}

function renderSettingsView() {
  return `
    <div class="grid-2">
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">FAQ</h2>
            <p class="panel-subtitle">현장 사용 중 자주 확인하는 항목</p>
          </div>
        </div>
        <div class="panel-body stack">
          ${[
            ["AI 추천을 그대로 적용해도 되나요?", "추천은 상담 보조 정보이며, 최종 판단과 신청 가능성 확인은 담당자가 수행합니다."],
            ["민감정보는 어떻게 다루나요?", "사례 입력은 최소화하고, 출력 추천서에는 불필요한 주민번호·진단명 등 민감정보를 포함하지 않는 운영을 전제로 합니다."],
            ["데이터 출처는 어디서 확인하나요?", "서비스 상세와 추천서 문의처 영역에서 출처, 기준연도, URL을 함께 확인합니다."],
          ]
            .map(
              ([q, a]) => `
                <div class="faq-row">
                  <strong>${escapeHtml(q)}</strong>
                  <span class="muted">${escapeHtml(a)}</span>
                </div>
              `
            )
            .join("")}
        </div>
      </section>
      <section class="workspace-panel">
        <div class="panel-head">
          <div>
            <h2 class="panel-title">데이터·권한 설정</h2>
            <p class="panel-subtitle">관리자 화면 초안</p>
          </div>
        </div>
        <div class="panel-body stack">
          ${renderSettingToggle("중앙부처 데이터", true)}
          ${renderSettingToggle("지자체 데이터", true)}
          ${renderSettingToggle("민간기관 데이터", true)}
          ${renderSettingToggle("중복 감지 규칙", true)}
          <div class="detail-grid">
            ${detailItem("접근 권한", "현장 종사자, 관리자")}
            ${detailItem("보안 기준", "최소 수집, 마스킹, 권한 분리")}
          </div>
        </div>
      </section>
    </div>
  `;
}

function renderSettingToggle(label, enabled) {
  return `
    <div class="source-row">
      <strong>${escapeHtml(label)}</strong>
      ${pill(enabled ? "활성" : "비활성", enabled ? "green" : "")}
    </div>
  `;
}

function renderServiceModal(serviceId) {
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
          <div class="pill-row">
            ${service.domains.map((domain) => pill(domain, needsColor(domain))).join("")}
            ${pill(service.target, "blue")}
            ${pill(service.urgency, service.urgency === "긴급" ? "red" : "")}
            ${service.detailLoaded ? pill("상세조회 API", "green") : ""}
          </div>
          <p class="service-summary">${escapeHtml(service.summary)}</p>
          <div class="detail-grid">
            ${detailItem("지원대상/기준", service.eligibility)}
            ${service.selectionCriteria ? detailItem("선정기준", service.selectionCriteria) : ""}
            ${detailItem("지원내용", service.support)}
            ${detailItem("신청절차", service.process)}
            ${detailItem("준비서류", service.docs.join(", "))}
            ${detailItem("문의처", service.contact)}
            ${detailItem("URL", service.url)}
            ${service.laws?.length ? detailItem("근거법령", service.laws.join(", ")) : ""}
          </div>
          ${
            service.applicationSteps?.length
              ? `<div class="report-block"><h3>연계 단계</h3><ol>${service.applicationSteps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ol></div>`
              : ""
          }
          <div class="button-row">
            <button class="btn secondary" onclick="generatePackages().then(() => { addServiceToPackage('${service.id}'); state.modalServiceId = null; render(); })">${icon("plus")} 패키지 추가</button>
            <button class="btn ghost" onclick="state.modalServiceId = null; render();">${icon("check")} 확인</button>
          </div>
        </div>
      </article>
    </div>
  `;
}

document.addEventListener("click", (event) => {
  const navButton = event.target.closest("[data-view]");
  if (!navButton) return;
  event.preventDefault();
  setView(navButton.dataset.view);
});

render();
