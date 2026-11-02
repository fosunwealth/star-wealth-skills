#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import client_common
import os_compat
from fintrust_gate import ensure_activated

EXIT_OK = 0
EXIT_DATA_FAILED = 6

def _items() -> list[dict[str, str]]:
    data = client_common.tool_json("ipo_list", {"source": "latest"}, timeout=60)
    inner = client_common.unwrap_capability(data)
    raw: list[Any] = inner.get("items") or [] if isinstance(inner, dict) else []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        code = client_common.norm_ipo_code(str(item.get("code") or item.get("symbol") or ""))
        if not code or not code.startswith("hk") or code in seen:
            continue
        seen.add(code)
        name = str(item.get("name") or item.get("stockName") or code).strip() or code
        out.append({"symbol": code, "name": name})
    return out

def main() -> int:
    os_compat.setup_console()
    client_common.load_skill_env()
    ensure_activated()
    print("  MCP ipo_list...", flush=True)
    try:
        items = _items()
    except RuntimeError as exc:
        return client_common.emit_next(
            {"ok": False, "error": f"ipo_list failed: {exc}", "next_action": "Retry later; do not switch to web search"},
            exit_code=EXIT_DATA_FAILED,
        )
    if not items:
        return client_common.emit_next(
            {"ok": True, "items": [], "next_action": "The list is empty; done"},
            exit_code=EXIT_OK,
        )
    for i, item in enumerate(items, 1):
        print(f"    {i}. {item['symbol']}  {item['name']}", flush=True)
    return client_common.emit_next(
        {"ok": True, "items": items, "next_action": "The list is printed; done"},
        exit_code=EXIT_OK,
    )

if __name__ == "__main__":
    sys.exit(main())
