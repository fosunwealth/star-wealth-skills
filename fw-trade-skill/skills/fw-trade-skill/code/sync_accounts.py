from __future__ import annotations
import argparse
from _client import MODE, build_client, dump_with_directive, refresh_account_index, run
EPILOG = """When to call (only at these moments; do not run it on your own otherwise):\n  - the user clearly says \"I just opened a new account / an account changed, refresh it\"\n  - business scripts keep reporting account errors and the cache looks stale\n\nNormally the business scripts refresh the cache on demand, so **this does not have to run first**.\n"""
NEXT_ACTION_HAS_ACCOUNT = (
 "The account index has been refreshed into the shared credential. Report the refresh result to the user "
 "and wait for a clear next business request before continuing; Do not chain cash_summary, holdings, cash_flows, or order_*."
)
NEXT_ACTION_NO_ACCOUNT = (
 f"After the refresh no {MODE.label} sub-account (subAccountType={MODE.sub_account_type} was found. Tell the user the visible account list immediately and stop; wait for the user "
 f"to decide what to do next. You must not switch to the {MODE.other_label} skill on your own, and you must not pick another account to continue the current work."
)
def main():
 argparse.ArgumentParser(
  description="Force a refresh of the account index into the shared credential (run it only when an account has changed)",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 ).parse_args()
 a = build_client()
 b = refresh_account_index(a)
 c = b.get("mock") or []
 d = b.get("real_stock") or []
 e = b.get("real_option") or []
 f = bool(b.get(MODE.account_type) or [])
 dump_with_directive(
  {
   "refreshedAt": b.get("refreshedAt"),
   "accounts": {
    "mock": c,
    "real_stock": d,
    "real_option": e,
   },
  },
  next_action=NEXT_ACTION_HAS_ACCOUNT if f else NEXT_ACTION_NO_ACCOUNT,
  **{MODE.account_available_key: f},
  accounts_summary={
   "mock": len(c),
   "real_stock": len(d),
   "real_option": len(e),
  },
 )
if __name__ == "__main__":
 run(main)
