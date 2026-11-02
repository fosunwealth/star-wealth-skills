import argparse
from _client import (
 build_client,
 dump_with_directive,
 ensure_user_confirmed,
 refresh_account_index,
 run,
 sim_account_create,
)
EPILOG = 'When to call: the user explicitly asks to create a paper account. Tell them it starts with 1,000,000 HKD and 1,000,000 USD, then pass --confirm only after they agree. Without --confirm, NEED_CONFIRMATION blocks the call.'
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
  description="Create a paper-trading securities account (1,000,000 in cash for HKD and USD each)",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument(
  "--intent",
  required=True,
  help=(
   "**required**: Restate in English the intent of creating this paper account. Example: \"create a "
   "new paper-trading securities account with 1,000,000 in cash for HKD and USD each\"."
  ),
 )
 a.add_argument("--confirm", action="store_true",
      help="required: add this flag only after the user has explicitly confirmed creating the paper account")
 a.add_argument("--confirm-token",
      help="second-confirmation token: trigger NEED_CONFIRMATION once, copy the token from the returned message, then submit it together with --confirm")
 b = a.parse_args()
 ensure_user_confirmed(
  b.confirm,
  action="Create a paper account",
  intent_summary=b.intent,
  confirm_token=b.confirm_token,
 )
 c = build_client()
 d = sim_account_create(c)
 e = _refresh_index_safely(c)
 dump_with_directive(
  {
   "intent": b.intent,
   "result": d,
   "account_index_refresh": e,
  },
  next_action=(
   "The paper-account request was sent. Report the result, subAccountId, status, starting HKD and USD cash, and the cache refresh to the user in English, then stop.When reporting you must not give only the code "
   "number; you must also state the matching word status (for example code=0 means the request "
   "succeeded). Do not chain cash_summary, holdings, or order_*. Wait for the next request."
  ),
 )
if __name__ == "__main__":
 run(main)
