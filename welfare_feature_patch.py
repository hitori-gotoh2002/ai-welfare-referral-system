from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import backend_server as b

SIDO_ALIASES = {
    "서울특별시": "서울", "서울시": "서울", "서울": "서울",
    "부산광역시": "부산", "부산시": "부산", "부산": "부산",
    "대구광역시": "대구", "대구시": "대구", "대구": "대구",
    "인천광역시": "인천", "인천시": "인천", "인천": "인천",
    "광주광역시": "광주", "광주시": "광주", "광주": "광주",
    "대전광역시": "대전", "대전시": "대전", "대전": "대전",
    "울산광역시": "울산", "울산시": "울산", "울산": "울산",
    "세종특별자치시": "세종", "세종시": "세종", "세종": "세종",
    "경기도": "경기", "경기": "경기",
    "강원특별자치도": "강원", "강원도": "강원", "강원": "강원",
    "충청북도": "충북", "충북": "충북",
    "충청남도": "충남", "충남": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전북": "전북",
    "전라남도": "전남", "전남": "전남",
    "경상북도": "경북", "경북": "경북",
    "경상남도": "경남", "경남": "경남",
    "제주특별자치도": "제주", "제주도": "제주", "제주": "제주",
}
NATIONWIDE = {"", "전국", "중앙", "공통", "온라인", "복지로", "정부24"}
LOCAL_SOURCES = {"지자체", "광역", "기초", "시군구"}
COMMON_FORM_URL = "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=14600000275"


def clean(value: Any) -> str:
    return b.clean_text(str(value or ""))


def normalize_region_name(region: Any) -> tuple[str, str]:
    value = re.sub(r"\s+", " ", clean(region)).strip()
    if not value:
        return "", ""
    if value in NATIONWIDE:
        return "전국", ""
    tokens = value.split()
    sido = SIDO_ALIASES.get(tokens[0], "")
    sigungu = tokens[1] if len(tokens) > 1 else ""
    if not sido:
        for alias, canonical in sorted(SIDO_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            if value.startswith(alias):
                sido = canonical
                sigungu = value[len(alias):].strip().split(" ")[0] if value[len(alias):].strip() else ""
                break
    if not sido and len(tokens) == 1:
        bare = re.sub(r"(특별시|광역시|특별자치시|특별자치도|자치도|도|시)$", "", tokens[0])
        sido = SIDO_ALIASES.get(bare, bare)
    sigungu = re.sub(r"(특례시|시|군|구)$", "", sigungu)
    return sido, sigungu


def is_region_compatible(service: dict[str, Any] | None, case_region: Any, structured: dict[str, Any] | None = None) -> bool:
    if not isinstance(service, dict):
        return False
    requested = clean(case_region) or clean((structured or {}).get("region"))
    service_region = clean(service.get("region"))
    service_source = clean(service.get("source"))
    if service_region in NATIONWIDE or service_source == "중앙":
        return True
    if not requested:
        return service_source not in LOCAL_SOURCES
    case_sido, case_sigungu = normalize_region_name(requested)
    service_sido, service_sigungu = normalize_region_name(service_region)
    if service_sido in {"", "전국"}:
        return service_source not in LOCAL_SOURCES
    if not case_sido or service_sido != case_sido:
        return False
    if service_sigungu and case_sigungu:
        return service_sigungu == case_sigungu or service_sigungu in case_sigungu or case_sigungu in service_sigungu
    return True


def selected_services(package: dict[str, Any], catalog: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    services = []
    for item in package.get("items", []):
        if item.get("included", True):
            service = b.find_service(item.get("serviceId", ""), catalog)
            if service:
                services.append(service)
    return services


def service_detail_template(service: dict[str, Any]) -> dict[str, Any]:
    name = clean(service.get("name"))
    laws = list(service.get("laws") or [])
    if not laws:
        if "긴급" in clean(service.get("urgency")) or "긴급복지" in name:
            laws = ["긴급복지지원법 및 같은 법 시행령"]
        elif "취업" in (service.get("domains") or []) or "고용" in name:
            laws = ["고용정책 기본법 및 국민취업지원제도 운영 관련 고시"]
        else:
            laws = ["사회보장급여의 이용ㆍ제공 및 수급권자 발굴에 관한 법률"]
    return {
        "service": name,
        "selectionCriteria": clean(service.get("selectionCriteria")) or clean(service.get("eligibility")),
        "support": clean(service.get("support")),
        "applicationSteps": b.unique([clean(service.get("process")), "주소지 읍면동 주민센터 또는 해당 접수기관 상담", "신청서 및 증빙서류 제출", "자격 확인 후 보장 결정 통지"]),
        "requiredDocs": b.unique([*(service.get("docs") or []), "사회보장급여 신청(변경)서", "신분증", "소득ㆍ재산 확인자료", "가구원 및 거주 사실 확인자료"]),
        "legalBasis": laws,
        "officialUrl": clean(service.get("detailUrl") or service.get("url")),
    }


def fallback_application_draft(case: dict[str, Any], structured: dict[str, Any], services: list[dict[str, Any]]) -> str:
    target = clean(case.get("targetType") or structured.get("target") or "대상자")
    region = clean(case.get("region") or structured.get("region") or "거주지")
    needs = structured.get("needs") or case.get("issueTypes") or []
    service_names = ", ".join(clean(service.get("name")) for service in services[:4] if service.get("name"))
    memo = clean(case.get("memo"))[:220] or "상담 과정에서 생계ㆍ주거ㆍ의료 등 복합적인 복지 욕구가 확인되었습니다."
    return f"신청인은 {region}에 거주하는 {target}로, 상담 결과 {', '.join(needs) or '복지급여'} 관련 지원 필요성이 확인되었습니다. {memo} 위와 같은 사유로 현재 가구의 생활 안정과 위기 완화를 위하여 {service_names or '해당 복지급여'}의 제공을 신청하고자 합니다. 제출 서류와 소득ㆍ재산 및 가구 구성 확인 절차에 성실히 협조하겠습니다."


def llm_application_draft(case: dict[str, Any], structured: dict[str, Any], services: list[dict[str, Any]], fallback: str) -> tuple[str, bool]:
    if not getattr(b, "GEMINI_API_KEY", "") or not services:
        return fallback, False
    prompt = f"""
공식 복지 신청서의 [신청 사유] 란에 붙여넣을 격식체 문단을 작성한다.
허위 사실, 확정되지 않은 수급 가능성, 개인정보 원문 노출은 금지한다.
180~350자 한국어 문단 하나만 JSON으로 반환한다.
반환 형식: {{"applicationDraft": "..."}}
상담 사례: {json.dumps(case, ensure_ascii=False)}
구조화 결과: {json.dumps(structured, ensure_ascii=False)}
신청 후보 서비스: {json.dumps([service_detail_template(service) for service in services[:5]], ensure_ascii=False)}
"""
    try:
        data = b.call_gemini_json(prompt, temperature=0.2)
        draft = clean(data.get("applicationDraft"))
        return draft or fallback, bool(draft)
    except Exception:
        return fallback, False


def enrich_report(report: dict[str, Any], case: dict[str, Any], structured: dict[str, Any], package: dict[str, Any], catalog: list[dict[str, Any]] | None) -> dict[str, Any]:
    services = selected_services(package, catalog)
    fallback = fallback_application_draft(case, structured, services)
    draft, used_llm = llm_application_draft(case, structured, services, fallback)
    official_links = b.unique([
        {"label": "사회보장급여 신청(변경) 민원 안내", "url": COMMON_FORM_URL, "type": "common-form"},
        *[{"label": f"{service.get('name', '복지서비스')} 공고/상세", "url": clean(service.get("detailUrl") or service.get("url") or COMMON_FORM_URL), "type": "service-detail"} for service in services],
    ])
    return {
        **report,
        "applicationDraft": draft,
        "applicationDraftLlmUsed": used_llm,
        "serviceDetails": [service_detail_template(service) for service in services],
        "officialLinks": official_links,
        "hwpGuide": {
            "formName": "사회보장급여 신청(변경)서 [별지 제1호서식]",
            "applicantName": "신청인 성명란에 대상자 또는 대리 신청인 성명을 기재",
            "residentNoMasked": "주민등록번호는 앞 6자리와 뒤 첫 자리 확인 후 마스킹 보관",
            "address": clean(case.get("region") or structured.get("region") or ""),
            "services": [clean(service.get("name")) for service in services if service.get("name")],
            "householdType": clean(case.get("targetType") or structured.get("target") or ""),
            "applicationReason": draft,
        },
    }


def install_region_wrappers() -> None:
    original_service_score = b.service_score
    def service_score(service: dict[str, Any], needs: list[str], case: dict[str, Any], structured: dict[str, Any] | None = None) -> int:
        if not is_region_compatible(service, case.get("region"), structured):
            return 0
        return original_service_score(service, needs, case, structured)
    b.service_score = service_score

    original_filter_services = b.filter_services
    def filter_services(query: dict[str, list[str]]):
        services, meta = original_filter_services(query)
        region = (query.get("region", [""])[0] or "").strip()
        if region:
            before = len(services)
            services = [service for service in services if is_region_compatible(service, region)]
            meta = {**meta, "regionFilter": {"region": region, "removed": before - len(services), "strict": True}}
        return services, meta
    b.filter_services = filter_services

    original_generate_packages = b.generate_packages
    def generate_packages(case: dict[str, Any], structured: dict[str, Any] | None, catalog: list[dict[str, Any]] | None = None):
        region = case.get("region") or (structured or {}).get("region") or ""
        filtered_catalog = [service for service in catalog if is_region_compatible(service, region, structured)] if catalog and region else catalog
        packages = original_generate_packages(case, structured, filtered_catalog)
        for package in packages:
            package["items"] = [item for item in package.get("items", []) if not region or is_region_compatible(b.find_service(item.get("serviceId", ""), filtered_catalog), region, structured)]
        return packages
    b.generate_packages = generate_packages


def install_report_wrapper() -> None:
    original_build_report = b.build_report
    def build_report(case: dict[str, Any], structured: dict[str, Any] | None, package: dict[str, Any], catalog: list[dict[str, Any]] | None = None, providers: list[dict[str, Any]] | None = None):
        structured_result = structured or b.analyze_case(case)
        report = original_build_report(case, structured_result, package, catalog, providers)
        return enrich_report(report, case, structured_result, package, catalog)
    b.build_report = build_report


def install_http_helpers() -> None:
    native_do_get = b.WelfareHandler.do_GET
    def patched_do_get(self):
        parsed = urlparse(self.path)
        if parsed.path == "/dashboard-hwp-patch.js":
            body = (b.ROOT / "dashboard-hwp-patch.js").read_bytes()
            self.send_response(b.HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return native_do_get(self)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/cases/"):
            case_id = parsed.path.rsplit("/", 1)[-1]
            before_saved, before_recent = len(b.SAVED_CASES), len(b.RECENT_CASES)
            b.SAVED_CASES[:] = [item for item in b.SAVED_CASES if item.get("id") != case_id]
            b.RECENT_CASES[:] = [item for item in b.RECENT_CASES if item.get("id") != case_id]
            deleted = before_saved != len(b.SAVED_CASES) or before_recent != len(b.RECENT_CASES)
            return self.write_json({"ok": True, "deleted": deleted, "id": case_id, "time": datetime.now().isoformat()})
        return self.write_json({"error": "not_found"}, b.HTTPStatus.NOT_FOUND)

    b.WelfareHandler.do_GET = patched_do_get
    b.WelfareHandler.do_DELETE = do_DELETE


def apply() -> None:
    if getattr(b, "WELFARE_FEATURE_PATCH_APPLIED", False):
        return
    install_region_wrappers()
    install_report_wrapper()
    install_http_helpers()
    b.is_region_compatible = is_region_compatible
    b.normalize_region_name = normalize_region_name
    b.WELFARE_FEATURE_PATCH_APPLIED = True
