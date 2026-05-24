from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlparse

import backend_server as b


BOKJIRO_DETAIL_BASE = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do"
WELFARE_ID_RE = re.compile(r"\bWLF[0-9A-Za-z_-]+\b")


def bokjiro_detail_url(service_id: str) -> str:
    return f"{BOKJIRO_DETAIL_BASE}?wlfareInfoId={quote(str(service_id), safe='')}"


def is_bokjiro_main_url(url: str) -> bool:
    value = str(url or "").strip().rstrip("/")
    return value in {"https://www.bokjiro.go.kr", "http://www.bokjiro.go.kr", "https://bokjiro.go.kr", "http://bokjiro.go.kr"}


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
