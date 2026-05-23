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
    b.fetch_public_welfare_detail = fetch_public_welfare_detail
    b.RUNTIME_PATCH_APPLIED = True

    native_do_get = b.WelfareHandler.do_GET

    def patched_do_get(self):
        parsed = urlparse(self.path)
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
