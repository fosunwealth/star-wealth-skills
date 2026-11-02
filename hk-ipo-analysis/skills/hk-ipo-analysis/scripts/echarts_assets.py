#!/usr/bin/env python3
from __future__ import annotations
import os
from pathlib import Path
HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
NODE_MODULES_RELATIVE = Path('node_modules') / 'echarts' / 'dist'
ECHARTS_FILE_NAMES = ('echarts.min.js', 'echarts.js')
_EOL = '\n'
_cache: str | None = None

def candidate_paths() -> list[Path]:
    found: list[Path] = []
    env = os.environ.get('ECHARTS_JS', '').strip()
    if env:
        found.append(Path(env).expanduser())
    for name in ECHARTS_FILE_NAMES:
        found.append(SKILL_ROOT / NODE_MODULES_RELATIVE / name)
    return found

def echarts_path() -> Path:
    tried: list[str] = []
    for path in candidate_paths():
        tried.append(str(path))
        if path.is_file():
            return path
    raise RuntimeError('echarts.min.js not found (the report inlines the chart library). Tried: ' + '; '.join(tried) + '. Run `npm install` in the skill root, or set ECHARTS_JS=<absolute path to echarts.min.js>.')

def echarts_source() -> str:
    global _cache
    if _cache is None:
        _cache = echarts_path().read_text(encoding='utf-8')
    return _cache

def inline_block() -> str:
    return _EOL + echarts_source() + _EOL
