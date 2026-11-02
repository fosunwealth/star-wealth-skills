#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from payload_check import SCHEMA_PATH, check as check_payload
from payload_merge import merge_prefer
from report_template import render

__all__ = [
    "SCHEMA_PATH",
    "check_payload",
    "html_path",
    "load_payload",
    "payload_path",
    "primary_path",
    "raw_path",
    "read_primary",
    "render_artifacts",
    "render_payload",
    "stale_payload_path",
    "write_artifacts",
    "write_html",
]

def raw_path(data_dir: Path | str, symbol: str) -> Path:
    return Path(data_dir) / f"{symbol}_raw.md"

def primary_path(data_dir: Path | str, symbol: str) -> Path:
    return Path(data_dir) / f"{symbol}_primary.json"

def payload_path(data_dir: Path | str, symbol: str) -> Path:
    return Path(data_dir) / f"{symbol}.json"

def html_path(data_dir: Path | str, symbol: str) -> Path:
    return Path(data_dir) / f"{symbol}_report.html"

def load_payload(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("the top level of the payload must be an object")
    return payload

def read_primary(data_dir: Path | str, symbol: str) -> dict[str, Any]:
    try:
        data = json.loads(primary_path(data_dir, symbol).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}

def _paragraphs(items: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        out.append({"label": str(item.get("label") or ""), "text": str(item.get("text") or "")})
    return out

def _normalize(payload: dict[str, Any], *, symbol: str, name: str) -> dict[str, Any]:
    payload["symbol"] = str(payload.get("symbol") or symbol or "").strip()
    payload["stock_name"] = str(payload.get("stock_name") or name or symbol or "").strip()
    for key in (
        "ai_rating", "subscription", "sponsor", "cornerstone",
        "premium", "valuation_module", "fundamental", "industry_module", "market",
    ):
        block = payload.get(key)
        if isinstance(block, dict):
            block["interpretation"] = _paragraphs(block.get("interpretation"))
    return payload

def merge_payload(payload: dict[str, Any], primary: dict[str, Any] | None,
                  *, symbol: str = "", name: str = "") -> dict[str, Any]:
    if primary:
        payload = merge_prefer(primary, payload)
    return _normalize(payload, symbol=symbol, name=name)

def render_payload(payload: dict[str, Any] | None) -> str:
    return render(payload)

def write_html(payload_file: Path | str, dest: Path | str, *,
               symbol: str = "", name: str = "") -> Path:
    payload = merge_payload(load_payload(payload_file), None, symbol=symbol, name=name)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_payload(payload), encoding="utf-8")
    return dest

def stale_payload_path(data_dir: Path | str, symbol: str) -> Path:
    return Path(data_dir) / f"{symbol}.json.stale"

def write_artifacts(
    text: str,
    data_dir: Path | str,
    *,
    symbol: str,
    primary: dict[str, Any] | None = None,
) -> dict[str, Path]:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    raw = raw_path(data_dir, symbol)
    payload = payload_path(data_dir, symbol)
    new_text = text or ""
    old_text = raw.read_text(encoding="utf-8") if raw.exists() else None
    paths = {"raw": raw, "primary": primary_path(data_dir, symbol)}
    if old_text is not None and old_text != new_text and payload.exists():
        paths["stale_payload"] = payload.replace(stale_payload_path(data_dir, symbol))
    raw.write_text(new_text, encoding="utf-8")
    paths["primary"].write_text(
        json.dumps(primary or {}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return paths

def render_artifacts(
    data_dir: Path | str,
    *,
    symbol: str,
    name: str,
    primary: dict[str, Any] | None = None,
    supplement: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    data_dir = Path(data_dir)
    payload = merge_payload(load_payload(payload_path(data_dir, symbol)), primary,
                            symbol=symbol, name=name)
    if supplement is not None:
        extra = supplement(payload) or {}
        if extra:
            payload = _normalize(merge_prefer(extra, payload), symbol=symbol, name=name)
    verdict = check_payload(payload)
    if verdict["errors"]:
        return {"paths": {}, "check": verdict}
    paths = {"payload": payload_path(data_dir, symbol), "html": html_path(data_dir, symbol)}
    paths["html"].write_text(render(payload), encoding="utf-8")
    return {"paths": paths, "check": verdict}
