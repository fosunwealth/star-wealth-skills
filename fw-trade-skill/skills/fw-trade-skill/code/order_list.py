import argparse
from datetime import date, timedelta
from _client import (
 StructuredScriptError,
 build_client,
 call_with_account_retry,
 dump,
 ensure_trade_markets,
 ensure_trade_show_type,
 normalize_codes_inplace,
 run,
)
ACTIVE_STATUS_CODES = [10, 20, 22, 23, 40, 60]
EPILOG = "When to call: the user asks for today's orders or which orders are still open. The script fills the last 7 days when dates are omitted and defaults to count=20. There is no --order-id filter; narrow with --stock-code, market, dates, or --active-only. APIERROR_50001: retry once with --count 50. Session expired is a stale credential, not a missing order."
def main():
 a = argparse.ArgumentParser(
  description="Query the order list with paging",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id")
 a.add_argument("--start", type=int, default=0)
 a.add_argument("--count", type=int, default=20)
 a.add_argument(
  "--stock-code", "--code", "--symbol", "--symbols",
  help=(
   "security filter (since v1.7.5 the \"user phrasing\" format is normalized automatically: `00700` becomes `hk00700`, `AAPL` becomes `usAAPL`); aliases "
   "accepted are --code/--symbol/--symbols (guards against invented argument names)"
  ),
 )
 a.add_argument("--status-arr", action="append", type=int,
      help="filter by status code (may be passed more than once); mutually exclusive with --active-only")
 a.add_argument("--active-only", action="store_true",
      help="show only orders that are \"not done yet\" (expanded automatically to status 10/20/22/23/40/60); mutually exclusive with --status-arr")
 a.add_argument("--from-date", help="start date yyyy-mm-dd (defaults to 7 days ago)")
 a.add_argument("--to-date", help="end date yyyy-mm-dd (defaults to today)")
 a.add_argument("--direction", type=int, choices=[1, 2], help="1=buy 2=sell (matches the gateway direction)")
 a.add_argument("--market", action="append", help="may be passed more than once: hk us")
 a.add_argument("--sort", default="desc", choices=["desc", "asc"])
 a.add_argument("--client-id", type=int)
 a.add_argument("--apply-account-id")
 a.add_argument(
  "--show-type",
  type=int,
  choices=[0, 1, 2],
  help=(
   "display type showType: 0=stock orders only 1=stock and option orders 2=option orders only (matches the OrderList documentation); do not pass 1 or 2, "
   "use the default or an explicit 0"
  ),
 )
 b = a.parse_args()
 normalize_codes_inplace(b, "stock_code")
 ensure_trade_markets(b.market)
 ensure_trade_show_type(b.show_type)
 if b.active_only and b.status_arr:
  raise StructuredScriptError(
   "`--active-only` and `--status-arr` are mutually exclusive: the former is already fixed to status 10/20/22/23/40/60, and adding --status-arr on top makes the filter ambiguous.",
   error_code="INVALID_PARAM",
   hint="Passing both `--active-only` and `--status-arr` makes the two intents overwrite each other, so it is impossible to tell which statuses you actually want.",
   next_action="Use one filter. Open orders: `--active-only` only. A custom status set: `--status-arr` only.",
   exit_code=2,
  )
 c = ACTIVE_STATUS_CODES if b.active_only else b.status_arr
 d = build_client()
 e = date.today()
 f = b.from_date or (e - timedelta(days=7)).isoformat()
 g = b.to_date or e.isoformat()
 def h(sub_account_id):
  return d.trade.list_orders(
   sub_account_id=sub_account_id,
   start=b.start,
   count=b.count,
   stock_code=b.stock_code,
   status_arr=c,
   from_date=f,
   to_date=g,
   direction=b.direction,
   market=b.market,
   sort=b.sort,
   client_id=b.client_id,
   apply_account_id=b.apply_account_id,
   show_type=b.show_type,
  )
 dump(call_with_account_retry(d, h, b.sub_account_id))
if __name__ == "__main__":
 run(main)
