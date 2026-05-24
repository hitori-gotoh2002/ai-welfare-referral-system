from __future__ import annotations

import builtins
from types import ModuleType
from typing import Any


_original_import = builtins.__import__


def _wrap_runtime_patch(module: ModuleType) -> ModuleType:
    if getattr(module, "_RECOMMENDATION_RELEVANCE_WRAPPED", False):
        return module

    original_apply = getattr(module, "apply", None)
    if not callable(original_apply):
        return module

    def apply_with_recommendation(*args: Any, **kwargs: Any) -> Any:
        result = original_apply(*args, **kwargs)
        try:
            import recommendation_relevance_patch

            recommendation_relevance_patch.apply()
        except Exception as error:
            print(f"Recommendation relevance patch skipped: {error}")
        try:
            import detail_alias_patch

            detail_alias_patch.apply()
        except Exception as error:
            print(f"Detail alias patch skipped: {error}")
        try:
            import llm_enhancement_patch

            llm_enhancement_patch.apply()
        except Exception as error:
            print(f"LLM enhancement patch skipped: {error}")
        try:
            import rich_report_patch

            rich_report_patch.apply()
        except Exception as error:
            print(f"Rich report patch skipped: {error}")
        try:
            import welfare_link_patch

            welfare_link_patch.apply()
        except Exception as error:
            print(f"Welfare link patch skipped: {error}")
        return result

    module.apply = apply_with_recommendation
    module._RECOMMENDATION_RELEVANCE_WRAPPED = True
    return module


def _import_with_runtime_hook(name: str, globals: Any = None, locals: Any = None, fromlist: tuple[str, ...] = (), level: int = 0) -> Any:
    module = _original_import(name, globals, locals, fromlist, level)
    if level == 0 and name == "backend_runtime_patch":
        return _wrap_runtime_patch(module)
    return module


builtins.__import__ = _import_with_runtime_hook
