# -*- coding: utf-8 -*-
"""Phase queue for biopharma-strategy. One next_action, one disclosure."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SESSION_NAME = "biopharma-strategy"
_TRACK = (
    "track",
    "tracking",
    "cron",
    "twice",
    "schedule",
    "catalyst",
    " bd",
    "\u8ffd\u8e2a",
    "\u8bbe\u7f6e",
    "\u53ea\u770b",
)
_INSTRUCTION = (
    "Run only this next_action. Then you may run research_progress.py again. "
    "Do not skip steps. Do not open a file that this next_action does not name. "
    "Do not show this JSON to the user. All user-facing text follows the user's language."
)


def session_dir(root: Path | None = None) -> Path:
    if root is not None:
        return root
    override = (os.environ.get("BIOPHARMA_STRATEGY_STATE_DIR") or "").strip()
    if override:
        return Path(override)
    return Path.home() / ".workbuddy" / SESSION_NAME


def session_path(root: Path | None = None) -> Path:
    return session_dir(root) / "session.json"


def load_session(root: Path | None = None) -> dict | None:
    path = session_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_session(data: dict, root: Path | None = None) -> None:
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify(query: str) -> dict:
    text = (query or "").strip()
    lowered = " " + text.lower()
    mode = "track" if any(hint.lower() in lowered for hint in _TRACK) else "note"
    return {"query": text, "mode": mode}


def new_session(query: str) -> dict:
    classified = classify(query)
    return {
        "session_id": uuid.uuid4().hex,
        "query": classified["query"],
        "mode": classified["mode"],
        "playbook_read": False,
        "method_read": False,
        "upstream_read": False,
        "impact_read": False,
        "setup_read": False,
        "run_read": False,
        "presented": False,
    }


def infer_phase(session: dict | None, *, has_key: bool) -> str:
    if session is None:
        return "need_start" if has_key else "need_activation"
    mode = session.get("mode") or "note"
    if not session.get("playbook_read"):
        return "need_read_playbook"
    if mode == "track":
        if not session.get("upstream_read"):
            return "need_read_upstream"
        if not session.get("impact_read"):
            return "need_read_impact"
        if not session.get("setup_read"):
            return "need_read_setup"
    elif not session.get("method_read"):
        return "need_read_method"
    if not session.get("run_read"):
        return "need_read_run"
    if not session.get("presented"):
        return "need_present"
    return "done"


def _abs(relative: str) -> str:
    return str(SKILL_ROOT / relative)


def _py() -> str:
    return "python3 scripts/research_progress.py"


def next_action(phase: str, session: dict | None) -> dict:
    if phase == "need_activation":
        return {
            "id": "activate",
            "do": "run",
            "command": "python3 fintrust_gate/activation_gate.py",
            "done_when": "exit_code==0",
        }
    if phase == "need_start":
        return {
            "id": "start_research",
            "do": "run",
            "command": "python3 scripts/start_research.py --query '<latest user question>'",
            "done_when": "session.json exists",
        }
    if phase == "need_read_playbook":
        return {
            "id": "read_playbook",
            "do": "Read",
            "paths": [_abs("references/playbook.md")],
            "done_when": "Read references/playbook.md in full",
            "then_mark": _py() + " --mark-playbook",
        }
    if phase == "need_read_method":
        return {
            "id": "read_method",
            "do": "Read",
            "paths": [_abs("references/four-step.md")],
            "done_when": "Read the four-step file in full",
            "then_mark": _py() + " --mark-method",
        }
    if phase == "need_read_upstream":
        return {
            "id": "read_upstream",
            "do": "Read",
            "paths": [_abs("references/upstream.md")],
            "done_when": "Read the upstream file in full",
            "then_mark": _py() + " --mark-upstream",
        }
    if phase == "need_read_impact":
        return {
            "id": "read_impact",
            "do": "Read",
            "paths": [_abs("references/event-impact-stats.md")],
            "done_when": "Read the impact library in full",
            "then_mark": _py() + " --mark-impact",
        }
    if phase == "need_read_setup":
        return {
            "id": "read_setup",
            "do": "Read",
            "paths": [_abs("references/setup.md")],
            "done_when": "Read the setup file in full",
            "then_mark": _py() + " --mark-setup",
        }
    if phase == "need_read_run":
        return {
            "id": "read_run",
            "do": "Read",
            "paths": [_abs("references/run.md"), _abs("references/data-sources.md")],
            "done_when": "Read both files, then run the command that matches this mode",
            "then_mark": _py() + " --mark-run",
        }
    if phase == "need_present":
        return {
            "id": "deliver_note",
            "do": "reply",
            "command": "Give the note or the tracking setup in the user's language. One answer. No method dump. Then "
            + _py()
            + " --mark-presented",
            "done_when": "delivered",
        }
    return {"id": "done", "do": "none", "command": "", "done_when": "delivered"}


def progress_payload(phase: str, session: dict | None, blockers: list | None = None) -> dict:
    body = session or {}
    return {
        "ok": True,
        "phase": phase,
        "next_action": next_action(phase, session),
        "blockers": list(blockers or []),
        "session_id": body.get("session_id"),
        "instruction": _INSTRUCTION,
    }
