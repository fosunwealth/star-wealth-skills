#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the one next_action for the current tech-hardware research session."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import research_state as rs  # noqa: E402


def _has_key() -> bool:
    try:
        from fintrust_gate import find_api_key
    except Exception:
        return False
    key, _source = find_api_key()
    return bool(key)


def emit_progress(phase: str, session: dict | None, blockers: list | None = None) -> None:
    print(json.dumps(rs.progress_payload(phase, session, blockers), ensure_ascii=False, indent=2))


def reject(message: str, phase: str, session: dict | None) -> int:
    print(message, file=sys.stderr)
    emit_progress(phase, session, [message])
    return 2


def _need_session() -> dict | None:
    session = rs.load_session()
    if session is None:
        print("no research session; run start_research.py first", file=sys.stderr)
    return session


def _guard(session: dict, expected: str) -> str | None:
    phase = rs.infer_phase(session, has_key=True)
    if phase != expected:
        return phase
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Research phase to next_action")
    parser.add_argument("--mark-playbook", action="store_true")
    parser.add_argument("--mark-sector", action="store_true")
    parser.add_argument("--sector", default="")
    parser.add_argument("--mark-framework", action="store_true")
    parser.add_argument("--mark-verify", action="store_true")
    parser.add_argument("--mark-fetch", action="store_true")
    parser.add_argument("--mark-pitfalls", action="store_true")
    parser.add_argument("--mark-tracking", action="store_true")
    parser.add_argument("--mark-written", action="store_true")
    parser.add_argument("--report", default="")
    parser.add_argument("--mark-scaffolded", action="store_true")
    parser.add_argument("--workspace", default="")
    parser.add_argument("--mark-presented", action="store_true")
    args = parser.parse_args()

    if args.mark_playbook:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_read_playbook")
        if wrong:
            return reject("playbook is not the current phase", wrong, session)
        playbook = _ROOT / "references" / "playbook.md"
        if not playbook.is_file():
            return reject("references/playbook.md is missing", "need_read_playbook", session)
        session["playbook_read"] = True
        rs.save_session(session)
        emit_progress(rs.infer_phase(session, has_key=True), session)
        return 0

    if args.mark_sector:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_read_sector")
        if wrong:
            return reject("sector is not the current phase", wrong, session)
        sector = (args.sector or session.get("sector") or "").strip()
        if sector not in rs.SECTOR_FILES:
            return reject("sector must be one of the six keys", "need_read_sector", session)
        sector_file = _ROOT / rs.SECTOR_FILES[sector]
        if not sector_file.is_file():
            return reject("the sector file is missing", "need_read_sector", session)
        had = session.get("sector") or ""
        session["sector"] = sector
        session["sector_read"] = had == sector
        rs.save_session(session)
        emit_progress(rs.infer_phase(session, has_key=True), session)
        return 0

    if args.mark_framework:
        return _flag("need_read_framework", "framework_read", _ROOT / "references" / "02-general-framework.md")

    if args.mark_verify:
        return _flag("need_read_verify", "verify_read", _ROOT / "references" / "09-verification-methods.md")

    if args.mark_pitfalls:
        return _flag("need_read_pitfalls", "pitfalls_read", _ROOT / "references" / "11-pitfalls.md")

    if args.mark_tracking:
        return _flag("need_read_tracking", "tracking_read", _ROOT / "references" / "10-tracking-system.md")

    if args.mark_fetch:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_fetch")
        if wrong:
            return reject("fetch is not the current phase", wrong, session)
        path = rs.sources_path()
        accepted, reason = rs.count_source_items(path)
        minimum = 26 if session.get("mode") == "full" else 1
        if reason or accepted < minimum:
            message = reason or ("sources.json has %s accepted items; this mode needs %s" % (accepted, minimum))
            return reject(message, "need_fetch", session)
        session["fetch_done"] = True
        rs.save_session(session)
        emit_progress(rs.infer_phase(session, has_key=True), session)
        return 0

    if args.mark_written:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_write")
        if wrong:
            return reject("write is not the current phase", wrong, session)
        report = Path(args.report).expanduser() if args.report else None
        if report is None:
            return reject("pass --report with the HTML path", "need_write", session)
        problem = rs.report_is_html(report)
        if problem:
            return reject(problem, "need_write", session)
        session["report_path"] = str(report.resolve())
        rs.save_session(session)
        emit_progress(rs.infer_phase(session, has_key=True), session)
        return 0

    if args.mark_scaffolded:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_scaffold")
        if wrong:
            return reject("scaffold is not the current phase", wrong, session)
        if not args.workspace:
            return reject("pass --workspace with the directory that holds the six files", "need_scaffold", session)
        workspace = Path(args.workspace).expanduser()
        problem = rs.workspace_is_complete(workspace)
        if problem:
            return reject(problem, "need_scaffold", session)
        session["workspace"] = str(workspace.resolve())
        rs.save_session(session)
        emit_progress(rs.infer_phase(session, has_key=True), session)
        return 0

    if args.mark_presented:
        session = _need_session()
        if session is None:
            return 2
        wrong = _guard(session, "need_present")
        if wrong:
            return reject("present is not the current phase", wrong, session)
        present = session.get("report_path") or ""
        if not present and session.get("workspace"):
            present = str(Path(session["workspace"]) / "00_overview.md")
        if not present or not Path(present).is_file():
            return reject("the file to present does not exist", "need_present", session)
        session["presented"] = True
        rs.save_session(session)
        emit_progress("done", session)
        return 0

    session = rs.load_session()
    if session is None:
        phase = rs.infer_phase(None, has_key=_has_key())
        emit_progress(phase, None)
        return 0
    phase = rs.infer_phase(session, has_key=True)
    emit_progress(phase, session)
    return 0


def _flag(expected: str, field: str, file_path: Path) -> int:
    session = _need_session()
    if session is None:
        return 2
    wrong = _guard(session, expected)
    if wrong:
        return reject(field + " is not the current phase", wrong, session)
    if not file_path.is_file():
        return reject(str(file_path.name) + " is missing", expected, session)
    session[field] = True
    rs.save_session(session)
    emit_progress(rs.infer_phase(session, has_key=True), session)
    return 0


if __name__ == "__main__":
    sys.exit(main())
