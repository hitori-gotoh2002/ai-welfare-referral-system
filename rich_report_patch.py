from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

import backend_server as b


ENABLE_RICH_REPORT = os.getenv("ENABLE_LLM_RICH_REPORT", "true").lower() not in {"0", "false", "no"}
_ORIGINAL_BUILD_REPORT: Any = None
_ORIGINAL_FETCH_PUBLIC_WELFARE_DETAIL: Any = None
_ORIGINAL_NORMALIZE_PUBLIC_SERVICE: Any = None


BOKJIRO_DETAIL_BASE = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do"


def compact_text(value: Any, limit: int = 360) -> str:
    text = b.clean_text(str(value or ""))
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text_list(value: Any, limit: int = 6, item_limit: int = 180) -> list[str]:
    result: list[str] = []
    for item in as_list(value):
        text = compact_text(item, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def object_list(value: Any, limit: int = 8) -> list[dict[str, Any]]:
    return [item for item in as_list(value) if isinstance(item, dict)][:limit]


def service_context(service: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": service.get("id", ""),
        "name": service.get("name", ""),
        "source": service.get("source", ""),
        "region": service.get("region", ""),
        "target": service.get("target", ""),
        "domains": service.get("domains", []),
        "urgency": service.get("urgency", ""),
        "summary": compact_text(service.get("summary", ""), 420),
        "eligibility": compact_text(service.get("eligibility", ""), 420),
        "selectionCriteria": compact_text(service.get("selectionCriteria", ""), 360),
        "support": compact_text(service.get("support", ""), 420),
        "process": compact_text(service.get("process", ""), 360),
        "docs": text_list(service.get("docs", []), 8, 120),
        "contact": compact_text(service.get("contact", ""), 180),
        "url": compact_text(service.get("url", ""), 220),
    }


def service_identity(service: dict[str, Any]) -> tuple[str, str]:
    try:
        return b.public_detail_identity(service)
    except Exception:
        return service.get("source", ""), service.get("externalId") or service.get("id", "")


def is_bokjiro_main_url(url: str) -> bool:
    value = str(url or "").strip().rstrip("/")
    return value in {"https://www.bokjiro.go.kr", "http://www.bokjiro.go.kr"}


def bokjiro_detail_url(service_id: str) -> str:
    if not service_id:
        return ""
    return f"{BOKJIRO_DETAIL_BASE}?wlfareInfoId={quote(str(service_id), safe='')}"


def ensure_service_detail_url(service: dict[str, Any]) -> dict[str, Any]:
    result = dict(service)
    source, service_id = service_identity(result)
    current_url = str(result.get("url") or "").strip()
    detail_url = str(result.get("detailUrl") or result.get("servDtlLink") or "").strip()
    if not detail_url and source in {"중앙", "지자체"} and service_id and not str(service_id).startswith("svc-"):
        detail_url = bokjiro_detail_url(service_id)
    if detail_url:
        result["detailUrl"] = detail_url
        if not current_url or is_bokjiro_main_url(current_url):
            result["url"] = detail_url
    return result


def install_service_link_patch() -> None:
    global _ORIGINAL_FETCH_PUBLIC_WELFARE_DETAIL, _ORIGINAL_NORMALIZE_PUBLIC_SERVICE

    if hasattr(b, "fetch_public_welfare_detail") and not getattr(b, "_RICH_REPORT_LINK_FETCH_PATCHED", False):
        _ORIGINAL_FETCH_PUBLIC_WELFARE_DETAIL = b.fetch_public_welfare_detail

        def fetch_public_welfare_detail(service: dict[str, Any]):
            detail, meta = _ORIGINAL_FETCH_PUBLIC_WELFARE_DETAIL(service)
            return ensure_service_detail_url(detail), meta

        b.fetch_public_welfare_detail = fetch_public_welfare_detail
        b._RICH_REPORT_LINK_FETCH_PATCHED = True

    if hasattr(b, "normalize_public_service") and not getattr(b, "_RICH_REPORT_LINK_NORMALIZE_PATCHED", False):
        _ORIGINAL_NORMALIZE_PUBLIC_SERVICE = b.normalize_public_service

        def normalize_public_service(element: Any, source: str) -> dict[str, Any]:
            return ensure_service_detail_url(_ORIGINAL_NORMALIZE_PUBLIC_SERVICE(element, source))

        b.normalize_public_service = normalize_public_service
        b._RICH_REPORT_LINK_NORMALIZE_PATCHED = True

    for service in getattr(b, "SERVICES", []):
        service.update(ensure_service_detail_url(service))


def selected_services_for_package(
    package: dict[str, Any], catalog: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    selected = []
    for item in package.get("items", []):
        if not item.get("included", True):
            continue
        service_id = item.get("serviceId", "")
        service = b.find_service(service_id, catalog)
        if service:
            selected.append(service)
    return selected


def case_summary(case: dict[str, Any], structured: dict[str, Any], package: dict[str, Any]) -> str:
    target = structured.get("target") or case.get("targetType") or "대상자"
    region = structured.get("region") or case.get("region") or "지역 미입력"
    urgency = structured.get("urgency") or case.get("urgency") or "주의"
    needs = structured.get("needs") or case.get("issueTypes") or []
    need_text = ", ".join(needs) if needs else "상담 메모 기반 욕구"
    return (
        f"{target} / {region} 사례입니다. 상담 메모에서 {need_text} 욕구가 확인되어 "
        f"{package.get('title', '추천 패키지')}를 우선 검토합니다. 긴급도는 {urgency}로 보되, "
        "실제 수급 가능성은 소득, 재산, 가구 구성, 거주지, 중복지원 여부 확인 후 판단해야 합니다."
    )


def default_priority_assessment(case: dict[str, Any], structured: dict[str, Any]) -> list[dict[str, str]]:
    urgency = structured.get("urgency") or case.get("urgency") or "주의"
    needs = structured.get("needs") or case.get("issueTypes") or []
    result = [
        {
            "level": urgency,
            "text": "생계, 주거, 의료, 안전 위험 중 즉시 개입이 필요한 항목을 먼저 확인합니다.",
        },
        {
            "level": "자격 확인",
            "text": "소득, 재산, 가구원, 연령, 거주지 요건은 접수기관 기준으로 재확인합니다.",
        },
    ]
    if needs:
        result.append({"level": "욕구 범위", "text": f"확인된 핵심 욕구는 {', '.join(needs[:5])}입니다."})
    return result


def default_service_plans(services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plans = []
    for service in services:
        priority = "높음" if service.get("urgency") == "긴급" else "중간"
        docs = text_list(service.get("docs", []), 6, 120)
        eligibility = [
            item
            for item in [
                compact_text(service.get("eligibility", ""), 180),
                compact_text(service.get("selectionCriteria", ""), 180),
            ]
            if item
        ]
        application = [
            item
            for item in [
                compact_text(service.get("process", ""), 180),
                compact_text(service.get("contact", ""), 120),
            ]
            if item
        ]
        plans.append(
            {
                "service": service.get("name", ""),
                "priority": priority,
                "purpose": ", ".join(service.get("domains", [])[:4]) or "지원 가능성 확인",
                "whyRecommended": compact_text(service.get("summary", ""), 220)
                or "상담 메모의 주요 욕구와 연결되는 후보 서비스입니다.",
                "eligibilityToCheck": eligibility or ["대상, 소득, 재산, 거주지, 중복지원 여부 확인"],
                "applicationPath": application or ["관할 주민센터 또는 서비스 문의처에 접수 가능 여부 확인"],
                "requiredDocs": docs or ["신분증", "소득·재산 확인 자료", "가구 상황 증빙"],
                "contactAction": compact_text(service.get("contact", ""), 160) or "공식 문의처 확인",
                "cautions": ["추천은 상담 보조 자료이며 최종 선정은 접수기관 심사로 결정됩니다."],
            }
        )
    return plans


def default_action_plan(case: dict[str, Any], structured: dict[str, Any], services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    urgent = (structured.get("urgency") or case.get("urgency")) == "긴급"
    first_services = [service.get("name", "") for service in services[:3] if service.get("name")]
    first_text = ", ".join(first_services) if first_services else "우선 추천 서비스"
    today = [
        f"{first_text}의 신청 자격과 접수기관을 확인합니다.",
        "신분증, 주민등록등본, 소득·재산 자료, 위기 사유 증빙 등 공통 서류 보유 여부를 확인합니다.",
    ]
    if urgent:
        today.insert(0, "안전, 생계, 의료 공백이 즉시 위험한 경우 129, 112, 119 등 긴급 연락망을 우선 안내합니다.")
    return [
        {"timing": "오늘", "tasks": today},
        {
            "timing": "3일 이내",
            "tasks": [
                "서비스별 담당기관에 접수 가능 여부와 추가 서류를 확인합니다.",
                "누락 서류와 중복지원 제한 항목을 체크해 신청 순서를 조정합니다.",
            ],
        },
        {
            "timing": "1~2주",
            "tasks": [
                "접수 결과와 보완 요청을 추적하고 탈락 시 대체 서비스를 재검색합니다.",
                "민간·지역기관 연계가 필요한 경우 이용 가능 일정과 담당자를 기록합니다.",
            ],
        },
    ]


def default_checklist(services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docs = b.unique([doc for service in services for doc in service.get("docs", [])])
    return [
        {
            "title": "공통 확인",
            "items": ["대상자 신원", "가구 구성", "실거주지", "소득·재산 변동", "최근 지원 이력"],
        },
        {
            "title": "서비스별 확인",
            "items": [
                "대상 기준과 선정 기준",
                "신청 기간과 접수 방식",
                "중복지원 제한",
                "관할 기관 처리 가능 여부",
            ],
        },
        {
            "title": "준비 서류",
            "items": docs[:6] or ["신분증", "주민등록등본", "소득 확인 자료", "위기 사유 증빙"],
        },
    ]


def default_provider_plan(providers: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result = []
    for provider in (providers or [])[:5]:
        name = provider.get("name") or provider.get("serviceName") or "연계기관"
        result.append(
            {
                "name": name,
                "reason": compact_text(provider.get("serviceType") or provider.get("serviceName") or "지역 연계 가능 기관", 120),
                "contactAction": compact_text(
                    provider.get("contact") or provider.get("address") or "지역·서비스 제공 가능 여부 확인", 140
                ),
            }
        )
    return result


def default_follow_up_questions(case: dict[str, Any], structured: dict[str, Any]) -> list[str]:
    questions = [
        "현재 함께 거주하는 가구원과 실제 생계를 같이하는 사람이 누구인지 확인했나요?",
        "최근 3개월 안에 소득, 실직, 질병, 체납, 주거 불안 등 변화가 있었나요?",
        "이미 신청했거나 받고 있는 복지급여, 민간지원, 보험급여가 있나요?",
        "신청 서류를 준비할 수 없는 사유나 대리 신청이 필요한 상황이 있나요?",
    ]
    needs = structured.get("needs") or case.get("issueTypes") or []
    if "의료" in needs:
        questions.append("진단서, 입퇴원 확인서, 의료비 영수증 등 의료 증빙을 확보할 수 있나요?")
    if "주거" in needs:
        questions.append("임대차계약서, 월세 체납, 퇴거 위험 등 주거 증빙 자료가 있나요?")
    return questions[:7]


def build_default_report(
    base: dict[str, Any],
    case: dict[str, Any],
    structured: dict[str, Any],
    package: dict[str, Any],
    services: list[dict[str, Any]],
    providers: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    names = [service.get("name", "") for service in services if service.get("name")]
    reason = base.get("reason") or f"{package.get('summary', '추천 패키지')}를 바탕으로 우선 연계합니다."
    return {
        **base,
        "generatedAt": base.get("generatedAt") or datetime.now().isoformat(timespec="seconds"),
        "generatedBy": "rich-report-engine",
        "llmUsed": bool(base.get("llmUsed")),
        "caseSummary": base.get("caseSummary") or case_summary(case, structured, package),
        "priorityAssessment": base.get("priorityAssessment") or default_priority_assessment(case, structured),
        "reason": reason,
        "servicePlans": base.get("servicePlans") or default_service_plans(services),
        "eligibilityChecklist": base.get("eligibilityChecklist") or default_checklist(services),
        "actionPlan": base.get("actionPlan") or default_action_plan(case, structured, services),
        "providerPlan": base.get("providerPlan") or default_provider_plan(providers),
        "followUpQuestions": base.get("followUpQuestions") or default_follow_up_questions(case, structured),
        "counselorScript": base.get("counselorScript")
        or "오늘 추천은 확정 판정이 아니라 신청 가능성을 빠르게 좁히기 위한 안내입니다. 확인 서류와 관할기관 심사를 거쳐 실제 지원 여부가 결정됩니다.",
        "caseNote": base.get("caseNote")
        or f"{', '.join(names[:4])} 중심으로 신청 가능성을 안내했고, 소득·재산·거주지·중복지원 여부 확인이 필요함.",
        "dataLimitations": base.get("dataLimitations")
        or [
            "추천서는 상담 보조 자료이며 최종 수급 가능성은 접수기관 심사로 결정됩니다.",
            "공공데이터와 기관 정보는 갱신 시점 차이가 있을 수 있어 신청 전 최신 공고와 문의처 확인이 필요합니다.",
        ],
    }


def clean_service_plans(raw: Any, allowed_names: set[str], fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    fallback_by_name = {item.get("service", ""): item for item in fallback}
    for item in object_list(raw, 8):
        service_name = compact_text(item.get("service", ""), 120)
        if service_name not in allowed_names:
            continue
        base = fallback_by_name.get(service_name, {})
        result.append(
            {
                "service": service_name,
                "priority": compact_text(item.get("priority") or base.get("priority") or "중간", 20),
                "purpose": compact_text(item.get("purpose") or base.get("purpose") or "", 80),
                "whyRecommended": compact_text(
                    item.get("whyRecommended") or item.get("reason") or base.get("whyRecommended") or "", 240
                ),
                "eligibilityToCheck": text_list(item.get("eligibilityToCheck"), 5, 160)
                or base.get("eligibilityToCheck", []),
                "applicationPath": text_list(item.get("applicationPath"), 5, 160) or base.get("applicationPath", []),
                "requiredDocs": text_list(item.get("requiredDocs"), 8, 120) or base.get("requiredDocs", []),
                "contactAction": compact_text(item.get("contactAction") or base.get("contactAction") or "", 160),
                "cautions": text_list(item.get("cautions"), 4, 160) or base.get("cautions", []),
            }
        )
    return result or fallback


def clean_phase_list(raw: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in object_list(raw, 5):
        timing = compact_text(item.get("timing", ""), 40)
        tasks = text_list(item.get("tasks"), 6, 180)
        if timing and tasks:
            result.append({"timing": timing, "tasks": tasks})
    return result or fallback


def clean_checklist(raw: Any, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in object_list(raw, 6):
        title = compact_text(item.get("title", ""), 50)
        items = text_list(item.get("items"), 8, 150)
        if title and items:
            result.append({"title": title, "items": items})
    return result or fallback


def enhance_with_llm(
    fallback: dict[str, Any],
    case: dict[str, Any],
    structured: dict[str, Any],
    package: dict[str, Any],
    services: list[dict[str, Any]],
    providers: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if not ENABLE_RICH_REPORT or not b.GEMINI_API_KEY or not services:
        return fallback

    selected_context = [service_context(service) for service in services]
    allowed_names = {service.get("name", "") for service in services if service.get("name")}
    prompt = f"""
너는 한국 복지 현장 종사자가 대상자에게 설명하고 내부 기록에 붙일 수 있는 추천서 초안을 작성하는 보조자다.
아래에 제공된 상담 메모, 구조화 결과, 선택된 서비스, 기관 후보만 근거로 JSON 객체만 반환한다.

작성 원칙:
- 서비스명, 지원 내용, 자격, 금액, 문의처, URL은 제공된 데이터 밖에서 새로 만들지 않는다.
- 수급 가능성을 확정하지 말고 "확인 필요", "접수기관 심사 필요"라고 표현한다.
- 단순 서비스 목록이 아니라 실제 다음 행동이 보이는 추천서로 작성한다.
- servicePlans의 service 값은 반드시 selectedServices의 name 중 하나여야 한다.
- 문장은 짧고 현장 상담자가 읽기 쉬운 한국어로 쓴다.

반환 JSON 스키마:
{{
  "caseSummary": "사례 요약 2~3문장",
  "priorityAssessment": [{{"level": "긴급/주의/확인", "text": "판단 근거"}}],
  "reason": "패키지 전체 추천 이유",
  "servicePlans": [
    {{
      "service": "선택된 서비스명",
      "priority": "높음/중간/낮음",
      "purpose": "이 서비스가 맡는 역할",
      "whyRecommended": "상담 메모와 연결되는 추천 이유",
      "eligibilityToCheck": ["확인할 자격 조건"],
      "applicationPath": ["신청 또는 문의 순서"],
      "requiredDocs": ["준비 서류"],
      "contactAction": "문의할 때 할 말",
      "cautions": ["주의점"]
    }}
  ],
  "eligibilityChecklist": [{{"title": "체크 묶음", "items": ["확인 항목"]}}],
  "actionPlan": [{{"timing": "오늘/3일 이내/1~2주", "tasks": ["실행할 일"]}}],
  "providerPlan": [{{"name": "기관명", "reason": "연계 이유", "contactAction": "연락/확인 행동"}}],
  "followUpQuestions": ["추가 상담 질문"],
  "counselorScript": "대상자에게 설명할 문구",
  "caseNote": "내부 사례기록 문구",
  "dataLimitations": ["주의 또는 한계"]
}}

case:
{json.dumps(case, ensure_ascii=False)}

structured:
{json.dumps(structured, ensure_ascii=False)}

package:
{json.dumps({"title": package.get("title"), "summary": package.get("summary"), "score": package.get("score")}, ensure_ascii=False)}

selectedServices:
{json.dumps(selected_context, ensure_ascii=False)}

providers:
{json.dumps((providers or [])[:8], ensure_ascii=False)}

fallbackReport:
{json.dumps(fallback, ensure_ascii=False)}
"""
    try:
        data = b.call_gemini_json(prompt, temperature=0.15)
        service_plans = clean_service_plans(
            data.get("servicePlans"), allowed_names, fallback.get("servicePlans", [])
        )
        enhanced = {
            **fallback,
            "generatedBy": f"{b.GEMINI_MODEL}+rich-report-engine",
            "llmUsed": True,
            "caseSummary": compact_text(data.get("caseSummary") or fallback.get("caseSummary"), 620),
            "priorityAssessment": object_list(data.get("priorityAssessment"), 6)
            or fallback.get("priorityAssessment", []),
            "reason": compact_text(data.get("reason") or fallback.get("reason"), 620),
            "servicePlans": service_plans,
            "eligibilityChecklist": clean_checklist(
                data.get("eligibilityChecklist"), fallback.get("eligibilityChecklist", [])
            ),
            "actionPlan": clean_phase_list(data.get("actionPlan"), fallback.get("actionPlan", [])),
            "providerPlan": object_list(data.get("providerPlan"), 6) or fallback.get("providerPlan", []),
            "followUpQuestions": text_list(data.get("followUpQuestions"), 8, 180)
            or fallback.get("followUpQuestions", []),
            "counselorScript": compact_text(data.get("counselorScript") or fallback.get("counselorScript"), 500),
            "caseNote": compact_text(data.get("caseNote") or fallback.get("caseNote"), 500),
            "dataLimitations": text_list(data.get("dataLimitations"), 5, 200)
            or fallback.get("dataLimitations", []),
        }
        return enhanced
    except Exception as error:
        return {
            **fallback,
            "llmUsed": False,
            "llmError": compact_text(error, 180),
        }


RICH_REPORT_UI_JS = r"""
(function () {
  if (typeof state === "undefined" || typeof renderReportView !== "function") return;
  function addStyles() {
    if (document.querySelector("#rich-report-ui-patch")) return;
    const style = document.createElement("style");
    style.id = "rich-report-ui-patch";
    style.textContent = `
      .report-emphasis{border-color:#c8ddd7;background:#f5fbf9}
      .report-card-grid,.report-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
      .report-card-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
      .report-mini-card,.service-plan-card,.timeline-card{border:1px solid var(--line);border-radius:8px;background:var(--surface-2);padding:12px}
      .report-mini-card,.service-plan-card,.timeline-list,.service-plan-list{display:grid;gap:12px}
      .service-plan-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
      .service-plan-head div{display:grid;gap:4px}
      .report-mini-card span,.service-plan-card p,.timeline-card li,.service-plan-head span{color:var(--muted);line-height:1.55}
      .service-plan-card h4{margin:0 0 6px;font-size:13px}
      .service-plan-card ul,.timeline-card ul{margin:0;padding-left:18px}
      .empty-state.compact{min-height:auto;padding:10px;font-size:13px}
      .inline-link{color:#17645b;font-weight:800;text-decoration:underline;text-underline-offset:3px}
      .analyze-loading-note{margin-bottom:12px}
      .btn.is-loading,.icon-btn.is-loading{cursor:progress;opacity:.72}
      @media(max-width:900px){.report-card-grid,.report-grid-2{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }
  function arr(value) {
    return Array.isArray(value) ? value.filter(Boolean) : [];
  }
  function bullets(items) {
    const values = arr(items);
    if (!values.length) return `<div class="empty-state compact">표시할 항목이 없습니다.</div>`;
    return `<ul>${values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }
  function link(url, label = "공식 상세 페이지 열기") {
    const value = String(url || "").trim();
    if (!/^https?:\/\//i.test(value)) return escapeHtml(url || "");
    return `<a class="inline-link" href="${escapeHtml(value)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
  }
  function fallbackPlans(selectedServices) {
    return selectedServices.map((service) => ({
      service: service.name,
      priority: service.urgency === "긴급" ? "높음" : "중간",
      purpose: arr(service.domains).join(", ") || "지원 가능성 확인",
      whyRecommended: service.summary || "상담 메모와 연결되는 후보 서비스입니다.",
      eligibilityToCheck: [service.eligibility || "대상, 소득, 재산, 거주지 확인"],
      applicationPath: [service.process || "관할 기관 문의 후 접수 가능 여부 확인"],
      requiredDocs: service.docs || [],
      contactAction: service.contact || "공식 문의처 확인",
      cautions: ["최종 선정은 접수기관 심사로 결정됩니다."],
    }));
  }
  function priority(items) {
    const values = arr(items).length ? arr(items) : [{ level: "확인", text: "소득, 재산, 가구원, 거주지, 중복지원 여부를 확인한 뒤 판단합니다." }];
    return `<div class="report-card-grid">${values.map((item) => `<div class="report-mini-card"><strong>${escapeHtml(item.level || "확인")}</strong><span>${escapeHtml(item.text || "")}</span></div>`).join("")}</div>`;
  }
  function servicePlans(plans, selectedServices) {
    const values = arr(plans).length ? arr(plans) : fallbackPlans(selectedServices);
    return `<div class="service-plan-list">${values.map((plan) => `
      <article class="service-plan-card">
        <div class="service-plan-head">
          <div><strong>${escapeHtml(plan.service || "서비스")}</strong><span>${escapeHtml(plan.purpose || "지원 가능성 확인")}</span></div>
          ${pill(plan.priority || "중간", plan.priority === "높음" ? "amber" : "")}
        </div>
        <p>${escapeHtml(plan.whyRecommended || "")}</p>
        <div class="report-grid-2">
          <div><h4>확인 조건</h4>${bullets(plan.eligibilityToCheck)}</div>
          <div><h4>신청·문의 경로</h4>${bullets(plan.applicationPath)}</div>
          <div><h4>준비 서류</h4>${bullets(plan.requiredDocs)}</div>
          <div><h4>문의 액션</h4><p>${escapeHtml(plan.contactAction || "관할 기관 확인")}</p></div>
        </div>
        ${arr(plan.cautions).length ? `<div class="tiny">${escapeHtml(arr(plan.cautions).join(" / "))}</div>` : ""}
      </article>`).join("")}</div>`;
  }
  function actionPlan(plan) {
    const values = arr(plan);
    if (!values.length) return bullets([]);
    return `<div class="timeline-list">${values.map((phase) => `<div class="timeline-card"><strong>${escapeHtml(phase.timing || "확인")}</strong>${bullets(phase.tasks)}</div>`).join("")}</div>`;
  }
  function checklist(groups) {
    const values = arr(groups);
    if (!values.length) return bullets([]);
    return `<div class="report-card-grid">${values.map((group) => `<div class="report-mini-card"><strong>${escapeHtml(group.title || "확인")}</strong>${bullets(group.items)}</div>`).join("")}</div>`;
  }
  function providerPlan(plan) {
    const values = arr(plan);
    if (!values.length) return "";
    return `<section class="report-block"><h3>민간·지역기관 연계 계획</h3><div class="source-stack">${values.map((item) => `
      <div class="source-row">
        <div><strong>${escapeHtml(item.name || "연계기관")}</strong><div class="tiny">${escapeHtml(item.reason || "")}</div><div class="tiny">${escapeHtml(item.contactAction || "")}</div></div>
        ${pill("연계 후보", "blue")}
      </div>`).join("")}</div></section>`;
  }
  if (typeof copyReport === "function") {
    copyReport = function () {
      const { pkg, selectedServices, needs } = reportData();
      const report = state.lastReport;
      const plans = report?.servicePlans || fallbackPlans(selectedServices);
      const lines = report
        ? [
            `[추천 패키지] ${report.packageTitle}`,
            `대상/지역: ${state.case.targetType} / ${state.case.region || "미입력"}`,
            `핵심 욕구: ${arr(report.needs).join(", ")}`,
            "",
            "사례 요약",
            report.caseSummary || report.reason || "",
            "",
            "서비스별 실행계획",
            ...plans.flatMap((plan, index) => [
              `${index + 1}. ${plan.service} [${plan.priority}] ${plan.purpose}`,
              `   추천 이유: ${plan.whyRecommended}`,
              ...arr(plan.eligibilityToCheck).map((item) => `   확인: ${item}`),
              ...arr(plan.applicationPath).map((item) => `   경로: ${item}`),
              ...arr(plan.requiredDocs).map((item) => `   서류: ${item}`),
              `   문의: ${plan.contactAction || "관할 기관 확인"}`,
            ]),
            "",
            "단계별 실행계획",
            ...arr(report.actionPlan).flatMap((phase) => [`- ${phase.timing}`, ...arr(phase.tasks).map((task) => `  · ${task}`)]),
            "",
            "추가 상담 질문",
            ...arr(report.followUpQuestions).map((question) => `- ${question}`),
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
          ];
      navigator.clipboard?.writeText(lines.join("\n")).then(() => showToast("추천서 텍스트를 복사했습니다.")).catch(() => showToast("복사 권한을 확인해 주세요."));
    };
  }
  renderReportView = function () {
    if (!state.packages.length) generatePackagesLocal({ show: false });
    const { pkg, selectedServices, needs, contacts } = reportData();
    const report = state.lastReport;
    const reportNeeds = report?.needs || needs;
    const reportDocs = report?.docs || Array.from(new Set(selectedServices.flatMap((service) => service.docs || [])));
    const reportContacts = report?.contacts || contacts.map((service) => ({ service: service.name, contact: service.contact, url: service.url }));
    const reportCaseSummary = report?.caseSummary || `${state.case.targetType} / ${state.case.region || "지역 미입력"} 사례입니다. ${pkg.title}를 우선 검토합니다.`;
    const reportReason = report?.reason || `${pkg.summary}. 상담 메모에서 ${needs.join(", ")} 욕구가 확인되어 관련 제도와 기관을 조합했습니다.`;
    const priorityAssessment = report?.priorityAssessment || [{ level: state.case.urgency || "주의", text: "소득·재산·가구원·거주지 기준 확인 후 최종 판단합니다." }];
    const defaultAction = [
      { timing: "오늘", tasks: ["1순위 서비스 문의처와 신청 자격을 확인합니다.", "공통 증빙 자료 보유 여부를 점검합니다."] },
      { timing: "3일 이내", tasks: ["서비스별 접수기관과 신청 경로를 정리합니다.", "누락 서류와 중복지원 제한을 확인합니다."] },
      { timing: "1~2주", tasks: ["접수 결과와 보완 요청을 추적하고 대체 자원을 확인합니다."] },
    ];
    const defaultChecklist = [
      { title: "공통 확인", items: ["신분 확인", "가구 구성", "실거주지", "소득·재산 변동"] },
      { title: "신청 가능성", items: ["서비스별 대상 기준", "중복지원 제한", "관할기관 접수 가능 여부"] },
    ];
    const limits = report?.dataLimitations || ["추천서는 상담 보조 자료이며 최종 수급 가능성은 접수기관 심사로 결정됩니다.", "공공데이터와 기관 정보는 갱신 시점 차이가 있을 수 있어 신청 전 최신 공고를 확인합니다."];
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
              <div class="pill-row">${pill(state.case.urgency, state.case.urgency === "긴급" ? "red" : "amber")}${reportNeeds.map((need) => pill(need, needsColor(need))).join("")}</div>
              <h2>${escapeHtml(state.case.title)}</h2>
              <div class="muted">${escapeHtml(state.case.targetType)} · ${escapeHtml(state.case.region || "지역 미입력")} · ${new Date(report?.generatedAt || Date.now()).toLocaleDateString("ko-KR")}</div>
            </div>
            <div class="report-content">
              <section class="report-block report-emphasis"><h3>사례 요약</h3><p>${escapeHtml(reportCaseSummary)}</p></section>
              <section class="report-block"><h3>우선순위 판단</h3>${priority(priorityAssessment)}</section>
              <section class="report-block"><h3>추천 이유</h3><p>${escapeHtml(reportReason)}</p></section>
              <section class="report-block"><h3>서비스별 실행 계획</h3>${servicePlans(report?.servicePlans, selectedServices)}</section>
              <section class="report-block"><h3>신청 전 확인 체크리스트</h3>${checklist(report?.eligibilityChecklist || defaultChecklist)}</section>
              <section class="report-block"><h3>공통 준비 서류</h3><div class="pill-row">${reportDocs.map((doc) => pill(doc)).join("") || pill("서비스별 서류 확인")}</div></section>
              <section class="report-block"><h3>단계별 실행계획</h3>${actionPlan(report?.actionPlan || defaultAction)}</section>
              ${providerPlan(report?.providerPlan)}
              ${arr(report?.followUpQuestions).length ? `<section class="report-block"><h3>추가 상담 질문</h3>${bullets(report.followUpQuestions)}</section>` : ""}
              ${report?.counselorScript || report?.caseNote ? `<section class="report-block report-emphasis"><h3>설명·기록 문구</h3>${report?.counselorScript ? `<p><strong>대상자 설명:</strong> ${escapeHtml(report.counselorScript)}</p>` : ""}${report?.caseNote ? `<p><strong>사례기록:</strong> ${escapeHtml(report.caseNote)}</p>` : ""}</section>` : ""}
              <section class="report-block"><h3>문의처</h3><table class="contact-table"><thead><tr><th>서비스</th><th>문의처</th><th>URL</th></tr></thead><tbody>${reportContacts.map((contact) => `<tr><td>${escapeHtml(contact.service || "")}</td><td>${escapeHtml(contact.contact || "")}</td><td>${link(contact.detailUrl || contact.url, "열기")}</td></tr>`).join("")}</tbody></table></section>
              <section class="report-block"><h3>확인 필요 사항</h3>${bullets(limits)}</section>
            </div>
          </article>
        </div>
      </section>`;
  };

  function linkExistingUrlFields() {
    document.querySelectorAll(".detail-item").forEach((item) => {
      const title = item.querySelector("strong")?.textContent || "";
      const span = item.querySelector("span");
      if (!span || !title.includes("URL")) return;
      const url = span.textContent.trim();
      if (!/^https?:\/\//i.test(url)) return;
      span.innerHTML = link(url);
    });
  }

  function reflectAnalyzeLoading() {
    document.querySelectorAll('button[onclick*="inferStructure"]').forEach((button) => {
      button.disabled = Boolean(state.structureLoading);
      button.classList.toggle("is-loading", Boolean(state.structureLoading));
      if (state.structureLoading && !button.dataset.originalLabel) {
        button.dataset.originalLabel = button.innerHTML;
        button.innerHTML = `${icon("loader-circle")} AI 구조화 중`;
      } else if (!state.structureLoading && button.dataset.originalLabel) {
        button.innerHTML = button.dataset.originalLabel;
        delete button.dataset.originalLabel;
      }
    });

    document.querySelector(".analyze-loading-note")?.remove();
    if (state.structureLoading && state.view === "case") {
      const content = document.querySelector(".content");
      content?.insertAdjacentHTML(
        "afterbegin",
        `<div class="status-note green analyze-loading-note">${icon("loader-circle")}<span>${escapeHtml(state.structureLoadingText || "AI가 상담 메모를 구조화하고 있습니다. 잠시만 기다려 주세요.")}</span></div>`
      );
    }
    lucide?.createIcons?.();
  }

  if (!globalThis.__RICH_LINK_DOM_PATCHED) {
    globalThis.__RICH_LINK_DOM_PATCHED = true;
    const baseRender = render;
    render = function () {
      const result = baseRender();
      linkExistingUrlFields();
      reflectAnalyzeLoading();
      return result;
    };
  }

  if (!globalThis.__CASE_ANALYZE_LOADING_PATCHED) {
    globalThis.__CASE_ANALYZE_LOADING_PATCHED = true;
    state.structureLoading = false;
    state.structureLoadingText = "";
    state.structureLoadingToken = 0;
    const baseInferStructure = inferStructure;
    inferStructure = async function (options = {}) {
      if (state.structureLoading) {
        showToast("AI 구조화가 진행 중입니다. 잠시만 기다려 주세요.");
        return;
      }
      const token = (state.structureLoadingToken || 0) + 1;
      state.structureLoadingToken = token;
      state.structureLoading = true;
      state.structureLoadingText = "AI가 상담 메모를 구조화하고 있습니다. 잠시만 기다려 주세요.";
      render();
      try {
        return await baseInferStructure(options);
      } finally {
        if (state.structureLoadingToken === token) {
          state.structureLoading = false;
          state.structureLoadingText = "";
          render();
        }
      }
    };
  }

  addStyles();
})();
"""


def write_text_response(handler: Any, body: str, content_type: str) -> None:
    encoded = body.encode("utf-8")
    handler.send_response(b.HTTPStatus.OK)
    handler.send_header("Content-Type", f"{content_type}; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def install_ui_patch() -> None:
    native_do_get = b.WelfareHandler.do_GET

    def patched_do_get(self: Any) -> None:
        parsed = b.urlparse(self.path)
        if parsed.path == "/rich-report-ui-patch.js":
            return write_text_response(self, RICH_REPORT_UI_JS, "application/javascript")
        if parsed.path in {"/", "/index.html"}:
            html = (b.ROOT / "index.html").read_text(encoding="utf-8")
            tag = '<script src="/rich-report-ui-patch.js"></script>'
            if tag not in html:
                html = html.replace("</body>", f"  {tag}\n</body>")
            return write_text_response(self, html, "text/html")
        return native_do_get(self)

    b.WelfareHandler.do_GET = patched_do_get


def apply() -> None:
    global _ORIGINAL_BUILD_REPORT
    if getattr(b, "_RICH_REPORT_PATCHED", False):
        return

    _ORIGINAL_BUILD_REPORT = b.build_report

    def build_report(
        case: dict[str, Any],
        structured: dict[str, Any] | None,
        package: dict[str, Any],
        catalog: list[dict[str, Any]] | None = None,
        providers: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        base = _ORIGINAL_BUILD_REPORT(case, structured, package, catalog, providers)
        if base.get("servicePlans") and base.get("actionPlan") and base.get("caseSummary"):
            return base
        if not structured:
            structured = b.analyze_case(case)
        services = selected_services_for_package(package, catalog)
        fallback = build_default_report(base, case, structured, package, services, providers)
        return enhance_with_llm(fallback, case, structured, package, services, providers)

    b.build_report = build_report
    install_service_link_patch()
    install_ui_patch()
    b._RICH_REPORT_PATCHED = True
