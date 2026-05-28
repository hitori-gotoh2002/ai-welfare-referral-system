from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode, urlparse
from xml.etree import ElementTree

import backend_server as b


PUBLIC_DETAIL_ALIASES: dict[str, tuple[str, str]] = {
    "svc-1": ("중앙", "WLF00003180"),
    "긴급복지 생계지원": ("중앙", "WLF00003180"),
    "긴급복지 지원": ("중앙", "WLF00003180"),
    "의료비 긴급지원": ("중앙", "WLF00003180"),
}
PUBLIC_DETAIL_CACHE: dict[str, tuple[str, str, dict[str, Any]]] = {}
PUBLIC_SEARCH_CACHE: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
PUBLIC_STATIC_PATHS = {
    "/",
    "/index.html",
    "/app.js",
    "/styles.css",
    "/age-filter-patch.js",
    "/auto-package-flow-patch.js",
    "/status-feedback-patch.js",
    "/case-loading-link-patch.js",
    "/commercial-ui-polish.js",
    "/commercial-ui-style-fix.js",
    "/case-list-persistence-patch.js",
    "/favicon.ico",
}
AGE_TARGET_PATTERNS = {
    "아동": r"아동|영유아|유아|어린이|초등학생|초등|미취학",
    "청소년": r"청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원",
    "청년": r"청년|대학생|사회초년생",
    "노인": r"노인|어르신|고령|독거노인|기초연금|장기요양",
}
TARGET_GROUP_PATTERNS = {
    **AGE_TARGET_PATTERNS,
    "중장년": r"중장년|장년|중년|40\s*세|50\s*세",
    "장애인": r"장애인|발달장애|장애\s*정도|장애\s*아동",
    "임산부": r"임산부|임신|출산|산모|영아",
    "한부모": r"한부모|조손|미혼모|미혼부",
    "여성폭력": r"가정폭력|성폭력|성매매|스토킹|여성긴급전화|1366",
    "국가유공자": r"국가유공자|보훈|참전|유공자",
}
BROAD_TARGET_PATTERN = re.compile(
    r"전\s*국민|전체|누구나|일반|저소득|취약계층|위기가구|기초생활|차상위|가구|가족|구직자"
)
CRISIS_PATTERN = re.compile(r"긴급|위기|체납|퇴거|노숙|폭력|학대|자살|자해|위험|실직|단전|단수|입원|응급")
SEARCH_EXPANSIONS = {
    ("노인", "돌봄"): ["노인맞춤돌봄", "노인돌봄", "방문돌봄", "재가"],
    ("노인", "의료"): ["노인 의료비", "병원동행", "장기요양"],
    ("청년", "주거"): ["청년월세", "월세", "주거안정 월세대출"],
    ("청년", "취업"): ["국민취업지원", "청년내일", "구직"],
    ("청소년", "안전"): ["청소년안전망", "위기청소년", "청소년상담"],
    ("저소득", "의료"): ["의료비", "긴급복지 의료", "재난적의료비"],
    ("저소득", "생계"): ["긴급복지 생계", "생활비", "생계급여"],
}
CASE_STOPWORDS = {
    "지원",
    "서비스",
    "복지",
    "대상",
    "가구",
    "상담",
    "필요",
    "확인",
    "연계",
    "신청",
    "제공",
    "사업",
    "운영",
    "프로그램",
    "현재",
    "최근",
    "어려움",
    "어렵고",
    "있습니다",
    "합니다",
    "합니다",
    "대한",
    "관련",
    "가능",
}
_NATIVE_FETCH_PUBLIC_WELFARE_SERVICES = b.fetch_public_welfare_services


def xml_tag_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1] if "}" in element.tag else element.tag


def xml_text(element: ElementTree.Element, *names: str) -> str:
    wanted = set(names)
    for found in element.iter():
        if xml_tag_name(found) in wanted and found.text:
            return b.clean_text(found.text)
    return ""


def xml_direct_text(element: ElementTree.Element, *names: str) -> str:
    wanted = set(names)
    for found in list(element):
        if xml_tag_name(found) in wanted and found.text:
            return b.clean_text(found.text)
    return ""


def xml_all_text(element: ElementTree.Element, name: str) -> list[str]:
    return [
        b.clean_text(item.text or "")
        for item in element.iter()
        if xml_tag_name(item) == name and b.clean_text(item.text or "")
    ]


def xml_items(root: ElementTree.Element) -> list[ElementTree.Element]:
    candidates = []
    for element in root.iter():
        if xml_direct_text(element, "servId", "wlfareInfoId") and xml_direct_text(
            element, "servNm", "wlfareInfoNm", "bizNm"
        ):
            candidates.append(element)
    return candidates


def first_nonempty(*values: str) -> str:
    return next((value for value in values if value), "")


def compact_text(value: str) -> str:
    return re.sub(r"[\s·ㆍ\-\(\)\[\]/,_]+", "", value or "").lower()


def age_groups_from_text(text: str) -> set[str]:
    value = b.clean_text(text)
    groups = {group for group, pattern in AGE_TARGET_PATTERNS.items() if re.search(pattern, value)}
    for match in re.finditer(r"(?<!\d)(\d{1,3})\s*세", value):
        age = int(match.group(1))
        if age >= 65:
            groups.add("노인")
        elif age >= 19:
            groups.add("청년")
        elif age >= 13:
            groups.add("청소년")
        else:
            groups.add("아동")
        if 40 <= age < 65:
            groups.add("중장년")
    return groups


def target_groups_from_text(text: str) -> set[str]:
    value = b.clean_text(text)
    groups = age_groups_from_text(value)
    groups.update(group for group, pattern in TARGET_GROUP_PATTERNS.items() if re.search(pattern, value))
    return groups


def case_context_text(case: dict[str, Any], structured: dict[str, Any] | None = None) -> str:
    structured = structured or {}
    parts = [
        case.get("title", ""),
        case.get("memo", ""),
        case.get("targetType", ""),
        case.get("region", ""),
        " ".join(case.get("issueTypes") or []),
        structured.get("target", ""),
        structured.get("region", ""),
        structured.get("urgency", ""),
        " ".join(structured.get("needs") or []),
        " ".join(structured.get("keywords") or []),
    ]
    for check in structured.get("riskChecks") or []:
        if isinstance(check, dict):
            parts.extend([check.get("label", ""), check.get("text", "")])
    return b.clean_text(" ".join(str(part) for part in parts if part))


def query_case_age_groups(case: dict[str, Any]) -> set[str]:
    return age_groups_from_text(" ".join(str(case.get(key, "")) for key in ("title", "memo", "targetType")))


def query_case_target_groups(case: dict[str, Any], structured: dict[str, Any] | None = None) -> set[str]:
    return target_groups_from_text(case_context_text(case, structured))


def service_text(service: dict[str, Any]) -> str:
    parts = [
        service.get("name", ""),
        service.get("target", ""),
        service.get("summary", ""),
        service.get("eligibility", ""),
        service.get("support", ""),
        service.get("process", ""),
        service.get("selectionCriteria", ""),
        " ".join(service.get("docs") or []),
        " ".join(service.get("domains") or []),
    ]
    return b.clean_text(" ".join(str(part) for part in parts if part))


def service_age_groups(service: dict[str, Any]) -> set[str]:
    return age_groups_from_text(service_text(service))


def service_target_groups(service: dict[str, Any]) -> set[str]:
    return target_groups_from_text(service_text(service))


def service_has_broad_target(service: dict[str, Any]) -> bool:
    target_text = b.clean_text(" ".join(str(service.get(key, "")) for key in ("target", "eligibility", "summary")))
    return bool(BROAD_TARGET_PATTERN.search(target_text))


def query_target_compatible(service: dict[str, Any], case: dict[str, Any]) -> bool:
    return target_compatible(service, case, None)


def target_compatible(
    service: dict[str, Any], case: dict[str, Any], structured: dict[str, Any] | None = None
) -> bool:
    case_groups = query_case_target_groups(case, structured)
    service_groups = service_target_groups(service)
    if service_groups and case_groups:
        return bool(service_groups & case_groups)
    if service_groups and not case_groups and not service_has_broad_target(service):
        return False
    if not case_groups or not service_groups:
        return True
    return bool(case_groups & service_groups)


def meaningful_tokens(text: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[가-힣A-Za-z0-9]{2,}", text):
        value = token.strip().lower()
        if value in CASE_STOPWORDS or value.isdigit():
            continue
        if len(value) <= 1:
            continue
        tokens.append(token)
    return b.unique(tokens)


def case_relevance_terms(
    case: dict[str, Any], structured: dict[str, Any] | None = None, needs: list[str] | None = None
) -> list[str]:
    structured = structured or {}
    text = case_context_text(case, structured)
    lowered = text.lower()
    terms: list[str] = []
    for need in needs or structured.get("needs") or []:
        terms.append(str(need))
        for word in b.KEYWORD_MAP.get(need, []):
            if word and word.lower() in lowered:
                terms.append(word)
    for keyword in structured.get("keywords") or []:
        keyword = b.clean_text(str(keyword))
        if len(keyword) >= 2 and keyword.lower() not in CASE_STOPWORDS:
            terms.append(keyword)
    terms.extend(meaningful_tokens(text)[:24])
    terms.extend(query_case_target_groups(case, structured))
    return b.unique([term for term in terms if len(str(term)) >= 2])[:36]


def keyword_hit_count(service: dict[str, Any], terms: list[str]) -> int:
    haystack = service_text(service).lower()
    return sum(1 for term in terms if str(term).lower() in haystack)


def case_is_crisis(case: dict[str, Any], structured: dict[str, Any] | None = None) -> bool:
    structured = structured or {}
    if case.get("urgency") == "긴급" or structured.get("urgency") == "긴급":
        return True
    return bool(CRISIS_PATTERN.search(case_context_text(case, structured)))


def case_requires_urgent_first(case: dict[str, Any], structured: dict[str, Any] | None = None) -> bool:
    structured = structured or {}
    if case.get("urgency") == "긴급" or structured.get("urgency") == "긴급":
        return True
    return bool(re.search(r"자살|자해|폭력|학대|노숙|응급|단전|단수", case_context_text(case, structured)))


def service_score(
    service: dict[str, Any], needs: list[str], case: dict[str, Any], structured: dict[str, Any] | None = None
) -> int:
    if not target_compatible(service, case, structured):
        return 0

    domains = service.get("domains") or []
    overlap = len([domain for domain in domains if domain in needs])
    terms = case_relevance_terms(case, structured, needs)
    keyword_hits = keyword_hit_count(service, terms)
    case_groups = query_case_target_groups(case, structured)
    target_hits = len(case_groups & service_target_groups(service))
    target_match = 1 if target_hits else 0
    non_target_hits = max(keyword_hits - target_hits, 0)
    external_public = bool(
        service.get("externalId")
        or str(service.get("id", "")).startswith("중앙:")
        or str(service.get("id", "")).startswith("지자체:")
    )

    if overlap == 0 and keyword_hits == 0 and target_match == 0:
        return 0
    if overlap == 0 and non_target_hits == 0:
        return 0
    if external_public and overlap > 0 and keyword_hits == 0 and target_match == 0:
        return 0

    region = case.get("region") or (structured or {}).get("region") or ""
    service_region = service.get("region", "")
    region_match = 1 if service_region == "전국" or (region and service_region and service_region in region) else 0
    urgent_service = service.get("urgency") == "긴급"
    crisis = case_is_crisis(case, structured)

    score = overlap * 10 + min(keyword_hits, 6) * 4 + region_match * 2 + target_match * 7
    if urgent_service and crisis and (overlap or keyword_hits):
        score += 3
    elif urgent_service and not crisis:
        score -= 4
    if service.get("source") in ("기관", "민간") and any(need in needs for need in ("심리", "돌봄", "안전")):
        score += 2
    return max(score, 0)


def service_score_for_query(service: dict[str, Any], needs: list[str], case: dict[str, Any]) -> int:
    return service_score(service, needs, case, None)


def query_public_terms(query: dict[str, list[str]]) -> list[str]:
    q = (query.get("q", [""])[0] or "").strip()
    if q:
        return [q]
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    target = (query.get("target", [""])[0] or "").strip()
    memo = (query.get("memo", [""])[0] or "").strip()
    keywords = [item for item in (query.get("keywords", [""])[0] or "").split(",") if item]
    synthetic_case = {"memo": memo, "targetType": target, "issueTypes": needs}
    synthetic_structured = {"needs": needs, "keywords": keywords, "target": target}
    target_groups = query_case_target_groups(synthetic_case, synthetic_structured)
    terms = [
        *query_case_target_groups(synthetic_case, synthetic_structured),
        *expanded_search_terms(target_groups, needs),
        *keywords,
        *case_relevance_terms(synthetic_case, synthetic_structured, needs),
        *needs,
    ]
    return b.unique([term for term in terms if len(str(term)) >= 2 and str(term).lower() not in CASE_STOPWORDS])[:5]


def cached_native_public_search(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key = "&".join(f"{name}={','.join(values)}" for name, values in sorted(query.items()))
    if key in PUBLIC_SEARCH_CACHE:
        services, meta = PUBLIC_SEARCH_CACHE[key]
        return list(services), {**meta, "cached": True}
    services, meta = _NATIVE_FETCH_PUBLIC_WELFARE_SERVICES(query)
    PUBLIC_SEARCH_CACHE[key] = (list(services), dict(meta))
    return services, meta


def fetch_public_welfare_services(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if (query.get("q", [""])[0] or "").strip():
        return cached_native_public_search(query)

    terms = query_public_terms(query)
    if not terms:
        return _NATIVE_FETCH_PUBLIC_WELFARE_SERVICES(query)

    services: list[dict[str, Any]] = []
    errors: list[str] = []
    enabled = True
    for term in terms:
        next_query = {key: list(value) for key, value in query.items()}
        next_query["q"] = [term]
        next_query.setdefault("numOfRows", ["30"])
        found, meta = cached_native_public_search(next_query)
        enabled = bool(meta.get("enabled", enabled))
        services.extend(found)
        errors.extend(meta.get("errors") or [])
    unique = b.unique_services(services)
    return unique, {
        "enabled": enabled,
        "source": "data.go.kr/bokjiro",
        "count": len(unique),
        "searchTerms": terms,
        "errors": b.unique(errors),
    }


def filter_local_services(query: dict[str, list[str]], catalog: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    q = (query.get("q", [""])[0] or "").strip().lower()
    source = query.get("source", ["전체"])[0] or "전체"
    domain = query.get("domain", ["전체"])[0] or "전체"
    urgency = query.get("urgency", ["전체"])[0] or "전체"
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    case = {
        "region": query.get("region", [""])[0] or "",
        "targetType": query.get("target", [""])[0] or "",
        "memo": query.get("memo", [""])[0] or "",
        "issueTypes": needs,
    }
    structured = {
        "region": case["region"],
        "target": case["targetType"],
        "needs": needs,
        "keywords": [item for item in (query.get("keywords", [""])[0] or "").split(",") if item],
    }
    source_catalog = catalog or b.SERVICES
    hide_target_mismatch = bool(query_case_target_groups(case, structured)) and not q

    def matches(service: dict[str, Any]) -> bool:
        searchable = " ".join(
            str(part)
            for part in [
                service.get("name", ""),
                service.get("summary", ""),
                service.get("target", ""),
                service.get("region", ""),
                service.get("source", ""),
                *(service.get("domains") or []),
            ]
        ).lower()
        return (
            (not q or q in searchable)
            and (source == "전체" or service.get("source") == source)
            and (domain == "전체" or domain in (service.get("domains") or []))
            and (urgency == "전체" or service.get("urgency") == urgency)
            and (not hide_target_mismatch or target_compatible(service, case, structured))
        )

    return sorted(
        [service for service in source_catalog if matches(service)],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    )


def package_search_terms(case: dict[str, Any], structured: dict[str, Any], needs: list[str]) -> list[str]:
    target_groups = query_case_target_groups(case, structured)
    terms = [
        *target_groups,
        *expanded_search_terms(target_groups, needs),
        *structured.get("keywords", []),
        *case_relevance_terms(case, structured, needs),
        *needs,
    ]
    return b.unique([str(term) for term in terms if len(str(term)) >= 2 and str(term).lower() not in CASE_STOPWORDS])[:6]


def expanded_search_terms(target_groups: set[str], needs: list[str]) -> list[str]:
    terms: list[str] = []
    for group in target_groups:
        for need in needs:
            terms.extend(SEARCH_EXPANSIONS.get((group, need), []))
    if "의료" in needs:
        terms.extend(SEARCH_EXPANSIONS.get(("저소득", "의료"), []))
    if "생계" in needs:
        terms.extend(SEARCH_EXPANSIONS.get(("저소득", "생계"), []))
    return b.unique(terms)


def enrich_catalog_for_case(
    case: dict[str, Any], structured: dict[str, Any], needs: list[str], catalog: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    base_catalog = catalog or b.SERVICES
    region = case.get("region") or structured.get("region") or ""
    target = structured.get("target") or case.get("targetType") or ""
    public_services: list[dict[str, Any]] = []
    for term in package_search_terms(case, structured, needs):
        query = {
            "q": [term],
            "source": ["전체"],
            "domain": ["전체"],
            "urgency": ["전체"],
            "needs": [",".join(needs)],
            "region": [region],
            "target": [target],
            "numOfRows": ["30"],
        }
        try:
            found, _meta = cached_native_public_search(query)
        except Exception:
            found = []
        public_services.extend(found)
    return b.unique_services([*public_services, *base_catalog])


def ensure_coverage(
    items: list[dict[str, Any]],
    needs: list[str],
    catalog: list[dict[str, Any]],
    case: dict[str, Any],
    structured: dict[str, Any],
) -> list[dict[str, Any]]:
    selected = b.unique_services(list(items))
    selected_ids = {service.get("id") for service in selected}
    domains = {domain for service in selected for domain in (service.get("domains") or [])}
    ranked = sorted(
        [
            service
            for service in catalog
            if service.get("id") not in selected_ids and service_score(service, needs, case, structured) > 0
        ],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    )
    for need in needs[:4]:
        if need in domains:
            continue
        found = next((service for service in ranked if need in (service.get("domains") or [])), None)
        if found:
            selected.append(found)
            selected_ids.add(found.get("id"))
            domains.update(found.get("domains") or [])
    while len([service for service in selected if service_score(service, needs, case, structured) > 0]) < 3:
        found = next((service for service in ranked if service.get("id") not in selected_ids), None)
        if not found:
            break
        selected.append(found)
        selected_ids.add(found.get("id"))
    return selected[:5]


def package_copy(needs: list[str]) -> tuple[str, str]:
    primary = needs[0] if needs else "생계"
    if primary == "주거":
        return "주거 안정 패키지", "주거비·거처 위험과 생계 부담을 함께 낮추는 조합"
    if primary == "의료":
        return "의료·생계 회복 패키지", "치료비와 생활 유지 부담을 우선 확인하는 조합"
    if primary == "돌봄":
        return "돌봄 연계 패키지", "돌봄 공백과 지역 기관 연결을 먼저 보강하는 조합"
    if primary == "심리":
        return "심리 안정 패키지", "상담·정신건강 지원과 생활 위험을 함께 살피는 조합"
    if primary == "취업":
        return "자립 준비 패키지", "일자리·훈련과 단기 생활 지원을 연결하는 조합"
    if primary == "교육":
        return "교육 지속 패키지", "학업 유지와 생활 지원을 함께 점검하는 조합"
    return "긴급 안정 패키지", "상담 메모에서 확인된 핵심 욕구를 우선 낮추는 조합"


def generate_packages(
    case: dict[str, Any], structured: dict[str, Any] | None, catalog: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    if not structured:
        structured = b.analyze_case(case)
    needs = structured.get("needs") or case.get("issueTypes") or ["생계", "주거"]
    enriched = enrich_catalog_for_case(case, structured, needs, catalog)
    source_catalog = [service for service in enriched if target_compatible(service, case, structured)]
    ranked = sorted(
        [service for service in source_catalog if service_score(service, needs, case, structured) > 0],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    )
    if not ranked:
        ranked = source_catalog[:]

    urgent_first = case_requires_urgent_first(case, structured)
    urgent_relevant = [
        service
        for service in ranked
        if urgent_first and service.get("urgency") == "긴급" and service_score(service, needs, case, structured) >= 10
    ]
    primary_seed = b.unique_services([*urgent_relevant, *ranked]) if urgent_first else ranked
    focus_seed = b.unique_services(
        [
            *[
                service
                for service in ranked
                if any(domain in (service.get("domains") or []) for domain in needs[1:] or needs)
                and service.get("urgency") != "긴급"
            ],
            *ranked,
        ]
    )
    local_seed = b.unique_services(
        [*[service for service in ranked if service.get("source") in ("기관", "민간", "지자체")], *ranked]
    )

    top_a = ensure_coverage(primary_seed[:4], needs, ranked, case, structured)
    top_b = ensure_coverage(focus_seed[:4], needs, ranked, case, structured)
    top_c = ensure_coverage(local_seed[:4], needs, ranked, case, structured)
    title, summary = package_copy(needs)

    return [
        b.build_package("pkg-1", title, summary, top_a, 94),
        b.build_package("pkg-2", "회복·자립 패키지", "단기 지원 이후 남은 욕구를 이어서 연결하는 조합", top_b, 88),
        b.build_package("pkg-3", "지역기관 연계 패키지", "공공 제도와 민간·지역기관 접점을 병합", top_c, 83),
    ]


def public_search_terms(service: dict[str, Any]) -> list[str]:
    name = b.clean_text(service.get("name", ""))
    terms = [
        name,
        re.sub(r"\s*\([^)]*\)", "", name).strip(),
        name.replace("지원금", "지원").replace("사업", "").strip(),
    ]
    words = [word for word in re.split(r"\s+", name) if len(word) >= 2]
    if len(words) >= 2:
        terms.append(" ".join(words[:2]))
    terms.extend(words)
    return b.unique([term for term in terms if term])


def public_detail_identity(service: dict[str, Any]) -> tuple[str, str]:
    source = service.get("source", "")
    service_id = service.get("externalId") or service.get("id", "")
    parsed = b.parse_public_service_id(service.get("id", ""))
    if parsed:
        return parsed
    alias = PUBLIC_DETAIL_ALIASES.get(service.get("id", "")) or PUBLIC_DETAIL_ALIASES.get(service.get("name", ""))
    if alias:
        return alias
    return source, service_id


def resolve_public_detail_identity(
    service: dict[str, Any], service_key: str
) -> tuple[str, str, dict[str, Any]] | None:
    cache_key = compact_text(service.get("name", ""))
    if cache_key in PUBLIC_DETAIL_CACHE:
        return PUBLIC_DETAIL_CACHE[cache_key]

    source = service.get("source", "")
    source_order = [source] if source in ("중앙", "지자체") else []
    source_order.extend(item for item in ("중앙", "지자체") if item not in source_order)
    target_name = compact_text(service.get("name", ""))

    for term in public_search_terms(service):
        for candidate_source in source_order:
            endpoint = b.NATIONAL_WELFARE_URL if candidate_source == "중앙" else b.LOCAL_WELFARE_URL
            params = {
                "serviceKey": service_key,
                "pageNo": "1",
                "numOfRows": "20",
                "srchKeyCode": "003",
                "searchWrd": term,
            }
            if candidate_source == "중앙":
                params["callTp"] = "L"
                params["orderBy"] = "popular"
            else:
                params["arrgOrd"] = "001"
            try:
                with b.urlopen(f"{endpoint}?{urlencode(params)}", timeout=10) as response:
                    raw = response.read()
                root = ElementTree.fromstring(raw)
                result_code = xml_text(root, "resultCode")
                if result_code and result_code not in ("0", "00", "NORMAL_CODE"):
                    continue
                candidates = [b.normalize_public_service(item, candidate_source) for item in xml_items(root)]
            except Exception:
                continue

            ranked = sorted(
                candidates,
                key=lambda item: (
                    compact_text(item.get("name", "")) == target_name,
                    target_name and target_name in compact_text(item.get("name", "")),
                    compact_text(term) in compact_text(item.get("name", "")),
                ),
                reverse=True,
            )
            for candidate in ranked:
                candidate_name = compact_text(candidate.get("name", ""))
                if not target_name or target_name == candidate_name or target_name in candidate_name or candidate_name in target_name:
                    resolved = (candidate_source, candidate.get("externalId", ""), candidate)
                    if resolved[1]:
                        PUBLIC_DETAIL_CACHE[cache_key] = resolved
                        return resolved
    return None


def load_public_detail(
    service: dict[str, Any], service_key: str, source: str, service_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if source not in ("중앙", "지자체") or not service_id:
        return service, {"enabled": True, "detail": False, "reason": "unsupported_service_source"}

    endpoint = b.NATIONAL_WELFARE_DETAIL_URL if source == "중앙" else b.LOCAL_WELFARE_DETAIL_URL
    params = {"serviceKey": service_key, "servId": service_id}
    if source == "중앙":
        params["callTp"] = "D"
    url = f"{endpoint}?{urlencode(params)}"

    try:
        with b.urlopen(url, timeout=15) as response:
            raw = response.read()
        root = ElementTree.fromstring(raw)
        result_code = xml_text(root, "resultCode")
        result_message = xml_text(root, "resultMessage", "resultMsg")
        if result_code and result_code not in ("0", "00", "NORMAL_CODE"):
            return service, {"enabled": True, "detail": False, "errors": [f"{source}:{result_code}:{result_message}"]}

        application_steps = b.unique(
            [
                *xml_all_text(root, "applmetList"),
                *xml_all_text(root, "aplyMtdCn"),
                *xml_all_text(root, "reqstProces"),
            ]
        )
        contacts = b.unique([*xml_all_text(root, "inqplCtadrList"), *xml_all_text(root, "inqplCtadr")])
        homepages = b.unique([*xml_all_text(root, "inqplHmpgReldList"), *xml_all_text(root, "inqplHmpgReld")])
        forms = b.unique([*xml_all_text(root, "basfrmList"), *xml_all_text(root, "reqstSe")])
        laws = b.unique([*xml_all_text(root, "baslawList"), *xml_all_text(root, "baslaw")])

        detail = {
            **service,
            "externalId": service_id,
            "publicDataSource": source,
            "name": first_nonempty(
                xml_text(root, "servNm", "wlfareInfoNm", "bizNm", "servName"),
                service.get("name", ""),
            ),
            "summary": first_nonempty(
                xml_text(root, "wlfareInfoOutlCn", "servDgst", "servDgstCn", "bizDc", "summary"),
                service.get("summary", ""),
            ),
            "eligibility": first_nonempty(
                xml_text(root, "tgtrDtlCn", "sprtTrgtCn", "trgterIndvdlArray", "tgtrCn"),
                service.get("eligibility", ""),
            ),
            "selectionCriteria": xml_text(root, "slctCritCn", "slctCrit", "selectnStdr"),
            "support": first_nonempty(
                xml_text(root, "alwServCn", "servCn", "sportCn", "sprtCn"),
                service.get("support", ""),
            ),
            "process": first_nonempty(
                xml_text(root, "aplyMtdCn", "aplyMtd", "reqstProces", "useMthd"),
                " → ".join(application_steps),
                service.get("process", ""),
            ),
            "docs": b.unique([*service.get("docs", []), *forms]) or service.get("docs", []),
            "contact": first_nonempty(
                xml_text(root, "rprsCtadr", "inqplCtadr", "bizChrDeptNm"),
                contacts[0] if contacts else "",
                service.get("contact", ""),
            ),
            "url": first_nonempty(
                xml_text(root, "servDtlLink", "servDtlUrl", "inqplHmpgReld", "url"),
                service.get("url", ""),
                homepages[0] if homepages else "",
                "https://www.bokjiro.go.kr",
            ),
            "updated": first_nonempty(
                xml_text(root, "crtrYr", "lastModYmd", "svcfrstRegTs", "frstRegTs"),
                service.get("updated", ""),
            ),
            "applicationSteps": application_steps,
            "contacts": contacts,
            "homepages": homepages,
            "laws": laws,
            "detailLoaded": True,
        }
        if source == "지자체":
            detail["region"] = first_nonempty(
                " ".join([xml_text(root, "ctpvNm"), xml_text(root, "sggNm")]).strip(),
                service.get("region", ""),
            )
            detail["contact"] = first_nonempty(
                contacts[0] if contacts else "",
                xml_text(root, "bizChrDeptNm"),
                service.get("contact", ""),
            )
        return detail, {"enabled": True, "detail": True, "source": "data.go.kr/bokjiro-detail"}
    except Exception as error:
        return service, {"enabled": True, "detail": False, "errors": [f"{source}:{error}"]}


def fetch_public_welfare_detail(service: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    service_key = b.get_public_data_key()
    if not service_key:
        return service, {"enabled": False, "reason": "missing_service_key"}

    source, service_id = public_detail_identity(service)
    detail, meta = load_public_detail(service, service_key, source, service_id)
    if meta.get("detail"):
        return detail, meta

    resolved = resolve_public_detail_identity(service, service_key)
    if not resolved:
        return detail, meta

    resolved_source, resolved_id, public_service = resolved
    lookup_service = {
        **public_service,
        **service,
        "source": resolved_source,
        "externalId": resolved_id,
        "publicMatchedId": public_service.get("id", ""),
    }
    detail, resolved_meta = load_public_detail(lookup_service, service_key, resolved_source, resolved_id)
    return detail, {**resolved_meta, "matchedBy": "public-list-search", "previousDetail": meta}


def apply() -> None:
    b.xml_tag_name = xml_tag_name
    b.xml_text = xml_text
    b.xml_all_text = xml_all_text
    b.xml_items = xml_items
    b.fetch_public_welfare_services = fetch_public_welfare_services
    b.fetch_public_welfare_detail = fetch_public_welfare_detail
    b.target_compatible = target_compatible
    b.service_score = service_score
    b.filter_local_services = filter_local_services
    b.generate_packages = generate_packages
    b.RUNTIME_PATCH_APPLIED = True

    native_do_get = b.WelfareHandler.do_GET

    def patched_do_get(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            if parsed.path not in PUBLIC_STATIC_PATHS:
                return self.write_json({"error": "not_found"}, b.HTTPStatus.NOT_FOUND)
            original_path = self.path
            self.path = parsed.path
            try:
                return native_do_get(self)
            finally:
                self.path = original_path
        if parsed.path == "/api/health":
            return self.write_json(
                {
                    "ok": True,
                    "service": "welfare-copilot-backend",
                    "time": b.datetime.now().isoformat(),
                    "runtimePatch": True,
                    "publicData": {
                        "enabled": bool(b.get_public_data_key()),
                        "keyEnvNames": b.PUBLIC_DATA_KEY_ENV_NAMES,
                        "nationalEndpoint": b.NATIONAL_WELFARE_URL,
                        "nationalDetailEndpoint": b.NATIONAL_WELFARE_DETAIL_URL,
                        "localEndpoint": b.LOCAL_WELFARE_URL,
                        "localDetailEndpoint": b.LOCAL_WELFARE_DETAIL_URL,
                        "socialserviceProviderEndpoint": b.SOCIALSERVICE_PROVIDER_URL,
                        "resourceInfoEndpoint": b.RESOURCE_INFO_URL,
                    },
                    "llm": {
                        "enabled": bool(b.GEMINI_API_KEY),
                        "provider": "google-gemini",
                        "model": b.GEMINI_MODEL,
                    },
                }
            )
        return native_do_get(self)

    b.WelfareHandler.do_GET = patched_do_get
