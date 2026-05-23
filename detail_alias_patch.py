from __future__ import annotations

import backend_server as b


DETAIL_ALIASES: dict[str, tuple[str, str]] = {
    "svc-4": ("중앙", "WLF00004661"),
    "청년월세 한시 특별지원": ("중앙", "WLF00004661"),
    "청년월세 지원사업": ("중앙", "WLF00004661"),
    "svc-7": ("중앙", "WLF00003245"),
    "국민취업지원제도": ("중앙", "WLF00003245"),
    "국민취업지원": ("중앙", "WLF00003245"),
}


def apply() -> None:
    try:
        import backend_runtime_patch

        backend_runtime_patch.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
    except Exception as error:
        print(f"Runtime detail aliases skipped: {error}")

    if hasattr(b, "PUBLIC_DETAIL_ALIASES"):
        b.PUBLIC_DETAIL_ALIASES.update(DETAIL_ALIASES)
    b.DETAIL_ALIAS_PATCH_APPLIED = True
