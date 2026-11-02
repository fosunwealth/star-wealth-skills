from __future__ import annotations
import argparse
from _client import build_client, dump_with_directive, normalize_codes_inplace, run
def main():
 a = argparse.ArgumentParser(description="Query candlestick (K-line) data")
 a.add_argument(
  "--code", "--stock-code", "--symbol", "--symbols",
  required=True,
  help=(
   "security code (since v1.7.5 the \"user phrasing\" format is normalized automatically: `01810` becomes `hk01810`, `AAPL` becomes `usAAPL`); aliases "
   "accepted are --stock-code/--symbol/--symbols (guards against invented argument names)"
  ),
 )
 a.add_argument("--ktype", required=True,
      help="min1/min5/min15/min30/min60/day/week/month/quarter/year")
 a.add_argument("--delay", action="store_true")
 a.add_argument("--num", type=int)
 a.add_argument("--right", choices=["noward", "forward", "backward"])
 a.add_argument("--start-time", type=int)
 a.add_argument("--end-time", type=int)
 a.add_argument("--time", type=int)
 a.add_argument("--suspension", type=int)
 b = a.parse_args()
 normalize_codes_inplace(b, "code")
 c = build_client()
 dump_with_directive(
  c.market.kline(
   code=b.code,
   ktype=b.ktype,
   delay=b.delay or None,
   end_time=b.end_time,
   num=b.num,
   right=b.right,
   start_time=b.start_time,
   suspension=b.suspension,
   time=b.time,
  ),
  next_action="Candles are back. Report the move to the user in English, then stop. Do not chain order_*. One step.",
 )
if __name__ == "__main__":
 run(main)
