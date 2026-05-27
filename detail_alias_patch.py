from __future__ import annotations

import backend_server as b


SERVICE_DETAIL_REGISTRY: dict[str, dict[str, str]] = {
    "svc-1": {"source": "중앙", "externalId": "WLF00003180", "name": "긴급복지 생계지원"},
    "svc-2": {"source": "중앙", "externalId": "WLF00002235", "name": "서울형 긴급복지지원"},
    "svc-4": {"source": "중앙", "externalId": "WLF00004661", "name": "청년월세 지원사업"},
    "svc-5": {"source": "중앙", "externalId": "WLF00004671", "name": "청년마음건강지원사업"},
    "svc-7": {"source": "중앙", "externalId": "WLF00003245", "name": "국민취업지원제도"},
    "svc-9": {"source": "중앙", "externalId": "WLF00003179", "name": "긴급복지 의료지원"},
}
DETAIL_ALIASES: dict[str, tuple[str, str]] = {}
DETAIL_RESPONSE_CACHE: dict[str, tuple[dict, dict]] = {}


def rebuild_aliases() -> None:
    DETAIL_ALIASES.clear()
    for local_id, info in SERVICE_DETAIL_REGISTRY.items():
        identity = (info["source"], info["externalId"])
        DETAIL_ALIASES[local_id] = identity
        DETAIL_ALIASES[info["name"]] = identity

    DETAIL_ALIASES.update(
        {
            "서울형 긴급복지": ("중앙", "WLF00002235"),
            "청년월세 한시 특별지원": ("중앙", "WLF00004661"),
            "청년 마음건강 지원사업": ("중앙", "WLF00004671"),
            "국민취업지원": ("중앙", "WLF00003245"),
            "의료비 긴급지원": ("중앙", "WLF00003179"),
        }
    )


rebuild_aliases()


def public_detail_identity(service: dict) -> tuple[str, str]:
    parsed = b.parse_public_service_id(service.get("id", "")) if hasattr(b, "parse_public_service_id") else None
    if parsed:
        return parsed

    source = service.get("publicDataSource")
    external_id = service.get("externalId")
    if source in ("중앙", "지자체") and external_id:
        return source, external_id

    alias = DETAIL_ALIASES.get(service.get("id", "")) or DETAIL_ALIASES.get(service.get("name", ""))
    if alias:
        return alias

    service_source = service.get("source", "")
    if service_source in ("중앙", "지자체") and external_id:
        return service_source, external_id
    return service_source, external_id or service.get("id", "")


def enrich_service_identity(service: dict) -> dict:
    info = SERVICE_DETAIL_REGISTRY.get(service.get("id", ""))
    if not info:
        return service
    service["externalId"] = info["externalId"]
    service["publicDataSource"] = info["source"]
    service["publicDetailName"] = info["name"]
    return service


def enrich_local_services() -> None:
    for service in getattr(b, "SERVICES", []):
        enrich_service_identity(service)


def should_skip_bokjiro_detail(service: dict) -> bool:
    if service.get("id") in DETAIL_ALIASES or service.get("name") in DETAIL_ALIASES:
        return False
    if service.get("publicDataSource") in ("중앙", "지자체") and service.get("externalId"):
        return False
    source = service.get("source", "")
    service_id = str(service.get("id", ""))
    url = str(service.get("url", ""))
    return source in ("중앙", "지자체") and service_id.startswith("svc-") and url and "bokjiro.go.kr" not in url


def install_fetch_wrapper() -> None:
    original = getattr(b, "_DETAIL_ALIAS_ORIGINAL_FETCH", None) or b.fetch_public_welfare_detail
    b._DETAIL_ALIAS_ORIGINAL_FETCH = original

    def fetch_public_welfare_detail(service: dict):
        service = enrich_service_identity({**service})
        source, service_id = public_detail_identity(service)
        cache_key = f"{source}:{service_id or service.get('id', '')}"
        if cache_key in DETAIL_RESPONSE_CACHE:
            cached_detail, cached_meta = DETAIL_RESPONSE_CACHE[cache_key]
            return {**cached_detail}, {**cached_meta, "cached": True}

        if should_skip_bokjiro_detail(service):
            meta = {
                "enabled": True,
                "detail": False,
                "reason": "external_portal_detail",
                "source": service.get("url", ""),
            }
            DETAIL_RESPONSE_CACHE[cache_key] = ({**service}, meta)
            return service, meta

        detail, meta = original(service)
        if meta.get("detail") or meta.get("reason") == "external_portal_detail":
            DETAIL_RESPONSE_CACHE[cache_key] = ({**detail}, {**meta})
        return detail, meta

    b.fetch_public_welfare_detail = fetch_public_welfare_detail


def apply() -> None:
    enrich_local_services()
    try:
        import backend_runtime_patch

        backend_runtime_patch.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
        backend_runtime_patch.public_detail_identity = public_detail_identity
    except Exception as error:
        print(f"Runtime detail aliases skipped: {error}")

    if hasattr(b, "PUBLIC_DETAIL_ALIASES"):
        b.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
    if hasattr(b, "public_detail_identity"):
        b.public_detail_identity = public_detail_identity
    if hasattr(b, "fetch_public_welfare_detail"):
        install_fetch_wrapper()
    b.DETAIL_ALIAS_PATCH_APPLIED = True
