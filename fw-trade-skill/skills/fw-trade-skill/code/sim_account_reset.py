import argparse
from _client import (
 build_client,
 dump_with_directive,
 ensure_user_confirmed,
 refresh_account_index,
 run,
 sim_account_reset,
)
EPILOG = 'When to call: the user explicitly asks to reset one paper account. Pass --sub-account-id of that old account; do not pick one. Tell them the old account will be disabled and a new one created with 1,000,000 HKD and 1,000,000 USD, then pass --confirm only after they agree. Without --confirm, NEED_CONFIRMATION blocks the call. Resets must be 7 days apart.'
def _refresh_index_safely(client):
 try:
  a = refresh_account_index(client)
  return {
   "refreshed": True,
   "accounts_summary": {
    "mock": len(a.get("mock") or []),
    "real_stock": len(a.get("real_stock") or []),
    "real_option": len(a.get("real_option") or []),
   },
   "refreshedAt": a.get("refreshedAt"),
  }
 except Exception as b:
  return {
   "refreshed": False,
   "error": f"{type(b).__name__}: {b}",
  }
def main():
 a = argparse.ArgumentParser(
  description="Reset a paper-trading securities account (disable the old one and create a new one)",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id", required=True, help="old paper-trading securities account ID (required)")
 a.add_argument(
  "--intent",
  required=True,
  help=(
   "**required**: Restate in English the intent of resetting this paper account, and it must include the old subAccountId. Example: \"reset old paper "
   "account 8: disable the old account and create a new paper account with 1,000,000 in cash for HKD and USD each\"."
  ),
 )
 a.add_argument("--confirm", action="store_true",
      help="required: add this flag only after the user has explicitly confirmed resetting the paper account")
 a.add_argument("--confirm-token",
      help="second-confirmation token: trigger NEED_CONFIRMATION once, copy the token from the returned message, then submit it together with --confirm")
 b = a.parse_args()
 ensure_user_confirmed(
  b.confirm,
  action="Reset a paper account",
  intent_summary=b.intent,
  confirm_token=b.confirm_token,
 )
 c = build_client()
 d = sim_account_reset(c, b.sub_account_id)
 e = _refresh_index_safely(c)
 dump_with_directive(
  {
   "intent": b.intent,
   "oldSubAccountId": b.sub_account_id,
   "result": d,
   "account_index_refresh": e,
  },
  next_action=(
   'The paper-account reset was sent. Report the old subAccountId, the new subAccountId, the reset count, and the status in English, then stop.'
  ),
 )
if __name__ == "__main__":
 run(main)
