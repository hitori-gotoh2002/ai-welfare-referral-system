from __future__ import annotations

import re
from typing import Any

import backend_server as b


TARGET_PATTERNS = {
    "아동": r"아동|영유아|유아|어린이|초등학생|미취학",
    "청소년": r"청소년|중학생|고등학생|학교\s*밖|위기청소년|청소년특별지원",
    "청년": r"청년|대학생|사회초년생|구직청년",
    "중장년": r"중장년|장년|중년|40\s*세|50\s*세",
    "노인": r"노인|어르신|고령|독거노인|장기요양|기초연금",
    "장애인": r"장애인|발달장애|장애\s*정도|장애\s*아동",
    "임산부": r"임산부|임신|출산|산모|영아",
    "한부모": r"한부모|조손|미혼모|미혼부",
    "여성폭력": r"가정폭력|성폭력|성매매|스토킹|여성긴급전화|1366",
    "국가유공자": r"국가유공자|보훈|참전|유공자",
}
BROAD_TARGET = re.compile(r"전\s*국민|전체|누구나|일반|저소득|취약계층|위기가구|기초생활|차상위|가구|가족|구직자")
CRISIS = re.compile(r"긴급|위기|체납|퇴거|노숙|폭력|학대|자살|자해|위험|실직|단전|단수|입원|응급")
URGENT_FIRST = re.compile(r"자살|자해|폭력|학대|노숙|응급|단전|단수")
STOPWORDS = {
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
    "있습니다",
    "합니다",
    "대한",
    "관련",
    "가능",
}
SEARCH_EXPANSIONS = {
    ("노인", "돌봄"): ["노인", "노인맞춤돌봄", "노인돌봄", "방문돌봄", "재가"],
    ("노인", "의료"): ["노인 의료비", "병원동행", "장기요양"],
    ("청년", "주거"): ["청년", "청년월세", "월세", "주거안정 월세대출"],
    ("청년", "취업"): ["국민취업지원", "청년내일", "구직"],
    ("청소년", "안전"): ["청소년안전망", "위기청소년", "청소년상담"],
    ("저소득", "의료"): ["의료비", "긴급복지 의료", "재난적의료비"],
    ("저소득", "생계"): ["긴급복지 생계", "생활비", "생계급여"],
}

_native_fetch_public = b.fetch_public_welfare_services
_search_cache: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}


def clean_join(parts: list[Any]) -> str:
    return b.clean_text(" ".join(str(part) for part in parts if part))


def context_text(case: dict[str, Any], structured: dict[str, Any] | None = None) -> str:
    structured = structured or {}
    parts: list[Any] = [
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
    return clean_join(parts)


def groups_from_text(text: str) -> set[str]:
    value = b.clean_text(text)
    groups = {name for name, pattern in TARGET_PATTERNS.items() if re.search(pattern, value)}
    for match in re.finditer(r"(?<!\d)(\d{1,3})\s*세", value):
        age = int(match.group(1))
        if age >= 65:
            groups.add("노인")
        elif age >= 40:
            groups.add("중장년")
        elif age >= 19:
            groups.add("청년")
        elif age >= 13:
            groups.add("청소년")
        else:
            groups.add("아동")
    return groups


def service_text(service: dict[str, Any]) -> str:
    return clean_join(
        [
            service.get("name", ""),
            service.get("target", ""),
            service.get("summary", ""),
            service.get("eligibility", ""),
            service.get("selectionCriteria", ""),
            service.get("support", ""),
            service.get("process", ""),
            " ".join(service.get("docs") or []),
            " ".join(service.get("domains") or []),
        ]
    )


def target_compatible(service: dict[str, Any], case: dict[str, Any], structured: dict[str, Any] | None = None) -> bool:
    case_groups = groups_from_text(context_text(case, structured))
    service_groups = groups_from_text(service_text(service))
    if service_groups and case_groups:
        return bool(service_groups & case_groups)
    if service_groups and not case_groups:
        target_text = clean_join([service.get("target", ""), service.get("eligibility", ""), service.get("summary", "")])
        return bool(BROAD_TARGET.search(target_text))
    return True


def meaningful_tokens(text: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[가-힣A-Za-z0-9]{2,}", text):
        lowered = token.lower()
        if lowered not in STOPWORDS and not lowered.isdigit():
            tokens.append(token)
    return b.unique(tokens)


def case_terms(case: dict[str, Any], structured: dict[str, Any] | None, needs: list[str]) -> list[str]:
    structured = structured or {}
    text = context_text(case, structured).lower()
    terms: list[str] = []
    for need in needs:
        terms.append(need)
        for word in b.KEYWORD_MAP.get(need, []):
            if word.lower() in text:
                terms.append(word)
    terms.extend(str(item) for item in structured.get("keywords") or [])
    terms.extend(meaningful_tokens(text)[:24])
    terms.extend(groups_from_text(context_text(case, structured)))
    return b.unique([term for term in terms if len(str(term)) >= 2 and str(term).lower() not in STOPWORDS])[:36]


def service_score(
    service: dict[str, Any], needs: list[str], case: dict[str, Any], structured: dict[str, Any] | None = None
) -> int:
    if not target_compatible(service, case, structured):
        return 0
    domains = service.get("domains") or []
    overlap = len([domain for domain in domains if domain in needs])
    terms = case_terms(case, structured, needs)
    haystack = service_text(service).lower()
    keyword_hits = sum(1 for term in terms if str(term).lower() in haystack)
    service_groups = groups_from_text(service_text(service))
    target_hits = len(groups_from_text(context_text(case, structured)) & service_groups)
    non_target_hits = max(keyword_hits - target_hits, 0)
    external_public = bool(
        service.get("externalId")
        or str(service.get("id", "")).startswith("중앙:")
        or str(service.get("id", "")).startswith("지자체:")
    )
    if overlap == 0 and keyword_hits == 0 and target_hits == 0:
        return 0
    if overlap == 0 and non_target_hits == 0:
        return 0
    if external_public and overlap > 0 and keyword_hits == 0 and target_hits == 0:
        return 0

    region = case.get("region") or (structured or {}).get("region") or ""
    service_region = service.get("region", "")
    region_match = 1 if service_region == "전국" or (region and service_region and service_region in region) else 0
    crisis = case.get("urgency") == "긴급" or (structured or {}).get("urgency") == "긴급" or CRISIS.search(context_text(case, structured))
    score = overlap * 10 + min(keyword_hits, 6) * 4 + target_hits * 7 + region_match * 2
    if service.get("urgency") == "긴급" and crisis and (overlap or keyword_hits):
        score += 3
    elif service.get("urgency") == "긴급" and not crisis:
        score -= 4
    if service.get("source") in ("기관", "민간") and any(need in needs for need in ("심리", "돌봄", "안전")):
        score += 2
    return max(score, 0)


def expanded_terms(groups: set[str], needs: list[str]) -> list[str]:
    terms: list[str] = []
    for group in groups:
        for need in needs:
            terms.extend(SEARCH_EXPANSIONS.get((group, need), []))
    if "의료" in needs:
        terms.extend(SEARCH_EXPANSIONS[("저소득", "의료")])
    if "생계" in needs:
        terms.extend(SEARCH_EXPANSIONS[("저소득", "생계")])
    return b.unique(terms)


def public_search(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key = "&".join(f"{name}={','.join(values)}" for name, values in sorted(query.items()))
    if key in _search_cache:
        services, meta = _search_cache[key]
        return list(services), {**meta, "cached": True}
    services, meta = _native_fetch_public(query)
    _search_cache[key] = (list(services), dict(meta))
    return services, meta


def fetch_public_welfare_services(query: dict[str, list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if (query.get("q", [""])[0] or "").strip():
        return public_search(query)
    needs = [item for item in query.get("needs", [""])[0].split(",") if item]
    target = query.get("target", [""])[0] or ""
    memo = query.get("memo", [""])[0] or ""
    keywords = [item for item in (query.get("keywords", [""])[0] or "").split(",") if item]
    case = {"memo": memo, "targetType": target, "issueTypes": needs}
    structured = {"target": target, "needs": needs, "keywords": keywords}
    groups = groups_from_text(context_text(case, structured))
    terms = b.unique([*groups, *expanded_terms(groups, needs), *keywords, *needs])[:5]
    services: list[dict[str, Any]] = []
    errors: list[str] = []
    for term in terms:
        next_query = {key: list(value) for key, value in query.items()}
        next_query["q"] = [term]
        found, meta = public_search(next_query)
        services.extend(found)
        errors.extend(meta.get("errors") or [])
    return b.unique_services(services), {
        "enabled": True,
        "source": "data.go.kr/bokjiro",
        "count": len(services),
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
        "needs": needs,
        "target": case["targetType"],
        "keywords": [item for item in (query.get("keywords", [""])[0] or "").split(",") if item],
    }

    def matches(service: dict[str, Any]) -> bool:
        searchable = clean_join(
            [
                service.get("name", ""),
                service.get("summary", ""),
                service.get("target", ""),
                service.get("region", ""),
                service.get("source", ""),
                " ".join(service.get("domains") or []),
            ]
        ).lower()
        return (
            (not q or q in searchable)
            and (source == "전체" or service.get("source") == source)
            and (domain == "전체" or domain in (service.get("domains") or []))
            and (urgency == "전체" or service.get("urgency") == urgency)
            and (not groups_from_text(context_text(case, structured)) or q or target_compatible(service, case, structured))
        )

    return sorted(
        [service for service in (catalog or b.SERVICES) if matches(service)],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    )


def package_terms(case: dict[str, Any], structured: dict[str, Any], needs: list[str]) -> list[str]:
    groups = groups_from_text(context_text(case, structured))
    terms = [*groups, *expanded_terms(groups, needs), *structured.get("keywords", []), *case_terms(case, structured, needs), *needs]
    return b.unique([str(term) for term in terms if len(str(term)) >= 2 and str(term).lower() not in STOPWORDS])[:6]


def enrich_catalog(case: dict[str, Any], structured: dict[str, Any], needs: list[str], catalog: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    public_services: list[dict[str, Any]] = []
    for term in package_terms(case, structured, needs):
        try:
            found, _meta = public_search(
                {
                    "q": [term],
                    "source": ["전체"],
                    "domain": ["전체"],
                    "urgency": ["전체"],
                    "needs": [",".join(needs)],
                    "region": [case.get("region") or structured.get("region") or ""],
                    "target": [structured.get("target") or case.get("targetType") or ""],
                    "numOfRows": ["30"],
                }
            )
            public_services.extend(found)
        except Exception:
            continue
    return b.unique_services([*public_services, *(catalog or b.SERVICES)])


def ensure_coverage(
    items: list[dict[str, Any]], needs: list[str], ranked: list[dict[str, Any]], case: dict[str, Any], structured: dict[str, Any]
) -> list[dict[str, Any]]:
    selected = b.unique_services(items)
    selected_ids = {item.get("id") for item in selected}
    domains = {domain for service in selected for domain in (service.get("domains") or [])}
    for need in needs[:4]:
        if need in domains:
            continue
        found = next((service for service in ranked if service.get("id") not in selected_ids and need in (service.get("domains") or [])), None)
        if found:
            selected.append(found)
            selected_ids.add(found.get("id"))
            domains.update(found.get("domains") or [])
    while len(selected) < 3:
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
    return "긴급 안정 패키지", "상담 메모에서 확인된 핵심 욕구를 우선 낮추는 조합"


def generate_packages(case: dict[str, Any], structured: dict[str, Any] | None, catalog: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    structured = structured or b.analyze_case(case)
    needs = structured.get("needs") or case.get("issueTypes") or ["생계", "주거"]
    source_catalog = [service for service in enrich_catalog(case, structured, needs, catalog) if target_compatible(service, case, structured)]
    ranked = sorted(
        [service for service in source_catalog if service_score(service, needs, case, structured) > 0],
        key=lambda service: service_score(service, needs, case, structured),
        reverse=True,
    ) or source_catalog
    force_urgent = case.get("urgency") == "긴급" or structured.get("urgency") == "긴급" or URGENT_FIRST.search(context_text(case, structured))
    urgent = [service for service in ranked if force_urgent and service.get("urgency") == "긴급" and service_score(service, needs, case, structured) >= 10]
    top_a = ensure_coverage(b.unique_services([*urgent, *ranked])[:4], needs, ranked, case, structured)
    top_b = ensure_coverage([service for service in ranked if service.get("urgency") != "긴급"][:4] or ranked[:4], needs, ranked, case, structured)
    top_c = ensure_coverage([service for service in ranked if service.get("source") in ("기관", "민간", "지자체")][:4] or ranked[:4], needs, ranked, case, structured)
    title, summary = package_copy(needs)
    return [
        b.build_package("pkg-1", title, summary, top_a, 94),
        b.build_package("pkg-2", "회복·자립 패키지", "단기 지원 이후 남은 욕구를 이어서 연결하는 조합", top_b, 88),
        b.build_package("pkg-3", "지역기관 연계 패키지", "공공 제도와 민간·지역기관 접점을 병합", top_c, 83),
    ]


def apply() -> None:
    b.fetch_public_welfare_services = fetch_public_welfare_services
    b.target_compatible = target_compatible
    b.service_score = service_score
    b.filter_local_services = filter_local_services
    b.generate_packages = generate_packages
    b.RECOMMENDATION_RELEVANCE_PATCH_APPLIED = True
