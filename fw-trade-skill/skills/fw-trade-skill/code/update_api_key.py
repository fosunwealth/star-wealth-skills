#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
_SETUP_CODE = Path(__file__).resolve().parent.parent / "fosun-env-setup" / "code"
if str(_SETUP_CODE) not in sys.path:
 sys.path.insert(0, str(_SETUP_CODE))
from ensure_fosun_env import update_api_key
from _client import run
def main():
 a = argparse.ArgumentParser(
  description="Update FSOPENAPI_API_KEY in fosun.env (provided by the user after the reset scan)"
 )
 a.add_argument("--api-key", required=True, help="the API Key copied from the page")
 a.add_argument(
  "--server-public-key",
  required=True,
  help="the full server public key PEM copied from the page (required together with the apikey)",
 )
 b = a.parse_args()
 c = update_api_key(
  b.api_key,
  server_public_key=b.server_public_key,
  finalize=True,
 )
 if c.get("status") == "valid":
  c.setdefault("ok", True)
  c.setdefault(
   "message",
   "The API Key has been written and verified; you can continue with the business you were doing.",
  )
 else:
  c.setdefault("ok", c.get("status") != "error")
  c.setdefault(
   "message",
   "The API Key has been written; if it is still not valid, finish the page steps described in operation_guide and then run ensure_fosun_env.py again.",
  )
 print(json.dumps(c, ensure_ascii=False, indent=2))
if __name__ == "__main__":
 run(main)
