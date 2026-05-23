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


def apply() -> None:
    if hasattr(b, "analyze_case"):
        install_analyze_wrapper()
    if hasattr(b, "fetch_public_welfare_detail"):
        install_detail_wrapper()
    if hasattr(b, "generate_packages"):
        install_package_wrapper()
    b.LLM_ENHANCEMENT_PATCH_APPLIED = True
