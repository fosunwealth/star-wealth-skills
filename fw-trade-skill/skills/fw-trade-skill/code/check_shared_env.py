from __future__ import annotations
import argparse
import json
import sys
from _client import MODE, build_client, refresh_account_index, shared_env_path
EPILOG = 'When to call: a health check, especially when the credential may be stale, and the first run after install. status=valid means the credential works. An account-availability flag of false means this mode has no usable sub-account and business scripts will refuse. status=invalid: repair it with fosun-env-setup.'
NEXT_ACTION_VALID_HAS_ACCOUNT = (
 "The credential is valid and this entry's sub-account is available. Report that to the user in English and wait for a specific request;"
 "do not chain another business script."
)
NEXT_ACTION_VALID_NO_ACCOUNT = (
 f"The credential is valid, but there is no {MODE.label} sub-account (subAccountType={MODE.sub_account_type}). Tell the user in English and stop. Wait for the user to decide whether "
 f"to open a {MODE.label} account at the broker before continuing; you must not switch to the {MODE.other_label} skill."
)
NEXT_ACTION_INVALID = (
 "The shared credential is unusable. First generate or repair a valid fosun.env through the sibling fosun-env-setup; do not call any business "
 "script before the credential is restored."
)
def main():
 argparse.ArgumentParser(
  description="Health check: whether the shared credential works, plus a refresh of the account index cache",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 ).parse_args()
 try:
  a = build_client()
  b = refresh_account_index(a)
  c = {
   "mock": len(b.get("mock") or []),
   "real_stock": len(b.get("real_stock") or []),
   "real_option": len(b.get("real_option") or []),
  }
  d = c[MODE.account_type] > 0
  e = {
   "status": "valid",
   "next_action": NEXT_ACTION_VALID_HAS_ACCOUNT if d else NEXT_ACTION_VALID_NO_ACCOUNT,
   MODE.account_available_key: d,
   "env_path": str(shared_env_path()),
   "message": "The shared credential works and the account index has been refreshed",
   "refreshedAt": b.get("refreshedAt"),
   "counts": c,
  }
  print(json.dumps(e, ensure_ascii=False, indent=2))
 except Exception as f:
  e = {
   "status": "invalid",
   "next_action": NEXT_ACTION_INVALID,
   "env_path": str(shared_env_path()),
   "message": f"{type(f).__name__}: {f}",
   "action": "First make sure, through the sibling fosun-env-setup, that the shared credential file FOSUN_ENV_PATH points at has been generated and is valid",
  }
  print(json.dumps(e, ensure_ascii=False, indent=2), file=sys.stderr)
  sys.exit(1)
if __name__ == "__main__":
 main()
