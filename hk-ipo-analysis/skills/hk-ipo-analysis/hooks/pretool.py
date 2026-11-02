#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_ROOT = _HOOKS_DIR.parent
for _p in (str(_ROOT), str(_ROOT / 'scripts')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os_compat

_PLUGIN_ROOT_ENV = (
    'CODEBUDDY_PLUGIN_ROOT',
    'CLAUDE_PLUGIN_ROOT',
    'WORKBUDDY_PLUGIN_ROOT',
    'PLUGIN_ROOT',
)

_DENY = 'No network search or other bypass. Run this package only: run.sh list / run.sh report --codes <code> / run.sh render --codes <code> (Windows: py -3 scripts\\main.py).'

_WEB_VERBS = ('search', 'fetch', 'scrape', 'browse', 'read', 'crawl', 'research')
_WEB_NAMES = ('browser', 'googlesearch', 'searchweb', 'readwebpage', 'websearch', 'webfetch', 'imagesearch', 'entitysearch', 'encyclopedia')
_SHELL_MARKS = ('shell', 'bash', 'terminal', 'console', 'powershell', 'runcommand', 'execute')
_MUTATE_MARKS = ('write', 'edit', 'strreplace', 'multiedit', 'applypatch', 'patch', 'create')

_DENIED_CMDS = frozenset({'curl', 'wget', 'lynx', 'w3m', 'httpie', 'aria2c'})

_ALLOWED_WEB = ('websearch', 'webfetch')

def _norm_tool(name: str) -> str:
    return name.lower().replace(' ', '').replace('_', '').replace('-', '').replace('.', '')

def _match_any(name: str, marks: tuple[str, ...]) -> bool:
    return any(mark in name for mark in marks)

def classify_tool(tool_name: str) -> str:
    name = _norm_tool(tool_name)
    if not name:
        return ''
    if _match_any(name, _WEB_NAMES):
        return 'web'
    if 'web' in name and _match_any(name, _WEB_VERBS):
        return 'web'
    if _match_any(name, _SHELL_MARKS):
        return 'shell'
    if _match_any(name, _MUTATE_MARKS):
        return 'mutate'
    return ''

def _allowed_web(name: str) -> bool:
    return any(name.endswith(mark) for mark in _ALLOWED_WEB)

def _plugin_root() -> Path:
    for name in _PLUGIN_ROOT_ENV:
        raw = (os.getenv(name) or '').strip()
        if raw:
            return Path(raw).resolve()
    return _ROOT

def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except (OSError, ValueError):
        return False

def _tokens(command: str) -> list[str]:
    pieces: list[str] = []
    for chunk in command.replace('|', ' ').replace(';', ' ').split('&&'):
        pieces.extend(chunk.split())
    out: list[str] = []
    for token in pieces:
        cleaned = token.strip().strip('"').strip("'")
        if cleaned:
            out.append(cleaned)
    return out

def _denied_cmd(command: str) -> bool:
    for token in _tokens(command):
        name = token.replace('\\', '/').rsplit('/', 1)[-1].lower()
        if name in _DENIED_CMDS:
            return True
    return False

def _tool_input(payload: dict) -> dict:
    for key in ('tool_input', 'toolInput'):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}

def _target_paths(tool_input: dict, payload: dict) -> list[Path]:
    out: list[Path] = []
    base = Path(str(payload.get('cwd') or os.getcwd()))
    for key in ('file_path', 'filePath', 'path', 'notebook_path'):
        raw = tool_input.get(key)
        if not isinstance(raw, str) or not raw.strip():
            continue
        candidate = Path(raw.strip())
        out.append(candidate if candidate.is_absolute() else base / candidate)
    return out

def _touches_plugin(payload: dict, plugin_root: Path, kind: str) -> bool:
    if kind == 'mutate':
        return any(_is_under(candidate, plugin_root) for candidate in _target_paths(_tool_input(payload), payload))
    tool_input = _tool_input(payload)
    command = str(tool_input.get('command') or '')
    if not command:
        return False
    if str(plugin_root) in command or any(mark in command for mark in ('run.sh', 'main.py', 'ipo.py', 'activation_gate.py', 'hk-ipo-analysis')):
        return True
    for candidate in _target_paths(tool_input, payload):
        if _is_under(candidate, plugin_root):
            return True
    base = Path(str(payload.get('cwd') or os.getcwd()))
    for token in _tokens(command):
        if token.startswith('-'):
            continue
        path = Path(token)
        candidate = path if path.is_absolute() or (os_compat.IS_WIN and ':' in token[:3]) else base / token
        if _is_under(candidate, plugin_root) and candidate.exists():
            return True
    return False

def _tool_name(payload: dict) -> str:
    return str(payload.get('tool_name') or payload.get('toolName') or '').strip()

def _deny(reason: str = _DENY) -> int:
    print(reason, file=sys.stderr)
    return 2

def main() -> int:
    os_compat.setup_console()
    try:
        payload = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0

    tool = _tool_name(payload)
    kind = classify_tool(tool)
    tool_input = _tool_input(payload)
    command = str(tool_input.get('command') or '')
    plugin_root = _plugin_root()

    if kind == 'web':
        if _allowed_web(_norm_tool(tool)):
            return 0
        return _deny()
    if kind == 'mutate' and _touches_plugin(payload, plugin_root, kind):
        targets = _target_paths(tool_input, payload)
        data_root = plugin_root / 'data'
        if targets and all(_is_under(path, data_root) for path in targets):
            return 0
        return _deny('Do not modify the source of this skill (the data surface and the gate both live inside the package). Write the payload only under this package: data/<code>/.')
    if kind == 'shell' and command and _denied_cmd(command):
        return _deny()

    if kind != 'shell' or not _touches_plugin(payload, plugin_root, kind):
        return 0

    json.dump(
        {
            'continue': True,
            'suppressOutput': True,
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'allow',
            },
        },
        sys.stdout,
        ensure_ascii=False,
    )
    return 0

if __name__ == '__main__':
    sys.exit(main())
