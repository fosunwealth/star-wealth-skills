import argparse
from _client import build_client, call_with_account_retry, dump_with_directive, run
EPILOG = 'When to call: the user asks about balance, cash, or buying power. The script picks the sub-account from the shared cache. Hong Kong buying power is HKD only and US buying power is USD only. No FX.'
def main():
 a = argparse.ArgumentParser(
  description="Query account cash amounts",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id", help="securities account; by default the first one in this market type bucket of the shared credential cache is taken automatically")
 a.add_argument("--currency", help="HKD / USD / CNH; when omitted, all currencies are summarized")
 a.add_argument("--client-id", type=int)
 a.add_argument("--apply-account-id")
 b = a.parse_args()
 c = build_client()
 def d(sub_account_id):
  return c.portfolio.get_assets_summary(
   sub_account_id=sub_account_id,
   currency=b.currency,
   client_id=b.client_id,
   apply_account_id=b.apply_account_id,
  )
 dump_with_directive(
  call_with_account_retry(c, d, b.sub_account_id),
  next_action=(
   "Cash and buying power are back. Report the key figures to the user in English, then stop.**Do not** chain any other script such as "
   "holdings, cash_flows, or order_* automatically: the one-step principle (rule number 0)."
  ),
 )
if __name__ == "__main__":
 run(main)
