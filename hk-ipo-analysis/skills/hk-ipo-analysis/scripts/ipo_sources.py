#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Callable

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import client_common
from payload_merge import is_blank, merge_prefer

LAYER1_TOOLS = ("ipo_list", "market_snapshot")
LAYER3_TOOLS = ("deep_profile", "news_catalysts")
HOST_IPO_CLI = "westock-data"
HOST_DATE_FIELDS = ("apply_start_date", "apply_end_date", "trade_date")

_LIST_SOURCES = ("latest", "simple", "trade")
_SUPPLEMENT_CHARS = 1200
_PROFILE_LABEL = "Fundamental profile (Baidu Stock)"
_NEWS_LABEL = "Company news (HK/US news feeds)"

def _enabled(name: str) -> bool:
    raw = str(os.environ.get(name, "1")).strip().lower()
    return raw not in ("0", "false", "no", "off")

def _budget(deadline: float | None, cap: float) -> float | None:
    if deadline is None:
        return cap
    remain = deadline - time.monotonic()
    if remain < 3:
        return None
    return min(cap, max(1.0, remain - 1.0))

def _call(name: str, arguments: dict, timeout: float, *, deadline: float | None = None) -> Any:
    budget = _budget(deadline, timeout)
    if budget is None:
        return None
    try:
        data = client_common.tool_json(name, arguments, timeout=budget)
        return client_common.unwrap_capability(data)
    except Exception as exc:
        print(f"  {name} unavailable ({exc}) -> falling back to the next layer", flush=True)
        return None

def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}

def _paras_blank(value: Any) -> bool:
    if is_blank(value):
        return True
    if isinstance(value, list):
        texts = [str(p.get("text") or "") if isinstance(p, dict) else str(p or "") for p in value]
        return not any(t.strip() for t in texts)
    return False

def _list_items(source: str, *, deadline: float | None = None) -> list[dict]:
    inner = _call("ipo_list", {"source": source}, 60, deadline=deadline)
    if not isinstance(inner, dict):
        return []
    items = inner.get("items")
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []

def find_list_item(code: str, *, deadline: float | None = None) -> dict:
    for source in _LIST_SOURCES:
        if _budget(deadline, 60) is None:
            break
        for item in _list_items(source, deadline=deadline):
            raw = item.get("code") or item.get("symbol") or ""
            if client_common.norm_ipo_code(str(raw)) == code:
                return item
    return {}

def _quote_data(code: str, *, deadline: float | None = None) -> dict:
    inner = _call("market_snapshot", {"code": code}, 30, deadline=deadline)
    quote = _as_dict(_as_dict(inner).get("quote"))
    data = _as_dict(quote.get("data"))
    for session in ("盘中", "盘前", "盘后", "夜盘"):
        bucket = _as_dict(data.get(session))
        row = bucket.get(code) or bucket.get(code.replace("hk", ""))
        if isinstance(row, dict) and row:
            return row
    return {}

def primary(code: str, *, deadline: float | None = None) -> dict:
    if not _enabled("IPO_MCP_PRIMARY"):
        return {}
    item = find_list_item(code, deadline=deadline)
    row = _quote_data(code, deadline=deadline)

    stock_name = str(item.get("name") or item.get("stockName") or row.get("名称") or "").strip()
    currency = str(row.get("币种") or "").strip().upper()
    fragment: dict[str, Any] = {}
    if stock_name:
        fragment["stock_name"] = stock_name
    if currency:
        fragment["issue_params"] = {"currency": currency}

    if fragment:
        bits = [f"{k}={v}" for k, v in (("name", stock_name), ("currency", currency)) if v]
        print(f"  [{code}] layer1 MCP {'+'.join(LAYER1_TOOLS)} → {', '.join(bits)}", flush=True)
    else:
        print(f"  [{code}] layer1 MCP got no real value -> handed to the parent", flush=True)
    return fragment

def _para(label: str, text: str) -> list[dict[str, str]]:
    text = client_common.redact_signed_urls(str(text or "").strip())
    if not text:
        return []
    if len(text) > _SUPPLEMENT_CHARS:
        text = text[:_SUPPLEMENT_CHARS].rstrip() + "…"
    return [{"label": label, "text": text}]

def _profile_paragraphs(code: str, deadline: float | None = None) -> list[dict[str, str]]:
    inner = _call("deep_profile", {"code": code}, 60, deadline=deadline)
    body = _as_dict(inner).get("profile")
    source = str(_as_dict(inner).get("source") or "").strip()
    label = f"{_PROFILE_LABEL.split('(')[0].strip()} ({source})" if source else _PROFILE_LABEL
    return _para(label, body if isinstance(body, str) else "")

def _news_paragraphs(code: str, deadline: float | None = None) -> list[dict[str, str]]:
    inner = _call("news_catalysts", {"code": code}, 30, deadline=deadline)
    body = _as_dict(inner).get("company_news")
    if isinstance(body, dict):
        text = "\n".join(f"{k}: {v}" for k, v in body.items() if str(v).strip())
    elif isinstance(body, str):
        text = body
    else:
        text = ""
    return _para(_NEWS_LABEL, text)

def _interpretation_of(payload: dict, block: str) -> Any:
    return _as_dict(payload.get(block)).get("interpretation")

def _host_exe() -> str:
    return shutil.which(HOST_IPO_CLI) or ""

def host_ipo_row(code: str, *, deadline: float | None = None) -> dict:
    exe = _host_exe()
    if not exe:
        return {}
    budget = _budget(deadline, 60)
    if budget is None:
        return {}
    try:
        proc = subprocess.run(
            [exe, "ipo", "--market", "hk", "--raw"],
            capture_output=True, text=True, timeout=budget, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  [{code}] layer4 {HOST_IPO_CLI} unavailable ({exc}) -> this layer stays empty", flush=True)
        return {}
    if proc.returncode != 0:
        return {}
    try:
        rows = json.loads(proc.stdout or "[]")
    except ValueError:
        return {}
    want = str(code).strip()
    if want.lower().startswith("hk"):
        want = want[2:]
    want = want.lstrip("0") or want
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        got = str(row.get("code") or "").strip()
        if got.lower().startswith("hk"):
            got = got[2:]
        if (got.lstrip("0") or got) == want:
            return row
    return {}

def _host_issue_dates(code: str, payload: dict, *, deadline: float | None = None) -> dict:
    issue = _as_dict(payload.get("issue_params"))
    missing = [key for key in HOST_DATE_FIELDS if is_blank(issue.get(key))]
    if not missing:
        return {}
    row = host_ipo_row(code, deadline=deadline)
    if not row:
        return {}
    fix: dict[str, Any] = {}
    if "apply_start_date" in missing or "apply_end_date" in missing:
        span = str(row.get("sgrq") or "").strip()
        if "~" in span:
            head, _, tail = span.partition("~")
            if "apply_start_date" in missing and head.strip():
                fix["apply_start_date"] = head.strip()
            if "apply_end_date" in missing and tail.strip():
                fix["apply_end_date"] = tail.strip()
    if "trade_date" in missing:
        day = str(row.get("ssrq") or "").strip()
        if day and day != "--":
            fix["trade_date"] = day
    if fix:
        print(f"  [{code}] layer4 {HOST_IPO_CLI} fills issue_params {', '.join(fix)}", flush=True)
    return {"issue_params": fix} if fix else {}

def supplement(code: str, payload: dict, *, deadline: float | None = None) -> dict:
    fragment: dict[str, Any] = {}

    if _enabled("IPO_MCP_SUPPLEMENT"):
        wanted = [
            ("fundamental", "deep_profile", _profile_paragraphs),
            ("market", "news_catalysts", _news_paragraphs),
        ]
        blanks = [slot for slot, _, _ in wanted if _paras_blank(_interpretation_of(payload, slot))]
        if not blanks:
            print(f"  [{code}] layer3 has no empty slot, not calling", flush=True)
        else:
            for slot, tool, build in wanted:
                if slot not in blanks:
                    continue
                paras = build(code, deadline)
                if paras:
                    fragment[slot] = {"interpretation": paras}
                    print(f"  [{code}] layer3 {tool} fills {slot} commentary", flush=True)
                else:
                    print(f"  [{code}] layer3 {tool} has no content, leaving {slot} empty", flush=True)

    if _enabled("IPO_HOST_SOURCES"):
        layered = _host_issue_dates(code, merge_prefer(fragment, payload), deadline=deadline)
        if layered:
            fragment = merge_prefer(layered, fragment)

    return fragment

def probe() -> list[tuple[str, bool]]:
    checks: list[tuple[str, Callable[[], Any]]] = [
        ("ipo_list", lambda: _list_items("latest")),
        ("market_snapshot", lambda: _quote_data("hk00700")),
    ]
    out: list[tuple[str, bool]] = []
    for name, fn in checks:
        try:
            out.append((name, bool(fn())))
        except Exception:
            out.append((name, False))
    return out
