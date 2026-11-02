#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
for _p in (str(HERE), str(SKILL_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import client_common
import ipo_sources
import os_compat
from fintrust_gate import ensure_activated
from render_report import (
    payload_path,
    raw_path,
    read_primary,
    render_artifacts,
    write_artifacts,
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DATA_FAILED = 6
EXIT_PAYLOAD = 7
REPORT_TIMEOUT = 1800
_POLL_WAIT = 25
_POLL_CAP = 30
_MAX_ATTEMPTS = 4
_RETRY_PAUSE = 5
_FAILED_TTL = 300
_RETRY_PROBE = 10.0
_MISSING_CODE = "Missing a valid HK IPO code"
# Marks that mean "stop retrying". The gateway answers in Chinese, so these stay
# Chinese; _MISSING_CODE sits here too, so display and matching share one string.
_FATAL_MARKS = ("额度", "招股书", "基本信息缺失", _MISSING_CODE, "Key 无效")

def _skill_version() -> str:
    try:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""

def _data_dir(code: str) -> Path:
    root = os.environ.get("IPO_DATA_DIR", "").strip()
    dest = (Path(root) if root else SKILL_ROOT / "data") / code
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def _poll_wait(inner: dict[str, Any], remain: float) -> int:
    raw = inner.get("poll_after_seconds")
    wait = int(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else _POLL_WAIT
    return max(1, min(_POLL_CAP, wait, max(1, int(remain))))

def _status_line(inner: dict[str, Any]) -> str:
    raw = inner.get("progress")
    progress: dict[str, Any] = raw if isinstance(raw, dict) else {}
    raw_steps = progress.get("steps")
    steps: list[Any] = [s for s in raw_steps if isinstance(s, dict)] if isinstance(raw_steps, list) else []
    node = str(progress.get("current_step") or "").strip()
    running = [s for s in steps if str(s.get("status")) == "running"]
    if not node and running:
        node = str(running[0].get("title") or "").strip()
    done = progress.get("done_steps")
    total = progress.get("total_steps")
    if isinstance(done, bool) or not isinstance(done, (int, float)):
        done = sum(1 for s in steps if str(s.get("status")) == "done")
    if isinstance(total, bool) or not isinstance(total, (int, float)):
        total = len(steps)
    bits = ["Running normally", f"Current node: {node}" if node else "Current node has not reported yet"]
    if total:
        index = int(done) + (1 if running else 0)
        index = min(max(index, 1), int(total))
        bits.append(f"Step {index}/{int(total)}")
    elapsed = inner.get("elapsed_seconds")
    if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool) and elapsed >= 1:
        bits.append(f"{int(elapsed)}s elapsed")
    eta = inner.get("eta_seconds")
    if isinstance(eta, (int, float)) and not isinstance(eta, bool) and eta > 0:
        bits.append(f"about {int(eta)}s left")
    return " · ".join(bits)

class _GenerationFailed(RuntimeError):

    def __init__(self, message: str, cooldown: float = 0.0) -> None:
        super().__init__(message)
        self.cooldown = max(0.0, cooldown)

def _retryable(message: str) -> bool:
    return not any(mark in message for mark in _FATAL_MARKS)

def fetch_report(code: str, name: str, *, deadline: float) -> str:
    normalized = client_common.norm_ipo_code(code)
    if not normalized:
        raise RuntimeError(_MISSING_CODE)
    company = (name or "").strip()
    attempts = 0
    while True:
        attempts += 1
        try:
            return _monitor_once(normalized, company, deadline=deadline,
                                 fresh=attempts > 1, first=attempts == 1)
        except _GenerationFailed as exc:
            message = str(exc)
            room = deadline - time.monotonic()
            if not _retryable(message) or attempts >= _MAX_ATTEMPTS or room <= 3.0:
                raise RuntimeError(message) from None
            pause = min(exc.cooldown or _RETRY_PAUSE, room - 3.0)
            print(f"  [{normalized}] generation interrupted on attempt {attempts}: {message}", flush=True)
            print(f"  [{normalized}] continuing with one new generation (attempt {attempts + 1}/{_MAX_ATTEMPTS}, "
                  f"uses 1 credit, waiting {int(pause)}s, {int(room)}s of budget left)", flush=True)
            time.sleep(max(0.0, pause))

def _monitor_once(normalized: str, company: str, *, deadline: float,
                  fresh: bool, first: bool) -> str:
    args: dict[str, Any] = {"code": normalized, "wait_seconds": 0}
    if company:
        args["name"] = company
    if fresh:
        args["retry"] = True
    if first:
        print(f"  [{normalized}] submitting one Dify job, then only this one is monitored", flush=True)
    started = time.monotonic()
    watched = ""
    while True:
        room = deadline - time.monotonic()
        if room <= 2:
            raise RuntimeError("MCP ipo_dify_report timed out waiting for the report")
        wait = float(args.get("wait_seconds") or 0)
        http_to = min(90.0 if wait <= 0 else wait + 40.0, max(1.0, room - 1.0))
        data = client_common.tool_json("ipo_dify_report", args, timeout=http_to)
        try:
            inner = client_common.unwrap_capability(data)
        except RuntimeError as exc:
            cold = _FAILED_TTL if (fresh and time.monotonic() - started < _RETRY_PROBE) else 0.0
            raise _GenerationFailed(str(exc), cold) from None
        if isinstance(inner, str) and inner.strip():
            text = inner.strip()
            print(f"  report {len(text):,} chars", flush=True)
            return text
        if not isinstance(inner, dict):
            raise RuntimeError("MCP ipo_dify_report returned an empty report text")
        status = str(inner.get("status") or "").strip().lower()
        text = str(inner.get("report") or "").strip()
        if text:
            print(f"  report {len(text):,} chars", flush=True)
            return text
        if status == "failed":
            raise _GenerationFailed(str(inner.get("error") or "IPO report generation failed"))
        if status and status != "running":
            raise _GenerationFailed(f"MCP ipo_dify_report returned an unexpected status: {status}")
        job_id = str(inner.get("job_id") or "")
        if watched and job_id and job_id != watched:
            print(f"  [{normalized}] server job id changed from {watched} to {job_id}; keep monitoring, do not resubmit", flush=True)
        watched = job_id or watched
        print(f"  [{normalized}] {_status_line(inner)}", flush=True)
        args["wait_seconds"] = _poll_wait(inner, deadline - time.monotonic())

def _long_cjk(text: str) -> bool:
    run = 0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            run += 1
            if run >= 12:
                return True
        else:
            run = 0
    return False

_SKIP_ENGLISH = {"stock_name", "symbol", "name", "groupName", "groupKey"}

def payload_needs_english(node: Any, key: str = "") -> bool:
    if key in _SKIP_ENGLISH:
        return False
    if isinstance(node, dict):
        return any(payload_needs_english(value, child) for child, value in node.items())
    if isinstance(node, list):
        return any(payload_needs_english(item, key) for item in node)
    return isinstance(node, str) and _long_cjk(node)

def _english_next(code: str, payload_file: str) -> str:
    return (
        "Do not deliver the file. The report narrative is still Chinese. "
        f"Rewrite every Chinese sentence in {payload_file} into English. "
        "Keep keys, numbers, the official issuer name, and the hk code. "
        f'Then run: bash "<skill root>/run.sh" render --codes {code}'
    )

class _PayloadMissing(RuntimeError):
    pass

class _PayloadInvalid(RuntimeError):
    pass

def _payload_hint(code: str, data_dir: Path, payload: Path, stale: Path | None = None) -> str:
    schema = SKILL_ROOT / "scripts" / "payload.schema.json"
    if stale is not None:
        return (f"The source text was replaced, so the previous payload moved to {stale} "
                f"(it no longer matches the source — do not rename it back): read "
                f"{raw_path(data_dir, code)} and write {payload} in full, following {schema}, "
                f"then run: render --codes {code}")
    if payload.exists():
        return f"{payload} is already there. Run: render --codes {code}"
    return (f"Read {raw_path(data_dir, code)} and write {payload} in full, following {schema}: "
            f"it carries every value the HTML needs, each field says in its title where it comes from, "
            f"and the whole narrative must be English. Then run: render --codes {code}")

def _fetch(code: str, name: str, *, refresh: bool, deadline: float) -> dict[str, Any]:
    t0 = time.perf_counter()
    data_dir = _data_dir(code)

    primary = ipo_sources.primary(code)

    raw = raw_path(data_dir, code)
    if refresh or not raw.exists():
        text = fetch_report(code, name, deadline=deadline)
    else:
        text = raw.read_text(encoding="utf-8")
        print(f"  [{code}] reusing local source {raw}", flush=True)

    paths = write_artifacts(text, data_dir, symbol=code, primary=primary)
    payload = payload_path(data_dir, code)
    stale = paths.get("stale_payload")
    print(f"  [{code}] source → {paths['raw']}", flush=True)
    print(f"  [{code}] layer1 truth → {paths['primary']}", flush=True)
    if stale is not None:
        print(f"  [{code}] source text replaced → previous payload voided, moved to {stale}", flush=True)
    print(f"  [{code}] payload → {payload}"
          + (" (already there, untouched)" if payload.exists() else " (you write it from the schema)"), flush=True)
    return {"symbol": code, "name": name, "raw_path": str(paths["raw"]),
            "primary_path": str(paths["primary"]), "payload_path": str(payload),
            "payload_exists": payload.exists(),
            "stale_payload": str(stale) if stale is not None else "",
            "hint": _payload_hint(code, data_dir, payload, stale),
            "elapsed_s": round(time.perf_counter() - t0, 1)}

def _render(code: str, name: str, *, deadline: float) -> dict[str, Any]:
    t0 = time.perf_counter()
    data_dir = _data_dir(code)
    payload_file = payload_path(data_dir, code)
    if not payload_file.exists():
        raise _PayloadMissing(f"missing payload: {payload_file}. "
                              + _payload_hint(code, data_dir, payload_file))
    result = render_artifacts(
        data_dir,
        symbol=code,
        name=name,
        primary=read_primary(data_dir, code),
        supplement=lambda merged: ipo_sources.supplement(code, merged, deadline=deadline),
    )
    verdict = result["check"]
    if verdict["errors"]:
        raise _PayloadInvalid(
            f"payload does not match the schema, {len(verdict['errors'])} hard error(s): "
            + "; ".join(verdict["errors"][:6])
        )
    for slot in verdict["empties"]:
        print(f"  [{code}] payload blank {slot} (schema says warn: expected but missing)", flush=True)
    payload = json.loads(payload_file.read_text(encoding="utf-8"))
    html = result["paths"]["html"]
    print(f"  [{code}] → {html}", flush=True)
    return {"symbol": code, "name": name, "html_path": str(html),
            "payload_path": str(payload_file),
            "needs_english": payload_needs_english(payload),
            "payload_empties": verdict["empties"],
            "elapsed_s": round(time.perf_counter() - t0, 1)}

def main(argv: list[str] | None = None, stage: str = "report") -> int:
    parser = argparse.ArgumentParser(prog="ipo.py")
    parser.add_argument("--codes", nargs="+", required=True)
    parser.add_argument("--name", default="")
    if stage == "report":
        parser.add_argument("--refresh", action="store_true",
                            help="Refetch the source text (default: reuse a local <code>_raw.md)")
    args = parser.parse_args(argv)
    os_compat.setup_console()
    client_common.load_skill_env()
    ensure_activated()

    codes = list(dict.fromkeys(c for c in (client_common.norm_ipo_code(raw) for raw in args.codes) if c))
    if not codes:
        return client_common.emit_next(
            {"ok": False, "error": "no code", "next_action": "Pass --codes"},
            exit_code=EXIT_USAGE,
        )

    name = (args.name or "").strip() if len(codes) == 1 else ""
    version = _skill_version()
    print(f"  hk-ipo-analysis v{version or '?'} · {stage}", flush=True)
    deadline = time.monotonic() + REPORT_TIMEOUT
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    stage_exit = 0
    try:
        for code in codes:
            try:
                if stage == "report":
                    results.append(_fetch(code, name or code, deadline=deadline,
                                          refresh=bool(getattr(args, "refresh", False))))
                else:
                    results.append(_render(code, name or code, deadline=deadline))
            except _PayloadMissing as exc:
                stage_exit = stage_exit or EXIT_USAGE
                failures.append({"symbol": code, "error": str(exc)})
                print(f"  [{code}] {exc}", flush=True)
            except _PayloadInvalid as exc:
                stage_exit = stage_exit or EXIT_PAYLOAD
                failures.append({"symbol": code, "error": str(exc)})
                print(f"  [{code}] {exc}", flush=True)
            except Exception as exc:
                failures.append({"symbol": code, "error": str(exc)})
                print(f"  [{code}] failed: {exc}", flush=True)
    except KeyboardInterrupt:
        return client_common.emit_next(
            {"ok": False, "error": "interrupted", "next_action": "Run it again"},
            exit_code=130,
        )

    ok = bool(results) and not failures
    htmls = ", ".join(r["html_path"] for r in results if r.get("html_path"))
    hints = " ".join(r["hint"] for r in results if r.get("hint"))
    pending = [r for r in results if r.get("needs_english")]
    if pending:
        return client_common.emit_next(
            {"ok": False, "results": results, "failures": failures,
             "next_action": _english_next(pending[0]["symbol"], pending[0]["payload_path"])},
            exit_code=EXIT_USAGE,
        )
    if stage == "report":
        if ok:
            next_action = hints
        elif hints:
            next_action = hints + " Relay failures[].error as-is."
        else:
            next_action = ("Could not fetch the source. Relay failures[].error as-is. "
                           "Do not switch to web search.")
    elif ok:
        next_action = ("The report is English. Deliver this one path only: name it in the chat, and attach the file when the host supports attachments. "
                       "Do not copy it outside the package: " + htmls)
    elif htmls:
        next_action = ("Partial result. Deliver this one path only: name it in the chat, and attach the file when the host supports attachments. Do not copy it outside the package: "
                       + htmls + " Relay failures[].error as-is.")
    else:
        next_action = ("No report: fix what failures[].error says (missing payload → write it from the schema; "
                       "hard errors → fix the payload), then run render again. Do not switch to web search.")
    return client_common.emit_next(
        {"ok": ok, "skill_version": version, "results": results,
         "failures": failures, "next_action": next_action},
        exit_code=EXIT_OK if ok else (stage_exit or EXIT_DATA_FAILED),
    )

if __name__ == "__main__":
    sys.exit(main())
