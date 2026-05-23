from __future__ import annotations

from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree

import backend_server as b


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


def fetch_public_welfare_detail(service: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    service_key = b.get_public_data_key()
    if not service_key:
        return service, {"enabled": False, "reason": "missing_service_key"}

    source = service.get("source", "")
    service_id = service.get("externalId") or service.get("id", "")
    parsed = b.parse_public_service_id(service.get("id", ""))
    if parsed:
        source, service_id = parsed

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


def apply() -> None:
    b.xml_tag_name = xml_tag_name
    b.xml_text = xml_text
    b.xml_all_text = xml_all_text
    b.xml_items = xml_items
    b.fetch_public_welfare_detail = fetch_public_welfare_detail
