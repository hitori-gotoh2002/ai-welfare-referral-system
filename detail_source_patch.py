from __future__ import annotations

from typing import Any

import backend_server as b


DETAIL_TEMPLATE_VERSION = "api-field-detail-template-v2"


def clean(value: Any) -> str:
    return b.clean_text(str(value or ""))


def first_clean_field(service: dict[str, Any], *keys: str) -> tuple[str, str]:
    for key in keys:
        value = clean(service.get(key))
        if value:
            return value, key
    return "", ""


def selected_services(package: dict[str, Any], catalog: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in package.get("items", []):
        if not item.get("included", True):
            continue
        service = b.find_service(item.get("serviceId", ""), catalog)
        if service:
            result.append(service)
    return result


def normalize_service(service: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(service)
    normalized["id"] = normalized.get("id") or normalized.get("serviceId") or normalized.get("externalId") or clean(normalized.get("name"))
    normalized["name"] = clean(normalized.get("name")) or "복지서비스"
    normalized["source"] = clean(normalized.get("source")) or "공공"
    normalized["region"] = clean(normalized.get("region")) or "전국"
    normalized["domains"] = list(normalized.get("domains") or [])
    normalized["urgency"] = clean(normalized.get("urgency")) or "일반"
    normalized["summary"] = clean(normalized.get("summary") or normalized.get("description"))
    normalized["eligibility"] = clean(normalized.get("eligibility") or normalized.get("selectionCriteria") or normalized.get("target"))
    normalized["support"] = clean(normalized.get("support") or normalized.get("description") or normalized.get("summary"))
    normalized["process"] = clean(normalized.get("process") or normalized.get("applicationProcess") or normalized.get("applyMethod"))
    normalized["docs"] = list(normalized.get("docs") or normalized.get("requiredDocs") or [])
    normalized["contact"] = clean(normalized.get("contact") or normalized.get("phone") or normalized.get("department")) or "관할 주민센터 또는 담당 기관"
    normalized["url"] = clean(normalized.get("url") or normalized.get("detailUrl") or normalized.get("officialUrl")) or "https://www.bokjiro.go.kr"
    normalized["detailUrl"] = clean(normalized.get("detailUrl") or normalized.get("url") or normalized.get("officialUrl"))
    normalized["updated"] = clean(normalized.get("updated"))
    normalized["group"] = normalized.get("group") or normalized["id"]
    return normalized


def normalize_catalog(catalog: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if catalog is None:
        return None
    return [normalize_service(service) for service in catalog]


def filter_package_for_region(
    package: dict[str, Any],
    catalog: list[dict[str, Any]] | None,
    case: dict[str, Any],
    structured: dict[str, Any] | None,
) -> dict[str, Any]:
    region = clean(case.get("region") or (structured or {}).get("region"))
    compatible = getattr(b, "is_region_compatible", None)
    if not region or not callable(compatible):
        return package

    filtered_items = []
    for item in package.get("items", []):
        service = b.find_service(item.get("serviceId", ""), catalog)
        if service is None or compatible(service, region, structured):
            filtered_items.append(item)
    return {**package, "items": filtered_items}


def build_detail(service: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    service = normalize_service(service)
    existing = existing or {}
    domains = service.get("domains") or []
    name = clean(service.get("name")) or clean(existing.get("service"))
    selection, selection_source = first_clean_field(service, "selectionCriteria", "eligibility", "target", "targetDescription")
    support, support_source = first_clean_field(service, "support", "summary", "description")
    process, process_source = first_clean_field(service, "process", "applicationProcess", "applyMethod")
    contact, contact_source = first_clean_field(service, "contact", "phone", "department")
    official_url, url_source = first_clean_field(service, "detailUrl", "url")
    laws = list(service.get("laws") or existing.get("legalBasis") or [])
    if not laws:
        if "긴급" in clean(service.get("urgency")) or "긴급복지" in name:
            laws = ["긴급복지지원법 및 같은 법 시행령"]
        elif "기초" in name or "생계" in domains:
            laws = ["국민기초생활 보장법 및 사회보장급여 관련 공통서식에 관한 고시"]
        elif "고용" in name or "취업" in domains:
            laws = ["고용정책 기본법 및 국민취업지원제도 운영 관련 고시"]
        else:
            laws = ["사회보장급여의 이용ㆍ제공 및 수급권자 발굴에 관한 법률"]

    docs = b.unique(
        [
            *(service.get("docs") or existing.get("requiredDocs") or []),
            "사회보장급여 신청(변경)서",
            "신분증",
            "소득ㆍ재산 확인자료",
            "가구원 및 거주 사실 확인자료",
        ]
    )
    steps = b.unique(
        [
            *(service.get("applicationSteps") or existing.get("applicationSteps") or []),
            process,
            "주소지 읍면동 주민센터 또는 해당 접수기관 상담",
            "신청서 및 증빙서류 제출",
            "소득ㆍ재산ㆍ위기사유 등 자격 확인",
            "보장 결정 통지 및 급여ㆍ서비스 연계",
        ]
    )
    field_map = {
        "selectionCriteria": selection_source or "template-fallback",
        "support": support_source or "template-fallback",
        "applicationSteps": process_source or "standard-procedure-template",
        "requiredDocs": "docs" if service.get("docs") else "standard-document-template",
        "legalBasis": "laws" if service.get("laws") else "domain-law-template",
        "contact": contact_source or "catalog-fallback",
        "officialUrl": url_source or "missing",
    }
    fallback_markers = {
        "template-fallback",
        "standard-procedure-template",
        "standard-document-template",
        "domain-law-template",
        "catalog-fallback",
        "missing",
    }
    api_field_count = sum(1 for value in field_map.values() if value not in fallback_markers)
    confidence = "high" if api_field_count >= 4 and official_url else "medium" if api_field_count >= 2 else "template-assisted"
    return {
        **existing,
        "service": name,
        "selectionCriteria": selection or clean(existing.get("selectionCriteria")),
        "support": support or clean(existing.get("support")),
        "applicationSteps": [item for item in steps if item],
        "requiredDocs": docs,
        "legalBasis": laws,
        "contact": contact or clean(existing.get("contact")),
        "officialUrl": official_url or clean(existing.get("officialUrl")),
        "detailSource": {
            "mode": "public-data-api-first-with-standard-template-fallback",
            "templateVersion": DETAIL_TEMPLATE_VERSION,
            "confidence": confidence,
            "source": clean(service.get("source")),
            "region": clean(service.get("region")),
            "updated": clean(service.get("updated")),
            "fieldMap": field_map,
            "notice": "공공데이터/복지서비스 API 필드를 우선 사용하고, API에 비어 있는 항목만 표준 신청 절차 템플릿으로 보강합니다.",
        },
    }


def apply() -> None:
    if getattr(b, "DETAIL_SOURCE_PATCH_APPLIED", False):
        return

    original_build_report = b.build_report

    def build_report(
        case: dict[str, Any],
        structured: dict[str, Any] | None,
        package: dict[str, Any],
        catalog: list[dict[str, Any]] | None = None,
        providers: list[dict[str, Any]] | None = None,
    ):
        normalized_catalog = normalize_catalog(catalog)
        safe_package = filter_package_for_region(package, normalized_catalog, case, structured)
        report = original_build_report(case, structured, safe_package, normalized_catalog, providers)
        services = selected_services(safe_package, normalized_catalog)
        existing_by_name = {clean(item.get("service")): item for item in report.get("serviceDetails", []) if isinstance(item, dict)}
        report["serviceDetails"] = [build_detail(service, existing_by_name.get(clean(service.get("name")))) for service in services]
        report["detailTemplateVersion"] = DETAIL_TEMPLATE_VERSION
        return report

    b.build_report = build_report
    b.DETAIL_SOURCE_PATCH_APPLIED = True
