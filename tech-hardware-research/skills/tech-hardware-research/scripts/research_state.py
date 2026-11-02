# -*- coding: utf-8 -*-
"""Phase queue for tech-hardware-research. One next_action, one disclosure."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SESSION_DIR_NAME = "tech-hardware-research"

SECTOR_FILES = {
    "semiconductor": "references/03-semiconductor.md",
    "consumer-electronics": "references/04-consumer-electronics.md",
    "ai-compute": "references/05-ai-compute.md",
    "display-panel": "references/06-display-panel.md",
    "communication": "references/07-communication.md",
    "auto-electronics": "references/08-auto-electronics.md",
}

WORKSPACE_FILES = (
    "00_overview.md",
    "01_desk_research.md",
    "02_open_questions.md",
    "03_fieldwork.md",
    "04_tracking.md",
    "05_pitfalls.md",
)

# Longer phrases first. Optical modules are AI compute; a bare "optical" is not.
_SECTOR_HINTS = (
    (
        "ai-compute",
        (
            "optical module",
            "optical-module",
            "hbm",
            "gpu",
            "ai compute",
            "liquid cool",
            "\u5149\u6a21\u5757",
            "\u7b97\u529b",
        ),
    ),
    (
        "display-panel",
        ("display panel", "miniled", "microled", "oled", "lcd", "panel", "\u9762\u677f"),
    ),
    (
        "auto-electronics",
        (
            "automotive electronic",
            "auto electronic",
            "aec-q",
            "sic mosfet",
            "\u6c7d\u8f66\u7535\u5b50",
            "\u8f66\u89c4",
        ),
    ),
    (
        "consumer-electronics",
        (
            "consumer electronic",
            "smartphone",
            "iphone",
            "apple chain",
            "tws",
            "\u6d88\u8d39\u7535\u5b50",
        ),
    ),
    (
        "communication",
        (
            "communications hardware",
            "base station",
            "carrier capex",
            "carrier",
            "\u901a\u4fe1\u786c\u4ef6",
            "\u8fd0\u8425\u5546",
        ),
    ),
    (
        "semiconductor",
        (
            "semiconductor",
            "foundry",
            "wafer",
            "nand",
            "dram",
            "osat",
            "tsmc",
            "\u534a\u5bfc\u4f53",
            "\u6676\u5706",
            "\u53f0\u79ef\u7535",
        ),
    ),
)

_WORKSPACE_HINTS = (
    "workspace",
    "scaffold",
    "set up a research",
    "\u7814\u7a76\u5de5\u4f5c\u533a",
    "\u642d\u4e00\u4e2a",
    "\u642d\u4e2a",
)
_REPORT_HINTS = (
    "report only",
    "already supplied",
    "notes and the figures",
    "skip the fieldwork",
    "\u53ea\u51fa\u62a5\u544a",
    "\u5df2\u6709\u7b14\u8bb0",
    "\u5df2\u6709\u6570\u636e",
)
_QUESTION_HINTS = (
    "how do",
    "how to",
    "how should",
    "map the",
    "\u600e\u4e48\u7814\u7a76",
    "\u600e\u4e48\u62c6",
    "\u4ea7\u4e1a\u94fe",
)

_INSTRUCTION = (
    "Run only this next_action. Then you may run research_progress.py again. "
    "Do not skip steps. Do not open a file that this next_action does not name. "
    "Do not show this JSON to the user. All user-facing text is English."
)


def session_dir(root: Path | None = None) -> Path:
    if root is not None:
        return root
    override = (os.environ.get("TECH_HARDWARE_STATE_DIR") or "").strip()
    if override:
        return Path(override)
    return Path.home() / ".workbuddy" / SESSION_DIR_NAME


def session_path(root: Path | None = None) -> Path:
    return session_dir(root) / "session.json"


def sources_path(root: Path | None = None) -> Path:
    return session_dir(root) / "sources.json"


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
    lowered = text.lower()
    sector = ""
    for key, hints in _SECTOR_HINTS:
        if any(hint.lower() in lowered for hint in hints):
            sector = key
            break
    if any(hint.lower() in lowered for hint in _WORKSPACE_HINTS):
        mode = "workspace"
    elif any(hint.lower() in lowered for hint in _REPORT_HINTS):
        mode = "report"
    elif any(hint.lower() in lowered for hint in _QUESTION_HINTS):
        mode = "question"
    else:
        mode = "full"
    return {"query": text, "mode": mode, "sector": sector}


def new_session(query: str) -> dict:
    classified = classify(query)
    return {
        "session_id": uuid.uuid4().hex,
        "query": classified["query"],
        "mode": classified["mode"],
        "sector": classified["sector"],
        "playbook_read": False,
        "sector_read": False,
        "framework_read": False,
        "verify_read": False,
        "fetch_done": False,
        "pitfalls_read": False,
        "tracking_read": False,
        "report_path": "",
        "workspace": "",
        "presented": False,
    }


def infer_phase(session: dict | None, *, has_key: bool) -> str:
    if session is None:
        return "need_start" if has_key else "need_activation"
    mode = session.get("mode") or "full"
    sector = session.get("sector") or ""
    if not session.get("playbook_read"):
        return "need_read_playbook"
    if mode == "workspace":
        if sector not in SECTOR_FILES:
            return "need_read_sector"
        if not session.get("workspace"):
            return "need_scaffold"
        if not session.get("presented"):
            return "need_present"
        return "done"
    if sector not in SECTOR_FILES or not session.get("sector_read"):
        return "need_read_sector"
    if mode in ("full", "report") and not session.get("framework_read"):
        return "need_read_framework"
    if mode == "full" and not session.get("verify_read"):
        return "need_read_verify"
    if mode in ("full", "question") and not session.get("fetch_done"):
        return "need_fetch"
    if mode in ("full", "report") and not session.get("pitfalls_read"):
        return "need_read_pitfalls"
    if mode == "full" and not session.get("tracking_read"):
        return "need_read_tracking"
    if not session.get("report_path"):
        return "need_write"
    if not session.get("presented"):
        return "need_present"
    return "done"


def _abs(relative: str) -> str:
    return str(SKILL_ROOT / relative)


def _py() -> str:
    return "python3 scripts/research_progress.py"


def next_action(phase: str, session: dict | None, root: Path | None = None) -> dict:
    session = session or {}
    mode = session.get("mode") or "full"
    sector = session.get("sector") or ""
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
    if phase == "need_read_sector":
        if sector not in SECTOR_FILES:
            keys = "|".join(SECTOR_FILES)
            return {
                "id": "choose_sector",
                "do": "run",
                "command": _py() + " --mark-sector --sector <" + keys + ">",
                "done_when": "sector is one of the six keys",
            }
        if not session.get("sector_read") and (session.get("mode") or "full") != "workspace":
            return {
                "id": "read_sector",
                "do": "Read",
                "paths": [_abs(SECTOR_FILES[sector])],
                "done_when": "Read that one sector file in full. Do not open the other sector files.",
                "then_mark": _py() + " --mark-sector --sector " + sector,
            }
        return {
            "id": "choose_sector",
            "do": "run",
            "command": _py() + " --mark-sector --sector " + sector,
            "done_when": "sector is set",
        }
    if phase == "need_read_framework":
        return {
            "id": "read_framework",
            "do": "Read",
            "paths": [_abs("references/02-general-framework.md")],
            "done_when": "Read the framework file in full",
            "then_mark": _py() + " --mark-framework",
        }
    if phase == "need_read_verify":
        return {
            "id": "read_verify",
            "do": "Read",
            "paths": [_abs("references/09-verification-methods.md")],
            "done_when": "Read the verification file in full",
            "then_mark": _py() + " --mark-verify",
        }
    if phase == "need_fetch":
        minimum = 26 if mode == "full" else 1
        src = str(sources_path(root))
        return {
            "id": "fetch",
            "do": "Read",
            "paths": [
                _abs("references/fetch-checklist.md"),
                _abs("references/12-tools-datasources.md"),
            ],
            "command": "WebSearch then WebFetch. Write " + src + " then " + _py() + " --mark-fetch",
            "sources_path": src,
            "min_items": minimum,
            "done_when": "sources.json has the required items and --mark-fetch has run",
        }
    if phase == "need_read_pitfalls":
        return {
            "id": "read_pitfalls",
            "do": "Read",
            "paths": [_abs("references/11-pitfalls.md")],
            "done_when": "Read the pitfalls file in full",
            "then_mark": _py() + " --mark-pitfalls",
        }
    if phase == "need_read_tracking":
        return {
            "id": "read_tracking",
            "do": "Read",
            "paths": [_abs("references/10-tracking-system.md")],
            "done_when": "Read the tracking file in full",
            "then_mark": _py() + " --mark-tracking",
        }
    if phase == "need_write":
        return {
            "id": "write_report",
            "do": "Read",
            "paths": [
                _abs("references/report-contract.md"),
                _abs("assets/report_template.html"),
            ],
            "command": "Write one HTML file from the template, then " + _py() + " --mark-written --report <html path>",
            "done_when": "the HTML file exists and --mark-written has run",
        }
    if phase == "need_scaffold":
        sector_arg = sector if sector in SECTOR_FILES else "<sector>"
        return {
            "id": "scaffold",
            "do": "run",
            "command": 'python3 scripts/research_scaffold.py --name "<name>" --sector '
            + sector_arg
            + " --out ./research",
            "then_mark": _py() + " --mark-scaffolded --workspace <directory>",
            "done_when": "the six workspace files exist",
        }
    if phase == "need_present":
        present = session.get("report_path") or ""
        if not present and session.get("workspace"):
            present = str(Path(session["workspace"]) / "00_overview.md")
        return {
            "id": "deliver_file",
            "do": "deliver_file",
            "present_path": present,
            "command": "give present_path to the user (attach the file when the host supports it), then give the full absolute path and one or two sentences. Then "
            + _py()
            + " --mark-presented",
            "done_when": "delivered",
        }
    return {"id": "done", "do": "none", "command": "", "done_when": "delivered"}


def progress_payload(phase: str, session: dict | None, blockers: list | None = None, root: Path | None = None) -> dict:
    body = session or {}
    return {
        "ok": True,
        "phase": phase,
        "next_action": next_action(phase, session, root),
        "blockers": list(blockers or []),
        "session_id": body.get("session_id"),
        "instruction": _INSTRUCTION,
    }


def count_source_items(path: Path) -> tuple:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, "sources.json is missing or is not JSON"
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return 0, "sources.json must be an object with an items list"
    accepted = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        blob = json.dumps(item, ensure_ascii=False).lower()
        if "not yet fetched" in blob:
            return 0, "sources.json still contains 'not yet fetched'"
        unavailable = item.get("unavailable")
        if isinstance(unavailable, dict):
            if unavailable.get("looked") and unavailable.get("why") and unavailable.get("substitute"):
                accepted += 1
            continue
        if item.get("value") and item.get("source") and item.get("date"):
            accepted += 1
    return accepted, ""


def report_is_html(path: Path) -> str:
    if not path.is_file():
        return "report file does not exist"
    if path.suffix.lower() not in (".html", ".htm"):
        return "report must be an HTML file"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return "report could not be read: " + str(exc)
    if "not yet fetched" in text.lower():
        return "report still contains 'not yet fetched'"
    if not text.strip():
        return "report is empty"
    return ""


def workspace_is_complete(path: Path) -> str:
    if not path.is_dir():
        return "workspace directory does not exist"
    missing = [name for name in WORKSPACE_FILES if not (path / name).is_file()]
    if missing:
        return "workspace is missing " + ", ".join(missing)
    return ""
