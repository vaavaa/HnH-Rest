"""Compiled constraints cache — normalised representation per Prompt Spec v1, LRU-bounded."""

from collections import OrderedDict
from threading import Lock
from typing import Any


def _sort_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively sort dict keys for canonical form."""
    return {k: _sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}


_CACHE_MAXSIZE = 256
_cache: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
_lock = Lock()


def get_compiled_constraints(template_id: str, semver: str, raw_constraints: dict[str, Any] | None) -> dict[str, Any]:
    """
    Return normalised (compiled) constraints for a template, from cache or by normalising.
    Keyed by (template_id, semver). LRU eviction when over maxsize.
    """
    key = (template_id, semver)
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
        compiled = _sort_dict(raw_constraints) if raw_constraints else {}
        _cache[key] = compiled
        if len(_cache) > _CACHE_MAXSIZE:
            _cache.popitem(last=False)
        return compiled
