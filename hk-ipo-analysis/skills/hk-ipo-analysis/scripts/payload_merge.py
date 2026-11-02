#!/usr/bin/env python3

from __future__ import annotations

from typing import Any

def is_blank(value: Any) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    return False

def merge_prefer(primary: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(base or {})
    for key, value in (primary or {}).items():
        current = out.get(key)
        if isinstance(value, dict) and isinstance(current, dict):
            out[key] = merge_prefer(value, current)
        elif not is_blank(value):
            out[key] = value
    return out
