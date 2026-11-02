import argparse
from _client import (
 build_client,
 call_with_account_retry,
 dump_with_directive,
 ensure_sub_account_class,
 run,
)
EPILOG = """When to call:\n  - the user asks about \"cash movements / deposits and withdrawals / fund changes / what was bought and sold today\"\n\nExamples:\n  # everything by default\n  cash_flows.py\n  # a single day\n  cash_flows.py --date 2026-04-23\n  # a range\n  cash_flows.py --trade-date-from 2026-04-01 --trade-date-to 2026-04-23\n"""
def main():
 a = argparse.ArgumentParser(
  description="Query cash movements",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id")
 a.add_argument("--apply-account-id")
 a.add_argument(
  "--sub-account-class",
  type=int,
  help=(
   "subAccountClass: the gateway defaults to 1 for the main account; for 9, the option account, see the CashFlows documentation. **Only stock cash "
   "movements may be queried, so 9 is forbidden** (blocked locally)."
  ),
 )
 a.add_argument("--business-type", action="append", type=int)
 a.add_argument("--date", help="a single day, YYYY-MM-DD")
 a.add_argument("--flow-type", type=int)
 a.add_argument("--trade-date-from")
 a.add_argument("--trade-date-to")
 b = a.parse_args()
 ensure_sub_account_class(b.sub_account_class)
 c = build_client()
 def d(sub_account_id):
  return c.trade.get_cash_flows(
   sub_account_id=sub_account_id,
   apply_account_id=b.apply_account_id,
   sub_account_class=b.sub_account_class,
   business_type=b.business_type,
   date=b.date,
   flow_type=b.flow_type,
   trade_date_from=b.trade_date_from,
   trade_date_to=b.trade_date_to,
  )
 dump_with_directive(
  call_with_account_retry(c, d, b.sub_account_id),
  next_action=(
   "Cash movements are back. Report them to the user in English, then stop.**Do not** chain any other script such as "
   "cash_summary, holdings, or order_* automatically: the one-step principle (rule number 0)."
  ),
 )
if __name__ == "__main__":
 run(main)
