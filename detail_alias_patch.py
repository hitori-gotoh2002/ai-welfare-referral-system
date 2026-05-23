from __future__ import annotations

import backend_server as b


DETAIL_ALIASES: dict[str, tuple[str, str]] = {
    "svc-2": ("중앙", "WLF00002235"),
    "서울형 긴급복지": ("중앙", "WLF00002235"),
    "서울형 긴급복지지원": ("중앙", "WLF00002235"),
    "svc-4": ("중앙", "WLF00004661"),
    "청년월세 한시 특별지원": ("중앙", "WLF00004661"),
    "청년월세 지원사업": ("중앙", "WLF00004661"),
    "svc-5": ("중앙", "WLF00004671"),
    "청년 마음건강 지원사업": ("중앙", "WLF00004671"),
    "청년마음건강지원사업": ("중앙", "WLF00004671"),
    "svc-7": ("중앙", "WLF00003245"),
    "국민취업지원제도": ("중앙", "WLF00003245"),
    "국민취업지원": ("중앙", "WLF00003245"),
    "svc-9": ("중앙", "WLF00003179"),
    "의료비 긴급지원": ("중앙", "WLF00003179"),
    "긴급복지 의료지원": ("중앙", "WLF00003179"),
}


def should_skip_bokjiro_detail(service: dict) -> bool:
    if service.get("id") in DETAIL_ALIASES or service.get("name") in DETAIL_ALIASES:
        return False
    source = service.get("source", "")
    service_id = str(service.get("id", ""))
    url = str(service.get("url", ""))
    return source in ("중앙", "지자체") and service_id.startswith("svc-") and url and "bokjiro.go.kr" not in url


def install_fetch_wrapper() -> None:
    original = getattr(b, "_DETAIL_ALIAS_ORIGINAL_FETCH", None) or b.fetch_public_welfare_detail
    b._DETAIL_ALIAS_ORIGINAL_FETCH = original

    def fetch_public_welfare_detail(service: dict):
        if should_skip_bokjiro_detail(service):
            return service, {
                "enabled": True,
                "detail": False,
                "reason": "external_portal_detail",
                "source": service.get("url", ""),
            }
        return original(service)

    b.fetch_public_welfare_detail = fetch_public_welfare_detail


def apply() -> None:
    try:
        import backend_runtime_patch

        backend_runtime_patch.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
    except Exception as error:
        print(f"Runtime detail aliases skipped: {error}")

    if hasattr(b, "PUBLIC_DETAIL_ALIASES"):
        b.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
    if hasattr(b, "fetch_public_welfare_detail"):
        install_fetch_wrapper()
    b.DETAIL_ALIAS_PATCH_APPLIED = True
