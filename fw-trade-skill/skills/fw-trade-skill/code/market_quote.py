from __future__ import annotations
import argparse
from _client import build_client, dump_with_directive, normalize_codes_inplace, run
def main():
 a = argparse.ArgumentParser(description="Query quotes for several securities at once")
 a.add_argument(
  "--code", "--stock-code", "--symbol", "--symbols",
  action="append", required=True,
  help=(
   "may be passed more than once, and the \"user phrasing\" format is supported (normalized automatically since "
   "v1.7.5): `01810` becomes `hk01810`, `AAPL` becomes `usAAPL`, `HK.00700` becomes `hk00700`, `us.aapl` becomes `usAAPL`. Aliases "
   "accepted are --stock-code/--symbol/--symbols (guards against invented argument names)"
  ),
 )
 a.add_argument("--field", action="append", help="may be passed more than once, for example --field price --field low")
 b = a.parse_args()
 normalize_codes_inplace(b, "code")
 c = build_client()
 dump_with_directive(
  c.market.quote(codes=b.code, fields=b.field),
  next_action=(
   "The quote is back. Report the price to the user in English, then stop.Decode price as raw/(10^power) and keep "
   "`power` decimal places.Do not guess the decimals.**Do not** chain order_* automatically: "
   "whether to place an order after the quote "
   "must be asked again; the one-step principle (rule number 0)."
  ),
 )
if __name__ == "__main__":
 run(main)
