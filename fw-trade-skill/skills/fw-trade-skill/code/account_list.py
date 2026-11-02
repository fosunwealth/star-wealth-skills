import argparse
from _client import MODE, build_client, dump_with_directive, refresh_account_index, run
EPILOG = 'When to call: the user asks which accounts they have, or says an account changed. Do not call it before every balance or holdings query. subAccountId is a string. If the account-availability flag is false, this mode has no usable sub-account and business scripts will refuse.'
NEXT_ACTION_HAS_ACCOUNT = (
 "Read the account list to the user in English, then wait for a specific request;"
 "Do not chain cash_summary, holdings, cash_flows, or order_*."
)
NEXT_ACTION_NO_ACCOUNT = (
 f"The current shared credential has no {MODE.label} sub-account (subAccountType={MODE.sub_account_type}). Tell the user the visible account list immediately and stop; wait for the "
 f"user to decide whether to open a {MODE.label} account at the broker, or whether to pass --sub-account-id explicitly for debugging. You must not switch to "
 f"the {MODE.other_label} skill on your own, and you must not pick another account to continue the current work."
)
def main():
 argparse.ArgumentParser(
  description="Query and refresh the account index (mock / real_stock / real_option)",
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
   "mock": c,
   "real_stock": d,
   "real_option": e,
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
