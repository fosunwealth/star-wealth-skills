from __future__ import annotations
import argparse
from _client import build_client, dump_with_directive, normalize_codes_inplace, run
def main():
 a = argparse.ArgumentParser(description="Query the broker queue for the bid and ask sides")
 a.add_argument(
  "--code", "--stock-code", "--symbol", "--symbols",
  required=True,
  help=(
   "security code (since v1.7.5 the \"user phrasing\" format is normalized automatically: `01810` becomes `hk01810`, `AAPL` becomes `usAAPL`); aliases "
   "accepted are --stock-code/--symbol/--symbols (guards against invented argument names)"
  ),
 )
 b = a.parse_args()
 normalize_codes_inplace(b, "code")
 c = build_client()
 dump_with_directive(
  c.market.broker_list(code=b.code),
  next_action="The broker queue is back. Report it to the user in English, then stop. Do not chain order_*. One step.",
 )
if __name__ == "__main__":
 run(main)
