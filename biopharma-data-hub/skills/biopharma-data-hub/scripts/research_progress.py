#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the one next_action for the current biopharma-data-sources session."""

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

_FILES = {
    "need_read_playbook": ("playbook_read", _ROOT / "references" / "playbook.md"),
    "need_read_sources": ("sources_read", _ROOT / "references" / "source-map.md"),
    "need_read_method": ("method_read", _ROOT / "references" / "four-step.md"),
    "need_read_upstream": ("upstream_read", _ROOT / "references" / "upstream.md"),
    "need_read_impact": ("impact_read", _ROOT / "docs" / "event_impact_stats.md"),
    "need_read_run": ("run_read", _ROOT / "references" / "run.md"),
}


def _has_key() -> bool:
    try:
        from fintrust_gate import find_api_key
    except Exception:
        return False
    key, _source = find_api_key()
    return bool(key)


def emit(phase: str, session: dict | None, blockers: list | None = None) -> None:
    print(json.dumps(rs.progress_payload(phase, session, blockers), ensure_ascii=False, indent=2))


def reject(message: str, phase: str, session: dict | None) -> int:
    print(message, file=sys.stderr)
    emit(phase, session, [message])
    return 2


def _flag(expected: str) -> int:
    session = rs.load_session()
    if session is None:
        print("no research session; run start_research.py first", file=sys.stderr)
        return 2
    phase = rs.infer_phase(session, has_key=True)
    if phase != expected:
        return reject(expected + " is not the current phase", phase, session)
    field, path = _FILES[expected]
    if not path.is_file():
        return reject(path.name + " is missing", expected, session)
    session[field] = True
    rs.save_session(session)
    emit(rs.infer_phase(session, has_key=True), session)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Research phase to next_action")
    parser.add_argument("--mark-playbook", action="store_true")
    parser.add_argument("--mark-sources", action="store_true")
    parser.add_argument("--mark-method", action="store_true")
    parser.add_argument("--mark-upstream", action="store_true")
    parser.add_argument("--mark-impact", action="store_true")
    parser.add_argument("--mark-run", action="store_true")
    parser.add_argument("--mark-presented", action="store_true")
    args = parser.parse_args()
    flags = [
        (args.mark_playbook, "need_read_playbook"),
        (args.mark_sources, "need_read_sources"),
        (args.mark_method, "need_read_method"),
        (args.mark_upstream, "need_read_upstream"),
        (args.mark_impact, "need_read_impact"),
        (args.mark_run, "need_read_run"),
    ]
    for chosen, expected in flags:
        if chosen:
            return _flag(expected)
    if args.mark_presented:
        session = rs.load_session()
        if session is None:
            print("no research session; run start_research.py first", file=sys.stderr)
            return 2
        phase = rs.infer_phase(session, has_key=True)
        if phase != "need_present":
            return reject("present is not the current phase", phase, session)
        session["presented"] = True
        rs.save_session(session)
        emit("done", session)
        return 0
    session = rs.load_session()
    if session is None:
        emit(rs.infer_phase(None, has_key=_has_key()), None)
        return 0
    emit(rs.infer_phase(session, has_key=True), session)
    return 0


if __name__ == "__main__":
    sys.exit(main())
