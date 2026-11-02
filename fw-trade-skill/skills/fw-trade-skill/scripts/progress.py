#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One next_action for fw-tradings."""
from __future__ import annotations
import argparse, json, os, sys, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ROUTES = {"paper": "moni-trade-skill/subSKILL.md", "live": "real-trade-skill/subSKILL.md", "setup": "fosun-env-setup/subSKILL.md"}
LIVE, PAPER = ("live", "real money", "\u5b9e\u76d8"), ("paper", "demo", "\u6a21\u62df")
SETUP = ("replace my key", "use my api", "open the app", "\u5f00\u901a", "api key", "token")
NOTE = "Run only this next_action, then scripts/progress.py again. Do not skip, open an unnamed subskill, show this JSON, or print key material."
PY = "python3 scripts/progress.py"

def state_dir():
 raw = (os.environ.get("FW_TRADE_STATE_DIR") or "").strip()
 return Path(raw) if raw else Path.home() / ".workbuddy" / "fw-tradings"

def load():
 try:
  data = json.loads((state_dir() / "session.json").read_text(encoding="utf-8"))
 except (OSError, json.JSONDecodeError):
  return None
 return data if isinstance(data, dict) else None

def save(data):
 path = state_dir() / "session.json"
 path.parent.mkdir(parents=True, exist_ok=True)
 path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def classify(query):
 text = (query or "").strip()
 low = text.lower()
 route = "setup" if any(h in low for h in SETUP) else "live" if any(h in low for h in LIVE) else "paper" if any(h in low for h in PAPER) else ""
 return {"query": text, "route": route}

def new_session(query):
 found = classify(query)
 return {"session_id": uuid.uuid4().hex, "query": found["query"], "route": found["route"], "route_read": False, "done": False}

STATUS = "FSOPENAPI_API_KEY_STATUS"

def env_path():
 raw = (os.environ.get("FOSUN_ENV_PATH") or "fosun.env").strip()
 path = Path(os.path.expandvars(os.path.expanduser(raw)))
 if not path.is_absolute():
  path = Path.home() / ".workbuddy" / "star-wealth-openapi" / path
 return path

def has_credential():
 try:
  lines = env_path().read_text(encoding="utf-8").splitlines()
 except OSError:
  return False
 for line in lines:
  text = line.strip()
  if not text or text.startswith("#") or "=" not in text:
   continue
  key, _, value = text.partition("=")
  if key.strip() == STATUS:
   return value.strip().strip('"').strip("'").lower() == "valid"
 return False

def phase_of(session, ready):
 if not ready:
  return "need_activation"
 if not session:
  return "need_start"
 route = session.get("route") or ""
 if route not in ROUTES:
  return "need_choose_route"
 if not session.get("route_read"):
  return "need_read_route"
 return "done" if session.get("done") else "need_act"

def action(phase, session):
 route = (session or {}).get("route") or ""
 if phase == "need_read_route":
  return {"id": "read_route", "do": "Read", "paths": [str(ROOT / ROUTES[route])], "then_mark": PY + " --mark-route --route " + route}
 table = {
  "need_activation": {"id": "activate", "do": "run", "command": "python3 fosun-env-setup/code/ensure_fosun_env.py"},
  "need_start": {"id": "start", "do": "run", "command": PY + ' --query "<latest user question>"'},
  "need_choose_route": {"id": "choose_route", "do": "run", "command": PY + " --mark-route --route paper|live|setup"},
  "need_act": {"id": "act", "do": "run", "command": "Follow the subskill just read, then " + PY + " --mark-done"},
 }
 return table.get(phase, {"id": "done", "do": "none"})

def emit(phase, session, blockers=None):
 print(json.dumps({"ok": True, "phase": phase, "next_action": action(phase, session), "blockers": list(blockers or []), "session_id": (session or {}).get("session_id"), "instruction": NOTE}, ensure_ascii=False))

def fail(message, phase, session):
 print(message, file=sys.stderr)
 emit(phase, session, [message])
 return 2

def main():
 parser = argparse.ArgumentParser()
 parser.add_argument("--query", default="")
 parser.add_argument("--mark-route", action="store_true")
 parser.add_argument("--route", default="")
 parser.add_argument("--mark-done", action="store_true")
 args = parser.parse_args()
 ready = has_credential()
 if args.query:
  if not ready:
   emit("need_activation", None, ["Star Wealth OpenAPI credential is not activated"])
   return 2
  session = new_session(args.query)
  save(session)
  emit(phase_of(session, True), session)
  return 0
 session = load()
 if not ready:
  emit("need_activation", session, ["Star Wealth OpenAPI credential is not activated"])
  return 2
 if not (args.mark_route or args.mark_done):
  emit(phase_of(session, True), session)
  return 0
 if session is None:
  return fail("no session; run progress.py --query first", "need_start", None)
 current = phase_of(session, True)
 if args.mark_route:
  route = (args.route or session.get("route") or "").strip()
  if current not in ("need_choose_route", "need_read_route"):
   return fail("route is not the current phase", current, session)
  if route not in ROUTES:
   return fail("route must be paper, live, or setup", current, session)
  had = session.get("route") or ""
  session["route"] = route
  session["route_read"] = had == route and current == "need_read_route"
 else:
  if current != "need_act":
   return fail("act is not the current phase", current, session)
  session["done"] = True
 save(session)
 emit("done" if session.get("done") else phase_of(session, True), session)
 return 0

if __name__ == "__main__":
 sys.exit(main())
