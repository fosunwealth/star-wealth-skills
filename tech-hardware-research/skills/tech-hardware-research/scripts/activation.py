#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single activation check for this skill. The verdict lives in fintrust_gate."""

import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from fintrust_gate import check_activation, guide_text  # noqa: E402

_ACTIVATION = None


def require_api_key():
    global _ACTIVATION
    if _ACTIVATION is None:
        _ACTIVATION = check_activation()
    result = _ACTIVATION
    if result.get("activated"):
        return result
    print(result.get("guide") or result.get("reason") or guide_text(), file=sys.stderr)
    raise SystemExit(int(result["exit_code"]))
