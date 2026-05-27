from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import backend_server as b


DETAIL_BRIEF_CACHE: dict[str, dict[str, Any]] = {}
PACKAGE_RERANK_CACHE: dict[str, list[dict[str, Any]]] = {}
RELATED_PROVIDER_CACHE: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}

ENABLE_DETAIL_SUMMARY = os.getenv("ENABLE_LLM_DETAIL_SUMMARY", "true").lower() not in {"0", "false", "no"}
ENABLE_PACKAGE_RERANK = os.getenv("ENABLE_LLM_PACKAGE_RERANK", "true").lower() not in {"0", "false", "no"}
ENABLE_DETAIL_PROVIDERS = os.getenv("ENABLE_DETAIL_PROVIDERS", "true").lower() not in {"0", "false", "no"}
ENABLE_RICH_REPORT = os.getenv("ENABLE_LLM_RICH_REPORT", "true").lower() not in {"0", "false", "no"}


def compact_text(value: Any, limit: int = 360) -> str:
    text = b.clean_text(str(value or ""))
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def clean_list(values: Any, limit: int = 5, item_limit: int = 180) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        text = compact_text(value, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def stable_key(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def merge_structured_with_case(case: dict[str, Any], structured: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(structured or {})
    try:
        local = b.analyze_case_local(case)
    except Exception:
        local = {}

    needs = b.unique(
        [
            *(case.get("issueTypes") or []),
            *(local.get("needs") or []),
            *(result.get("needs") or []),
        ]
    )
    if needs:
        result["needs"] = needs[:7]

    keywords = b.unique([*(local.get("keywords") or []), *(result.get("keywords") or [])])
    if keywords:
        result["keywords"] = keywords[:12]

    if not result.get("target") and case.get("targetType"):
        result["target"] = case.get("targetType")
    if not result.get("region") and case.get("region"):
        result["region"] = case.get("region")
    if local.get("urgency") == "긴급" and result.get("urgency") != "긴급":
        result["urgency"] = "긴급"
    elif not result.get("urgency"):
        result["urgency"] = case.get("urgency") or local.get("urgency") or "주의"

    risk_checks = b.unique([*(result.get("riskChecks") or []), *(local.get("riskChecks") or [])])
    if risk_checks:
        result["riskChecks"] = risk_checks[:6]
    return result


def service_context(service: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": service.get("id", ""),
        "externalId": service.get("externalId", ""),
        "name": service.get("name", ""),
        "source": service.get("source", ""),
        "region": service.get("region", ""),
        "target": service.get("target", ""),
        "domains": service.get("domains", []),
        "urgency": service.get("urgency", ""),
        "summary": compact_text(service.get("summary", ""), 520),
        "eligibility": compact_text(service.get("eligibility", ""), 520),
        "selectionCriteria": compact_text(service.get("selectionCriteria", ""), 420),
        "support": compact_text(service.get("support", ""), 520),
        "process": compact_text(service.get("process", ""), 420),
        "docs": clean_list(service.get("docs", []), limit=8, item_limit=120),
        "contact": compact_text(service.get("contact", ""), 180),
        "url": compact_text(service.get("url", ""), 220),
        "laws": clean_list(service.get("laws", []), limit=5, item_limit=120),
    }


def fallback_detail_brief(service: dict[str, Any]) -> dict[str, Any]:
    points = []
    if service.get("eligibility"):
        points.append(f"대상: {compact_text(service.get('eligibility'), 130)}")
    if service.get("support"):
        points.append(f"지원: {compact_text(service.get('support'), 130)}")
    if service.get("process"):
        points.append(f"신청: {compact_text(service.get('process'), 130)}")
    if not points and service.get("summary"):
        points.append(compact_text(service.get("summary"), 150))

    checks = []
    if service.get("selectionCriteria"):
        checks.append(compact_text(service.get("selectionCriteria"), 130))
    if service.get("docs"):
        checks.append(f"서류: {compact_text(', '.join(service.get('docs', [])[:4]), 130)}")
    if service.get("contact"):
        checks.append(f"문의처: {compact_text(service.get('contact'), 130)}")

    return {
        "headline": compact_text(service.get("summary") or service.get("name") or "서비스 기본 정보를 확인하세요.", 92),
        "keyPoints": points[:4],
        "checkBeforeApply": checks[:4] or ["소득·재산·연령·거주지 기준은 신청 전 재확인 필요"],
        "caseworkerNote": "상세 원문과 관할 기관 기준을 함께 확인한 뒤 연계 여부를 판단하세요.",
        "generatedBy": "rule-detail-summary",
        "llmUsed": False,
    }


def summarize_detail(service: dict[str, Any]) -> dict[str, Any]:
    key = stable_key("detail", service_context(service))
    if key in DETAIL_BRIEF_CACHE:
        return dict(DETAIL_BRIEF_CACHE[key])

    fallback = fallback_detail_brief(service)
    if not ENABLE_DETAIL_SUMMARY or not b.GEMINI_API_KEY:
        DETAIL_BRIEF_CACHE[key] = fallback
        return dict(fallback)

    prompt = f"""
너는 한국 복지 현장 종사자가 공공데이터 상세조회 원문을 빠르게 검토하도록 돕는 보조자다.
아래 서비스 데이터에 근거해서 JSON 객체만 반환한다.

엄격한 규칙:
- 제공된 데이터에 없는 혜택, 금액, 자격, 연락처, URL을 만들지 않는다.
- 신청 가능 여부를 확정하지 말고 "확인 필요" 표현을 사용한다.
- 현장 종사자가 먼저 볼 핵심만 간결하게 정리한다.
- 각 배열은 최대 4개, 각 문장은 80자 안팎으로 작성한다.

반환 JSON 스키마:
{{
  "headline": "한 줄 요약",
  "keyPoints": ["지원대상/지원내용/신청방법 핵심"],
  "checkBeforeApply": ["신청 전 확인할 조건 또는 서류"],
  "caseworkerNote": "상담자가 기록에 남길 짧은 확인 메모"
}}

서비스 데이터:
{json.dumps(service_context(service), ensure_ascii=False)}
"""
    try:
        data = b.call_gemini_json(prompt, temperature=0.1)
        brief = {
            "headline": compact_text(data.get("headline") or fallback["headline"], 110),
            "keyPoints": clean_list(data.get("keyPoints"), limit=4, item_limit=120) or fallback["keyPoints"],
            "checkBeforeApply": clean_list(data.get("checkBeforeApply"), limit=4, item_limit=120)
            or fallback["checkBeforeApply"],
            "caseworkerNote": compact_text(data.get("caseworkerNote") or fallback["caseworkerNote"], 150),
            "generatedBy": f"{b.GEMINI_MODEL}+detail-summary",
            "llmUsed": True,
        }
    except Exception as error:
        brief = {**fallback, "llmError": compact_text(error, 120)}

    DETAIL_BRIEF_CACHE[key] = brief
    return dict(brief)


def provider_query_for_detail(service: dict[str, Any]) -> dict[str, list[str]]:
    domains = service.get("domains") or []
    preferred_domain = next((domain for domain in domains if domain in {"돌봄", "심리", "안전", "의료", "생계", "주거"}), "전체")
    query_word = service.get("name", "") if service.get("source") in {"기관", "민간"} else preferred_domain
    if query_word == "전체":
        query_word = ""
    return {
        "q": [query_word],
        "domain": [preferred_domain],
        "needs": [",".join(domains)],
        "region": [service.get("region", "")],
        "numOfRows": ["5"],
    }


def should_attach_providers(service: dict[str, Any], meta: dict[str, Any]) -> bool:
    if not ENABLE_DETAIL_PROVIDERS:
        return False
    if service.get("source") in {"기관", "민간"}:
        return True
    if meta.get("reason") in {"unsupported_service_source", "external_portal_detail"}:
        return True
    return bool({"돌봄", "심리", "안전", "의료"} & set(service.get("domains") or []))


def attach_related_providers(service: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    if not should_attach_providers(service, meta):
        return service
    query = provider_query_for_detail(service)
    key = stable_key("providers", query)
    try:
        if key in RELATED_PROVIDER_CACHE:
            providers, provider_meta = RELATED_PROVIDER_CACHE[key]
        else:
            providers, provider_meta = b.fetch_providers(query)
            RELATED_PROVIDER_CACHE[key] = (providers[:5], provider_meta)
        return {**service, "relatedProviders": providers[:5], "relatedProvidersMeta": provider_meta}
    except Exception as error:
        return {**service, "relatedProviders": [], "relatedProvidersMeta": {"fallback": True, "errors": [compact_text(error, 120)]}}


def package_candidate_context(service: dict[str, Any], score: int) -> dict[str, Any]:
    context = service_context(service)
    return {
        "id": context["id"],
        "name": context["name"],
        "source": context["source"],
        "target": context["target"],
        "region": context["region"],
        "domains": context["domains"],
        "urgency": context["urgency"],
        "summary": context["summary"],
        "eligibility": context["eligibility"],
        "support": context["support"],
        "score": score,
    }


def ranked_candidates(
    case: dict[str, Any], structured: dict[str, Any], catalog: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    source_catalog = b.unique_services(list(catalog or b.SERVICES))
    compatible_catalog = []
    for service in source_catalog:
        try:
            if b.target_compatible(service, case, structured):
                compatible_catalog.append(service)
        except Exception:
            continue
    needs = structured.get("needs") or case.get("issueTypes") or []

    scored: list[tuple[int, dict[str, Any]]] = []
    for service in compatible_catalog:
        try:
            score = b.service_score(service, needs, case, structured)
        except Exception:
            score = 0
        if score > 0:
            scored.append((score, service))

    scored.sort(key=lambda item: item[0], reverse=True)
    regional = [
        (max(score, 1), service)
        for score, service in scored
        if service.get("source") in {"기관", "민간", "지자체"}
    ]
    combined = b.unique_services([service for _score, service in [*scored[:14], *regional[:6]]])
    if len(combined) < 8:
        combined = b.unique_services([*combined, *compatible_catalog])[:18]
    return combined[:18]


def fill_package_items(
    chosen: list[dict[str, Any]], candidates: list[dict[str, Any]], case: dict[str, Any], structured: dict[str, Any]
) -> list[dict[str, Any]]:
    needs = structured.get("needs") or case.get("issueTypes") or []
    selected = b.unique_services(chosen)
    selected_ids = {item.get("id") for item in selected}
    domains = {domain for service in selected for domain in service.get("domains", [])}
    for need in needs[:4]:
        if need in domains:
            continue
        found = next(
            (
                service
                for service in candidates
                if service.get("id") not in selected_ids and need in (service.get("domains") or [])
            ),
            None,
        )
        if found:
            selected.append(found)
            selected_ids.add(found.get("id"))
            domains.update(found.get("domains") or [])
    while len(selected) < 3:
        found = next((service for service in candidates if service.get("id") not in selected_ids), None)
        if not found:
            break
        selected.append(found)
        selected_ids.add(found.get("id"))
    return selected[:5]


def rerank_packages_with_llm(
    case: dict[str, Any],
    structured: dict[str, Any],
    catalog: list[dict[str, Any]] | None,
    fallback_packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not ENABLE_PACKAGE_RERANK or not b.GEMINI_API_KEY:
        return fallback_packages

    candidates = ranked_candidates(case, structured, catalog)
    if len(candidates) < 3:
        return fallback_packages

    needs = structured.get("needs") or case.get("issueTypes") or []
    scored_context = [
        package_candidate_context(service, b.service_score(service, needs, case, structured))
        for service in candidates
    ]
    cache_key = stable_key(
        "packages",
        {
            "case": case,
            "structured": structured,
            "candidateIds": [service.get("id") for service in candidates],
        },
    )
    if cache_key in PACKAGE_RERANK_CACHE:
        return [dict(package) for package in PACKAGE_RERANK_CACHE[cache_key]]

    prompt = f"""
너는 한국 복지 현장 종사자용 추천 시스템의 재정렬 엔진이다.
아래 상담 정보와 후보 서비스 목록만 사용해서 JSON 객체만 반환한다.

엄격한 규칙:
- 후보 목록에 있는 id만 사용한다. 새 서비스나 제도명을 만들지 않는다.
- 상담 대상 연령·상황과 맞지 않는 서비스는 제외한다.
- 같은 긴급복지 계열만 반복하지 말고, 실제 메모의 욕구를 나누어 조합한다.
- 민간/기관/지자체 후보가 상담 맥락에 맞으면 적어도 한 패키지에 포함한다.
- 각 패키지는 3~5개 서비스로 구성한다.

반환 JSON 스키마:
{{
  "packages": [
    {{
      "title": "패키지명",
      "summary": "추천 이유 한 문장",
      "score": 80,
      "serviceIds": ["후보 id"]
    }}
  ]
}}

상담:
{json.dumps(case, ensure_ascii=False)}

구조화 결과:
{json.dumps(structured, ensure_ascii=False)}

기존 규칙 기반 패키지:
{json.dumps(fallback_packages, ensure_ascii=False)}

후보 서비스:
{json.dumps(scored_context, ensure_ascii=False)}
"""
    data = b.call_gemini_json(prompt, temperature=0.15)
    raw_packages = data.get("packages") if isinstance(data, dict) else None
    if not isinstance(raw_packages, list):
        return fallback_packages

    candidate_map = {service.get("id"): service for service in candidates}
    built: list[dict[str, Any]] = []
    used_signatures = set()
    for index, item in enumerate(raw_packages[:3], start=1):
        if not isinstance(item, dict):
            continue
        service_ids = [str(service_id) for service_id in item.get("serviceIds", []) if str(service_id) in candidate_map]
        chosen = [candidate_map[service_id] for service_id in b.unique(service_ids)]
        chosen = fill_package_items(chosen, candidates, case, structured)
        if len(chosen) < 2:
            continue
        signature = tuple(service.get("id") for service in chosen)
        if signature in used_signatures:
            continue
        used_signatures.add(signature)
        score = item.get("score", 88 - ((index - 1) * 5))
        try:
            score = max(70, min(98, int(score)))
        except Exception:
            score = 88 - ((index - 1) * 5)
        package = b.build_package(
            f"pkg-{index}",
            compact_text(item.get("title") or fallback_packages[index - 1].get("title") or f"추천 패키지 {index}", 34),
            compact_text(item.get("summary") or fallback_packages[index - 1].get("summary") or "상담 메모 기반 조합", 90),
            chosen,
            score,
        )
        package["provider"] = f"{b.GEMINI_MODEL}+candidate-rerank"
        package["llmUsed"] = True
        built.append(package)

    for fallback in fallback_packages:
        if len(built) >= 3:
            break
        fallback_ids = tuple(item.get("serviceId") for item in fallback.get("items", []))
        if fallback_ids in used_signatures:
            continue
        built.append({**fallback, "id": f"pkg-{len(built) + 1}"})

    if not built:
        return fallback_packages
    PACKAGE_RERANK_CACHE[cache_key] = [dict(package) for package in built[:3]]
    return built[:3]


def selected_services_for_report(package: dict[str, Any], catalog: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    selected = []
    for item in package.get("items", []):
        service_id = item.get("serviceId", "")
        if not item.get("included", True) or not service_id:
            continue
        service = b.find_service(service_id, catalog)
        if service:
            selected.append(service)
    return b.unique_services(selected)


def service_report_context(service: dict[str, Any]) -> dict[str, Any]:
    context = service_context(service)
    brief = service.get("detailBrief") or {}
    return {
        **context,
        "detailHeadline": compact_text(brief.get("headline", ""), 160) if isinstance(brief, dict) else "",
        "detailKeyPoints": clean_list(brief.get("keyPoints", []), limit=4) if isinstance(brief, dict) else [],
    }


def provider_report_context(providers: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result = []
    for provider in providers or []:
        result.append(
            {
                "name": compact_text(provider.get("name", ""), 100),
                "source": compact_text(provider.get("source", ""), 60),
                "serviceName": compact_text(provider.get("serviceName") or provider.get("serviceType") or "", 140),
                "region": compact_text(provider.get("region", ""), 80),
                "address": compact_text(provider.get("address", ""), 160),
                "contact": compact_text(provider.get("contact", ""), 100),
            }
        )
        if len(result) >= 8:
            break
    return result


def infer_service_purpose(service: dict[str, Any]) -> str:
    domains = service.get("domains") or []
    if "의료" in domains:
        return "의료비와 치료 접근성 확인"
    if "돌봄" in domains:
        return "일상 돌봄 공백 보완"
    if "주거" in domains:
        return "주거비·거처 안정 확인"
    if "생계" in domains:
        return "단기 생계 안정"
    if "심리" in domains:
        return "정서 안정과 위기상담 연계"
    if "취업" in domains:
        return "자립·구직 경로 연결"
    return "상담 욕구와 관련된 지원 가능성 확인"


def risk_alerts_from_structured(case: dict[str, Any], structured: dict[str, Any]) -> list[dict[str, str]]:
    alerts = []
    urgency = structured.get("urgency") or case.get("urgency") or "주의"
    if urgency == "긴급":
        alerts.append({"level": "긴급", "text": "위기 신호가 있어 생계·주거·안전 위험을 우선 확인합니다."})
    for check in structured.get("riskChecks") or []:
        if isinstance(check, dict) and check.get("text"):
            alerts.append(
                {
                    "level": compact_text(check.get("label") or "확인 필요", 28),
                    "text": compact_text(check.get("text"), 180),
                }
            )
        if len(alerts) >= 4:
            break
    if not alerts:
        alerts.append({"level": "일반", "text": "신청 가능성은 소득·재산·거주지·연령 기준 확인 후 판단합니다."})
    return alerts


def default_service_plans(selected_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plans = []
    for index, service in enumerate(selected_services, start=1):
        docs = clean_list(service.get("docs", []), limit=5, item_limit=80)
        checks = clean_list(
            [
                service.get("eligibility", ""),
                service.get("selectionCriteria", ""),
                "소득·재산·연령·거주지 기준 확인 필요",
            ],
            limit=4,
            item_limit=130,
        )
        plans.append(
            {
                "service": service.get("name", ""),
                "priority": "높음" if index <= 2 or service.get("urgency") == "긴급" else "중간",
                "purpose": infer_service_purpose(service),
                "whyRecommended": compact_text(
                    service.get("summary") or "상담 메모의 핵심 욕구와 연결되는 서비스입니다.", 180
                ),
                "eligibilityToCheck": checks,
                "applicationPath": clean_list([service.get("process", "")], limit=3, item_limit=150),
                "requiredDocs": docs or ["신분증", "소득·재산 관련 증빙", "서비스별 추가 서류"],
                "contactAction": compact_text(service.get("contact") or service.get("url") or "관할 기관 문의", 130),
                "cautions": ["수급 가능 여부는 접수기관 심사와 최신 기준 확인 후 판단합니다."],
            }
        )
    return plans


def default_action_plan(
    case: dict[str, Any],
    structured: dict[str, Any],
    selected_services: list[dict[str, Any]],
    providers: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    primary = selected_services[0] if selected_services else {}
    primary_contact = primary.get("contact") or primary.get("url") or "관할 읍면동/서비스 담당 기관"
    plan = [
        {
            "timing": "오늘",
            "tasks": [
                "현재 위험 수준과 즉시 필요한 생계·주거·의료·안전 조치를 확인합니다.",
                f"{primary.get('name', '1순위 서비스')} 접수 가능성과 문의처({compact_text(primary_contact, 80)})를 확인합니다.",
            ],
        },
        {
            "timing": "3일 이내",
            "tasks": [
                "소득·재산·거주·가구구성·연령 등 공통 자격 확인 자료를 정리합니다.",
                "패키지에 포함된 서비스별 신청 경로와 중복 가능성을 담당 기관에 확인합니다.",
            ],
        },
        {
            "timing": "1~2주",
            "tasks": [
                "접수 결과, 보완서류, 서비스 제공 여부를 점검하고 필요 시 대체 자원을 연결합니다.",
                "위기 재발 가능성이 있으면 통합사례관리 또는 지역기관 모니터링 계획을 세웁니다.",
            ],
        },
    ]
    if providers:
        provider = providers[0]
        plan[1]["tasks"].append(
            f"지역 연계 후보({provider.get('name', '기관')})의 서비스 범위와 이용 가능 여부를 확인합니다."
        )
    if structured.get("urgency") == "긴급" or case.get("urgency") == "긴급":
        plan[0]["tasks"].insert(0, "안전·의료·주거 상실 위험이 있으면 112/119/129 또는 관할 긴급지원 창구를 우선 연결합니다.")
    return plan


def default_checklist(case: dict[str, Any], structured: dict[str, Any]) -> list[dict[str, Any]]:
    needs = structured.get("needs") or case.get("issueTypes") or []
    checklist = [
        {"title": "공통 확인", "items": ["신분 확인", "주민등록상 주소와 실거주지", "가구원 구성", "소득·재산 변동"]},
        {"title": "신청 가능성", "items": ["서비스별 연령·대상 기준", "중복 수급 제한", "최근 지원 이력", "관할 기관 접수 가능 여부"]},
    ]
    if "의료" in needs:
        checklist.append({"title": "의료", "items": ["진단/진료 내역", "의료비 영수증", "보험·본인부담 상태", "치료 지속 필요성"]})
    if "주거" in needs:
        checklist.append({"title": "주거", "items": ["임대차계약", "체납·퇴거 위험", "주거 형태", "공공임대 이전 의향"]})
    if "돌봄" in needs:
        checklist.append({"title": "돌봄", "items": ["일상생활 수행 어려움", "보호자 지원 가능성", "방문 서비스 필요 시간", "안전 위험"]})
    if "생계" in needs:
        checklist.append({"title": "생계", "items": ["최근 소득 감소", "식비·공과금 부담", "기존 수급 여부", "긴급 지출 항목"]})
    return checklist[:6]


def default_provider_plan(providers: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    plan = []
    for provider in providers or []:
        plan.append(
            {
                "name": compact_text(provider.get("name", "지역 기관"), 90),
                "reason": compact_text(provider.get("serviceName") or provider.get("serviceType") or "지역 연계 가능성 확인", 120),
                "contactAction": compact_text(
                    " / ".join([provider.get("contact", ""), provider.get("address", "")]).strip(" / ")
                    or "이용 가능 여부 문의",
                    160,
                ),
            }
        )
        if len(plan) >= 5:
            break
    return plan


def default_follow_up_questions(needs: list[str]) -> list[str]:
    questions = [
        "최근 3개월 소득·재산·가구구성 변화가 있었나요?",
        "이미 신청했거나 받고 있는 유사 급여가 있나요?",
        "접수기관에 제출 가능한 증빙자료가 준비되어 있나요?",
    ]
    if "주거" in needs:
        questions.append("임대료 체납, 퇴거 통보, 주거 형태를 확인했나요?")
    if "의료" in needs:
        questions.append("진단명, 치료 일정, 진료비 내역, 본인부담 상태를 확인했나요?")
    if "돌봄" in needs:
        questions.append("식사, 이동, 복약, 안전 확인 중 어느 돌봄 공백이 가장 큰가요?")
    return questions[:7]


def build_default_rich_report(
    case: dict[str, Any],
    structured: dict[str, Any],
    package: dict[str, Any],
    selected_services: list[dict[str, Any]],
    providers: list[dict[str, Any]] | None,
    base_report: dict[str, Any],
) -> dict[str, Any]:
    needs = structured.get("needs") or case.get("issueTypes") or []
    service_names = ", ".join(service.get("name", "") for service in selected_services[:3] if service.get("name"))
    case_summary = compact_text(
        f"{case.get('targetType', '대상자')} / {case.get('region', '지역 미입력')} 사례입니다. "
        f"상담 메모에서 {', '.join(needs) or '복지'} 욕구가 확인되어 {package.get('title', '추천 패키지')}를 우선 검토합니다.",
        260,
    )
    rich = {
        **base_report,
        "generatedBy": base_report.get("generatedBy", "backend-report-engine"),
        "caseSummary": case_summary,
        "priorityAssessment": risk_alerts_from_structured(case, structured),
        "servicePlans": default_service_plans(selected_services),
        "actionPlan": default_action_plan(case, structured, selected_services, providers),
        "eligibilityChecklist": default_checklist(case, structured),
        "providerPlan": default_provider_plan(providers),
        "followUpQuestions": default_follow_up_questions(needs),
        "counselorScript": compact_text(
            f"현재 상황에서는 {service_names or '선택한 서비스'}를 우선 확인하고, 신청 가능성은 소득·재산·거주지 기준을 확인한 뒤 판단하겠습니다.",
            220,
        ),
        "caseNote": base_report.get("caseNote")
        or compact_text(
            f"{case.get('targetType', '대상자')} 사례로 {', '.join(needs) or '복지'} 욕구가 확인됨. "
            f"{package.get('title', '추천 패키지')} 중심으로 공공제도와 지역기관 연계 가능성을 검토함.",
            260,
        ),
        "dataLimitations": [
            "본 추천서는 상담 보조 자료이며 최종 수급 가능 여부는 접수기관 심사로 확인합니다.",
            "공공데이터 기준일과 관할 지자체 운영 기준이 다를 수 있어 신청 전 최신 공고를 확인합니다.",
            "LLM은 제공된 서비스·기관 데이터 범위 안에서 문장을 정리하며 새 제도를 생성하지 않습니다.",
        ],
    }
    return rich


def validate_service_plans(plans: Any, selected_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {service.get("name", ""): service for service in selected_services}
    result = []
    if not isinstance(plans, list):
        return result
    for item in plans:
        if not isinstance(item, dict):
            continue
        service_name = clean_report_text(item.get("service"), 120)
        if service_name not in allowed:
            continue
        result.append(
            {
                "service": service_name,
                "priority": clean_report_text(item.get("priority") or "중간", 20),
                "purpose": clean_report_text(item.get("purpose"), 120),
                "whyRecommended": clean_report_text(item.get("whyRecommended"), 220),
                "eligibilityToCheck": clean_list(item.get("eligibilityToCheck"), limit=5, item_limit=130),
                "applicationPath": clean_list(item.get("applicationPath"), limit=4, item_limit=140),
                "requiredDocs": clean_list(item.get("requiredDocs"), limit=6, item_limit=80),
                "contactAction": clean_report_text(item.get("contactAction"), 160),
                "cautions": clean_list(item.get("cautions"), limit=3, item_limit=120),
            }
        )
        if len(result) >= len(selected_services):
            break
    return result


def clean_report_text(value: Any, limit: int = 240) -> str:
    return compact_text(value, limit)


def clean_named_list(values: Any, name_key: str = "title", items_key: str = "items", limit: int = 6) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if not isinstance(value, dict):
            continue
        title = clean_report_text(value.get(name_key) or value.get("timing") or value.get("level") or value.get("name"), 80)
        raw_items = value.get(items_key)
        if isinstance(raw_items, str):
            raw_items = [raw_items]
        if not raw_items:
            raw_items = value.get("tasks")
        if isinstance(raw_items, str):
            raw_items = [raw_items]
        if not raw_items:
            raw_items = [value.get("text", "")]
        items = clean_list(raw_items, limit=6, item_limit=150)
        if title and items:
            normalized = {name_key: title, items_key: items}
            if "timing" in value:
                normalized = {"timing": title, "tasks": items}
            if "level" in value:
                normalized = {"level": title, "text": items[0]}
            result.append(normalized)
        if len(result) >= limit:
            break
    return result


def enhance_report_with_llm(
    case: dict[str, Any],
    structured: dict[str, Any],
    package: dict[str, Any],
    selected_services: list[dict[str, Any]],
    providers: list[dict[str, Any]] | None,
    report: dict[str, Any],
) -> dict[str, Any]:
    if not ENABLE_RICH_REPORT or not b.GEMINI_API_KEY or not selected_services:
        return report

    prompt = f"""
너는 한국 복지 현장 종사자가 대상자 설명과 사례기록에 함께 쓸 수 있는 복지 추천서를 작성하는 보조자다.
아래 데이터에 근거해서 JSON 객체만 반환한다.

도메인 원칙:
- 복지멤버십/보조금24처럼 받을 가능성이 있는 서비스를 안내하되, 신청 가능성을 확정하지 않는다.
- 통합사례관리 관점에서 욕구, 위험, 서비스 제공계획, 점검·사후관리를 분리한다.
- 공공지원과 민간·지역기관 연계를 함께 제안한다.

엄격한 규칙:
- 제공된 서비스/기관 데이터에 없는 제도명, 혜택, 금액, 자격, 연락처를 만들지 않는다.
- servicePlans.service는 반드시 선택 서비스명 중 하나만 사용한다.
- 민감정보를 새로 쓰지 않는다.
- 각 문장은 실무자가 읽기 쉬운 짧은 문장으로 쓴다.
- 모든 판단은 \"확인 필요\"로 표현한다.

반환 JSON 스키마:
{{
  "caseSummary": "사례 요약 2~3문장",
  "reason": "패키지 추천 이유 3~5문장",
  "priorityAssessment": [{{"level": "긴급/높음/중간/확인", "text": "우선 확인할 위험"}}],
  "servicePlans": [
    {{
      "service": "선택 서비스명",
      "priority": "높음/중간/보조",
      "purpose": "이 서비스의 역할",
      "whyRecommended": "상담 메모와 연결되는 근거",
      "eligibilityToCheck": ["확인 조건"],
      "applicationPath": ["신청 또는 문의 단계"],
      "requiredDocs": ["준비 서류"],
      "contactAction": "문의처 활용 방법",
      "cautions": ["주의 사항"]
    }}
  ],
  "actionPlan": [{{"timing": "오늘/3일 이내/1~2주", "tasks": ["실행 과업"]}}],
  "eligibilityChecklist": [{{"title": "확인 묶음", "items": ["확인 항목"]}}],
  "providerPlan": [{{"name": "기관명", "reason": "연계 이유", "contactAction": "문의 방법"}}],
  "followUpQuestions": ["추가 상담 질문"],
  "counselorScript": "대상자에게 설명할 짧은 문장",
  "caseNote": "사례기록에 붙여넣을 문장",
  "dataLimitations": ["확인 필요/한계"]
}}

상담:
{json.dumps(case, ensure_ascii=False)}

구조화 결과:
{json.dumps(structured, ensure_ascii=False)}

선택 패키지:
{json.dumps(package, ensure_ascii=False)}

선택 서비스 데이터:
{json.dumps([service_report_context(service) for service in selected_services], ensure_ascii=False)}

기관 후보:
{json.dumps(provider_report_context(providers), ensure_ascii=False)}

기본 추천서:
{json.dumps(report, ensure_ascii=False)}
"""
    data = b.call_gemini_json(prompt, temperature=0.18)
    enhanced = dict(report)
    if isinstance(data.get("caseSummary"), str):
        enhanced["caseSummary"] = clean_report_text(data["caseSummary"], 360)
    if isinstance(data.get("reason"), str):
        enhanced["reason"] = clean_report_text(data["reason"], 560)
    priority = clean_named_list(data.get("priorityAssessment"), name_key="level", items_key="text", limit=4)
    if priority:
        enhanced["priorityAssessment"] = priority
    service_plans = validate_service_plans(data.get("servicePlans"), selected_services)
    if service_plans:
        enhanced["servicePlans"] = service_plans
    action_plan = clean_named_list(data.get("actionPlan"), name_key="timing", items_key="tasks", limit=4)
    if action_plan:
        enhanced["actionPlan"] = action_plan
    checklist = clean_named_list(data.get("eligibilityChecklist"), name_key="title", items_key="items", limit=6)
    if checklist:
        enhanced["eligibilityChecklist"] = checklist
    provider_plan = []
    if isinstance(data.get("providerPlan"), list):
        for item in data["providerPlan"]:
            if not isinstance(item, dict):
                continue
            provider_plan.append(
                {
                    "name": clean_report_text(item.get("name"), 90),
                    "reason": clean_report_text(item.get("reason"), 140),
                    "contactAction": clean_report_text(item.get("contactAction"), 160),
                }
            )
            if len(provider_plan) >= 5:
                break
    if provider_plan:
        enhanced["providerPlan"] = provider_plan
    follow_up = clean_list(data.get("followUpQuestions"), limit=8, item_limit=130)
    if follow_up:
        enhanced["followUpQuestions"] = follow_up
    for field, limit in [
        ("counselorScript", 280),
        ("caseNote", 360),
    ]:
        if isinstance(data.get(field), str):
            enhanced[field] = clean_report_text(data[field], limit)
    limitations = clean_list(data.get("dataLimitations"), limit=4, item_limit=150)
    if limitations:
        enhanced["dataLimitations"] = limitations
    enhanced["generatedBy"] = f"{b.GEMINI_MODEL}+rich-report-engine"
    enhanced["llmUsed"] = True
    return enhanced


def install_detail_wrapper() -> None:
    if getattr(b, "_LLM_ENHANCEMENT_DETAIL_WRAPPED", False):
        return
    original = b.fetch_public_welfare_detail
    b._LLM_ENHANCEMENT_ORIGINAL_DETAIL_FETCH = original

    def fetch_public_welfare_detail(service: dict[str, Any]):
        detail, meta = original(service)
        enriched = {**detail, "detailBrief": summarize_detail(detail)}
        enriched = attach_related_providers(enriched, meta)
        return enriched, meta

    b.fetch_public_welfare_detail = fetch_public_welfare_detail
    b._LLM_ENHANCEMENT_DETAIL_WRAPPED = True


def install_package_wrapper() -> None:
    if getattr(b, "_LLM_ENHANCEMENT_PACKAGE_WRAPPED", False):
        return
    original = b.generate_packages
    b._LLM_ENHANCEMENT_ORIGINAL_GENERATE_PACKAGES = original

    def generate_packages(
        case: dict[str, Any], structured: dict[str, Any] | None, catalog: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        structured_result = merge_structured_with_case(case, structured or b.analyze_case(case))
        fallback_packages = original(case, structured_result, catalog)
        try:
            return rerank_packages_with_llm(case, structured_result, catalog, fallback_packages)
        except Exception:
            return fallback_packages

    b.generate_packages = generate_packages
    b._LLM_ENHANCEMENT_PACKAGE_WRAPPED = True


def install_analyze_wrapper() -> None:
    if getattr(b, "_LLM_ENHANCEMENT_ANALYZE_WRAPPED", False):
        return
    original = b.analyze_case
    b._LLM_ENHANCEMENT_ORIGINAL_ANALYZE_CASE = original

    def analyze_case(case: dict[str, Any]) -> dict[str, Any]:
        structured = original(case)
        return merge_structured_with_case(case, structured)

    b.analyze_case = analyze_case
    b._LLM_ENHANCEMENT_ANALYZE_WRAPPED = True


def install_report_wrapper() -> None:
    if getattr(b, "_LLM_ENHANCEMENT_REPORT_WRAPPED", False):
        return
    original = b.build_report
    b._LLM_ENHANCEMENT_ORIGINAL_BUILD_REPORT = original

    def build_report(
        case: dict[str, Any],
        structured: dict[str, Any] | None,
        package: dict[str, Any],
        catalog: list[dict[str, Any]] | None = None,
        providers: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        structured_result = merge_structured_with_case(case, structured or b.analyze_case(case))
        base_report = original(case, structured_result, package, catalog, providers)
        selected_services = selected_services_for_report(package, catalog)
        rich_report = build_default_rich_report(
            case,
            structured_result,
            package,
            selected_services,
            providers,
            base_report,
        )
        try:
            return enhance_report_with_llm(case, structured_result, package, selected_services, providers, rich_report)
        except Exception:
            rich_report["llmError"] = True
            return rich_report

    b.build_report = build_report
    b._LLM_ENHANCEMENT_REPORT_WRAPPED = True


def apply() -> None:
    if hasattr(b, "analyze_case"):
        install_analyze_wrapper()
    if hasattr(b, "fetch_public_welfare_detail"):
        install_detail_wrapper()
    if hasattr(b, "generate_packages"):
        install_package_wrapper()
    if hasattr(b, "build_report"):
        install_report_wrapper()
    b.LLM_ENHANCEMENT_PATCH_APPLIED = True
