#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

_MARKERS = ("SKILL.md", ".env")

def skill_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here):
        if any((candidate / marker).is_file() for marker in _MARKERS):
            return candidate
    return here.parent

def setup_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            if stream.isatty():
                reconfigure(errors="replace")
            else:
                reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
