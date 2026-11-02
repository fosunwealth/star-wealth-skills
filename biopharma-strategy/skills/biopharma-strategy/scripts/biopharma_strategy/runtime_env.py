#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

ENV_SKIP = frozenset({"FINTRUST_API_KEY"})

def env_file() -> Path:
    root = Path(os.path.expanduser(os.environ.get("BIOPHARMA_ROOT", "~/.biopharma")))
    return root / ".env"

def load_runtime_env() -> Path | None:
    path = env_file()
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if not name or name in ENV_SKIP:
            continue
        os.environ.setdefault(name, value.strip().strip('"').strip("'"))
    return path
