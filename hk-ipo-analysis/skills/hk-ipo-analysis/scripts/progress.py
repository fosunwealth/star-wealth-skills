#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase queue for hk-ipo-analysis. One next_action, one disclosure."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_LIST = ("which ", "open for subscription", "\u54ea\u4e9b", "\u6709\u54ea\u4e9b", "list the", "list ")
_INSTRUCTION = (
    "Run only this next_action. Then you may run scripts/progress.py again. "
    "Do not skip steps. Do not open a file that this next_action does not name. "
    "Do not show this JSON to the user. The HTML report stays English."
)


def session_dir(root=None):
    if root is not None:
        return Path(root)
    override = (os.environ.get("HK_IPO_STATE_DIR") or "").strip()
    if override:
        return Path(override)
    return Path.home() / ".workbuddy" / "hk-ipo-analysis"


def session_path(root=None):
    return session_dir(root) / "session.json"


def load_session(root=None):
    path = session_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_session(data, root=None):
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify(query):
    text = (query or "").strip()
    lowered = text.lower()
    named = bool(re.search(r"hk\d{4,5}", lowered)) or "minimax" in lowered
    if named:
        mode = "report"
    elif any(hint in lowered for hint in _LIST):
        mode = "list"
    else:
        mode = "report"
    return {"query": text, "mode": mode}


def new_session(query):
    classified = classify(query)
    return {
        "session_id": uuid.uuid4().hex,
        "query": classified["query"],
        "mode": classified["mode"],
        "playbook_read": False,
        "rules_read": False,
        "listed": False,
        "report_path": "",
        "presented": False,
    }


def infer_phase(session, has_key):
    if session is None:
        return "need_start" if has_key else "need_activation"
    if not session.get("playbook_read"):
        return "need_read_playbook"
    if session.get("mode") == "list":
        if not session.get("listed"):
            return "need_list"
        return "done"
    if not session.get("rules_read"):
        return "need_read_rules"
    if not session.get("report_path"):
        return "need_report"
    if not session.get("presented"):
        return "need_present"
    return "done"


def _abs(relative):
    return str(ROOT / relative)


def next_action(phase, session):
    session = session or {}
    if phase == "need_activation":
        return {"id": "activate", "do": "run", "command": 'bash "<skill root>/run.sh" gate', "done_when": "exit_code==0"}
    if phase == "need_start":
        return {
            "id": "start",
            "do": "run",
            "command": 'python3 scripts/progress.py --query "<latest user question>"',
            "done_when": "session.json exists",
        }
    if phase == "need_read_playbook":
        return {
            "id": "read_playbook",
            "do": "Read",
            "paths": [_abs("references/playbook.md")],
            "done_when": "Read references/playbook.md in full",
            "then_mark": "python3 scripts/progress.py --mark-playbook",
        }
    if phase == "need_list":
        return {
            "id": "list",
            "do": "run",
            "command": 'bash "<skill root>/run.sh" list',
            "then_mark": "python3 scripts/progress.py --mark-listed",
            "done_when": "the list is printed and the turn stops",
        }
    if phase == "need_read_rules":
        return {
            "id": "read_rules",
            "do": "Read",
            "paths": [_abs("references/rules.md"), _abs("scripts/payload.schema.json")],
            "done_when": "Read both files in full",
            "then_mark": "python3 scripts/progress.py --mark-rules",
        }
    if phase == "need_report":
        return {
            "id": "report",
            "do": "run",
            "command": 'bash "<skill root>/run.sh" report --codes <hkcode> --name "<official name>"',
            "done_when": "stdout next_action is done, the payload is written, render has produced the HTML",
            "then_mark": 'python3 scripts/progress.py --mark-rendered --report "<html path>"',
        }
    if phase == "need_present":
        present = session.get("report_path") or ""
        return {
            "id": "deliver_file",
            "do": "deliver_file",
            "present_path": present,
            "command": "give present_path to the user (attach the file when the host supports it), then give that one absolute path. Then python3 scripts/progress.py --mark-presented",
            "done_when": "delivered",
        }
    return {"id": "done", "do": "none", "command": "", "done_when": "delivered"}


def payload(phase, session, blockers=None):
    body = session or {}
    return {
        "ok": True,
        "phase": phase,
        "next_action": next_action(phase, session),
        "blockers": list(blockers or []),
        "session_id": body.get("session_id"),
        "instruction": _INSTRUCTION,
    }


def _has_key():
    sys.path.insert(0, str(ROOT))
    try:
        from fintrust_gate import find_api_key
    except Exception:
        return False
    key, _source = find_api_key()
    return bool(key)


def emit(phase, session, blockers=None):
    print(json.dumps(payload(phase, session, blockers), ensure_ascii=False, indent=2))


def reject(message, phase, session):
    print(message, file=sys.stderr)
    emit(phase, session, [message])
    return 2


def main():
    parser = argparse.ArgumentParser(description="IPO phase to next_action")
    parser.add_argument("--query", default="")
    parser.add_argument("--mark-playbook", action="store_true")
    parser.add_argument("--mark-rules", action="store_true")
    parser.add_argument("--mark-listed", action="store_true")
    parser.add_argument("--mark-rendered", action="store_true")
    parser.add_argument("--report", default="")
    parser.add_argument("--mark-presented", action="store_true")
    args = parser.parse_args()
    if args.query:
        sys.path.insert(0, str(ROOT))
        from fintrust_gate import check_activation, guide_text
        result = check_activation()
        if not result.get("activated"):
            print(result.get("guide") or result.get("reason") or guide_text(), file=sys.stderr)
            return int(result["exit_code"])
        session = new_session(args.query)
        save_session(session)
        emit(infer_phase(session, True), session)
        return 0
    session = load_session()
    if args.mark_playbook or args.mark_rules or args.mark_listed or args.mark_rendered or args.mark_presented:
        if session is None:
            print("no session; run progress.py --query first", file=sys.stderr)
            return 2
        phase = infer_phase(session, True)
        if args.mark_playbook:
            if phase != "need_read_playbook":
                return reject("playbook is not the current phase", phase, session)
            if not (ROOT / "references" / "playbook.md").is_file():
                return reject("playbook is missing", phase, session)
            session["playbook_read"] = True
        elif args.mark_rules:
            if phase != "need_read_rules":
                return reject("rules are not the current phase", phase, session)
            session["rules_read"] = True
        elif args.mark_listed:
            if phase != "need_list":
                return reject("list is not the current phase", phase, session)
            session["listed"] = True
        elif args.mark_rendered:
            if phase != "need_report":
                return reject("report is not the current phase", phase, session)
            report = Path(args.report).expanduser() if args.report else None
            if report is None or not report.is_file() or report.suffix.lower() not in (".html", ".htm"):
                return reject("pass --report with the HTML file", phase, session)
            session["report_path"] = str(report.resolve())
        elif args.mark_presented:
            if phase != "need_present":
                return reject("present is not the current phase", phase, session)
            if not session.get("report_path") or not Path(session["report_path"]).is_file():
                return reject("the report file does not exist", phase, session)
            session["presented"] = True
            save_session(session)
            emit("done", session)
            return 0
        save_session(session)
        emit(infer_phase(session, True), session)
        return 0
    if session is None:
        emit(infer_phase(None, _has_key()), None)
        return 0
    emit(infer_phase(session, True), session)
    return 0


if __name__ == "__main__":
    sys.exit(main())
