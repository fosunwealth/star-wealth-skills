import argparse
from _client import (
 build_client,
 call_with_account_retry,
 dump_with_directive,
 ensure_sub_account_class,
 ensure_trade_product_types,
 normalize_codes_inplace,
 run,
)
EPILOG = """When to call:\n  - the user asks about \"holdings / what did I buy / which stocks do I hold now\"\n\nExamples:\n  # all holdings\n  holdings.py\n  # Hong Kong stocks only\n  holdings.py --product-types 5\n  # US stocks only\n  holdings.py --product-types 6\n  # a single security\n  holdings.py --symbols hk00700\n"""
def main():
 a = argparse.ArgumentParser(
  description="Query current holdings",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id")
 a.add_argument("--start", type=int, default=0)
 a.add_argument("--count", type=int, default=100)
 a.add_argument(
  "--product-types", action="append", type=int,
  help="product type (may be passed more than once): 5=Hong Kong stocks 6=US stocks 7=China A-shares 15=options",
 )
 a.add_argument("--currencies", action="append")
 a.add_argument(
  "--symbols", "--code", "--stock-code", "--symbol",
  action="append",
  help=(
   "security filter (since v1.7.5 the \"user phrasing\" format is normalized automatically: `00700` becomes `hk00700`, `AAPL` becomes `usAAPL`; may be passed more than once); "
   "aliases accepted are --code/--stock-code/--symbol (guards against invented argument names)"
  ),
 )
 a.add_argument("--use-us-pre", action="store_true")
 a.add_argument("--use-us-post", action="store_true")
 a.add_argument("--use-us-night", action="store_true")
 a.add_argument("--client-id", type=int)
 a.add_argument("--apply-account-id")
 a.add_argument("--sub-account-class", type=int)
 b = a.parse_args()
 normalize_codes_inplace(b, "symbols")
 ensure_trade_product_types(b.product_types)
 ensure_sub_account_class(b.sub_account_class)
 c = build_client()
 def d(sub_account_id):
  return c.portfolio.get_holdings(
   sub_account_id=sub_account_id,
   start=b.start,
   count=b.count,
   product_types=b.product_types,
   currencies=b.currencies,
   symbols=b.symbols,
   use_us_pre=b.use_us_pre,
   use_us_post=b.use_us_post,
   use_us_night=b.use_us_night,
   client_id=b.client_id,
   apply_account_id=b.apply_account_id,
   sub_account_class=b.sub_account_class,
  )
 dump_with_directive(
  call_with_account_retry(c, d, b.sub_account_id),
  next_action=(
   "Positions are back. Report the names, quantities, and market values to the user in English, then stop.**Do not** chain any other script such as "
   "cash_summary, cash_flows, or order_* automatically: the one-step principle (rule number 0)."
  ),
 )
if __name__ == "__main__":
 run(main)
