from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlencode, urlparse

import backend_server as b


BOKJIRO_DETAIL_BASE = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do"
WELFARE_ID_RE = re.compile(r"\bWLF[0-9A-Za-z_-]+\b")
BOKJIRO_HOSTS = {"www.bokjiro.go.kr", "bokjiro.go.kr"}
MAIN_URL_HOSTS = {
    "wis.seoul.go.kr",
    "www.myhome.go.kr",
    "myhome.go.kr",
    "www.socialservice.or.kr",
    "socialservice.or.kr",
    "www.mentalhealth.go.kr",
    "mentalhealth.go.kr",
    "www.work24.go.kr",
    "work24.go.kr",
    "www.foodbank1377.org",
    "foodbank1377.org",
    "www.kyci.or.kr",
    "kyci.or.kr",
    "www.nhis.or.kr",
    "nhis.or.kr",
    "www.ableservice.or.kr",
    "ableservice.or.kr",
    "longtermcare.or.kr",
    "www.longtermcare.or.kr",
    "www.cjagis.go.kr",
    "cjagis.go.kr",
}
EXTERNAL_DETAIL_URLS_BY_ID = {
    "svc-2": "https://wis.seoul.go.kr/wfs/sos/urgencySupport.do?crtId=PLP01020302",
    "svc-3": "https://www.myhome.go.kr/hws/portal/cont/selectSupResidentsAbnormalView.do",
    "svc-5": "https://www.socialservice.or.kr/user/htmlEditor/view2.do?p_sn=8",
    "svc-6": "https://www.mentalhealth.go.kr/portal/disease/diseaseDetail.do?dissId=67",
    "svc-7": "https://www.work24.go.kr/ua/z/z/1300/selectEmssRqutIntro.do?intro=8",
    "svc-8": "https://www.foodbank1377.org/introduce/organize.do",
    "svc-10": "https://www.kyci.or.kr/userSite/sub02_1_cont.asp",
    "svc-12": "https://www.myhome.go.kr/hws/portal/cont/selectHousingBenefitView.do",
    "svc-16": "https://www.nhis.or.kr/static/html/wbma/c/wbmac0222.html",
    "svc-17": "https://www.ableservice.or.kr/regm/info/getOHGC0005M0.do",
    "svc-19": "https://www.longtermcare.or.kr/npbs/e/b/101/npeb101m01.web?menuId=npe0000000030",
}
EXTERNAL_DETAIL_RULES = (
    (("서울형 긴급복지", "서울형긴급복지"), "https://wis.seoul.go.kr/wfs/sos/urgencySupport.do?crtId=PLP01020302"),
    (("주거취약", "주거상향"), "https://www.myhome.go.kr/hws/portal/cont/selectSupResidentsAbnormalView.do"),
    (("주거급여",), "https://www.myhome.go.kr/hws/portal/cont/selectHousingBenefitView.do"),
    (("청년 마음건강", "청년마음건강", "마음건강"), "https://www.socialservice.or.kr/user/htmlEditor/view2.do?p_sn=8"),
    (("정신건강복지센터", "정신건강 상담"), "https://www.mentalhealth.go.kr/portal/disease/diseaseDetail.do?dissId=67"),
    (("국민취업지원", "취업지원제도"), "https://www.work24.go.kr/ua/z/z/1300/selectEmssRqutIntro.do?intro=8"),
    (("푸드마켓", "푸드뱅크"), "https://www.foodbank1377.org/introduce/organize.do"),
    (("위기청소년", "청소년안전망", "청소년 통합지원"), "https://www.kyci.or.kr/userSite/sub02_1_cont.asp"),
    (("재난적의료비",), "https://www.nhis.or.kr/static/html/wbma/c/wbmac0222.html"),
    (("장애인 활동지원", "장애인활동지원"), "https://www.ableservice.or.kr/regm/info/getOHGC0005M0.do"),
    (("노인장기요양", "장기요양보험"), "https://www.longtermcare.or.kr/npbs/e/b/101/npeb101m01.web?menuId=npe0000000030"),
)


def bokjiro_detail_url(service_id: str) -> str:
    return f"{BOKJIRO_DETAIL_BASE}?wlfareInfoId={quote(str(service_id), safe='')}"


def is_bokjiro_main_url(url: str) -> bool:
    value = str(url or "").strip().rstrip("/")
    return value in {"https://www.bokjiro.go.kr", "http://www.bokjiro.go.kr", "https://bokjiro.go.kr", "http://bokjiro.go.kr"}


def host_of(url: str) -> str:
    try:
        return urlparse(str(url or "")).netloc.lower()
    except Exception:
        return ""


def is_portal_main_url(url: str) -> bool:
    value = str(url or "").strip().rstrip("/")
    if is_bokjiro_main_url(value):
        return True
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return host in MAIN_URL_HOSTS and path in {"", "/", "/main.do", "/index.do"}


def official_search_url(service: dict[str, Any]) -> str:
    current_url = str(service.get("url") or "")
    host = host_of(current_url)
    query = str(service.get("name") or service.get("publicDetailName") or "").strip()
    if not query:
        return ""
    if host in {"www.work24.go.kr", "work24.go.kr"}:
        return "https://www.work24.go.kr/cm/f/c/0100/selectUnifySearch.do?" + urlencode(
            {"topQueryData": query, "topQuerySearchArea": "all"}
        )
    if host in {"www.socialservice.or.kr", "socialservice.or.kr"}:
        return "https://m.socialservice.or.kr/srch/svc/arndList.do"
    return ""


def external_detail_url(service: dict[str, Any]) -> str:
    service_id = str(service.get("id") or "").strip()
    if service_id in EXTERNAL_DETAIL_URLS_BY_ID:
        return EXTERNAL_DETAIL_URLS_BY_ID[service_id]

    text = " ".join(
        str(service.get(key) or "")
        for key in ("name", "publicDetailName", "summary", "support", "target", "contact")
    )
    for keywords, url in EXTERNAL_DETAIL_RULES:
        if any(keyword and keyword in text for keyword in keywords):
            return url
    return official_search_url(service)


def extract_welfare_id(service: dict[str, Any]) -> str:
    candidates: list[str] = []
    for key in ("externalId", "publicMatchedId", "id", "url", "detailUrl"):
        value = str(service.get(key) or "").strip()
        if value:
            candidates.append(value)

    try:
        import detail_alias_patch

        _, alias_id = detail_alias_patch.public_detail_identity(service)
        if alias_id:
            candidates.insert(0, str(alias_id))
    except Exception:
        pass

    for value in candidates:
        match = WELFARE_ID_RE.search(value)
        if match:
            return match.group(0)
    return ""


def ensure_service_detail_url(service: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(service, dict):
        return service

    result = {**service}
    external_url = external_detail_url(result)
    if external_url:
        result["detailUrl"] = external_url
        result["officialUrl"] = external_url
        result["isDetailUrl"] = True
        current_url = str(result.get("url") or "").strip()
        if not current_url or is_portal_main_url(current_url) or host_of(current_url) not in BOKJIRO_HOSTS:
            result["url"] = external_url
        return result

    welfare_id = extract_welfare_id(result)
    if not welfare_id:
        return result

    detail_url = bokjiro_detail_url(welfare_id)
    result["detailUrl"] = detail_url
    result["isDetailUrl"] = True
    current_url = str(result.get("url") or "").strip()
    if not current_url or is_bokjiro_main_url(current_url):
        result["url"] = detail_url
    return result


def apply() -> None:
    if getattr(b, "WELFARE_LINK_PATCH_APPLIED", False):
        return

    original_fetch = getattr(b, "fetch_public_welfare_detail", None)
    if callable(original_fetch):
        b._WELFARE_LINK_ORIGINAL_FETCH = original_fetch

        def fetch_public_welfare_detail(service: dict[str, Any]):
            detail, meta = original_fetch(service)
            return ensure_service_detail_url(detail), meta

        b.fetch_public_welfare_detail = fetch_public_welfare_detail

    original_normalize = getattr(b, "normalize_public_service", None)
    if callable(original_normalize):
        b._WELFARE_LINK_ORIGINAL_NORMALIZE = original_normalize

        def normalize_public_service(element: Any, source: str) -> dict[str, Any]:
            return ensure_service_detail_url(original_normalize(element, source))

        b.normalize_public_service = normalize_public_service

    for service in getattr(b, "SERVICES", []):
        service.update(ensure_service_detail_url(service))

    native_do_get = b.WelfareHandler.do_GET

    def patched_do_get(self):
        parsed = urlparse(self.path)
        if parsed.path == "/case-loading-link-patch.js":
            body = (b.ROOT / "case-loading-link-patch.js").read_bytes()
            self.send_response(b.HTTPStatus.OK)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return native_do_get(self)

    b.WelfareHandler.do_GET = patched_do_get

    b.WELFARE_LINK_PATCH_APPLIED = True
