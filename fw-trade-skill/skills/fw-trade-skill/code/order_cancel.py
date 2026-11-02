import argparse
from _client import (
 build_client,
 call_with_account_retry,
 dump_with_directive,
 ensure_order_cancel_effective,
 ensure_user_confirmed,
 resolve_market_args,
 run,
)
EPILOG = 'When to call: the user says cancel that order. --market must match the order. If the order id is unknown, run order_list.py and let them pick. Pass --intent and --confirm only after they explicitly agree; otherwise NEED_CONFIRMATION. Whether the order can be cancelled is decided by the server.'
def main():
 a = argparse.ArgumentParser(
  description="Cancel an unfilled or partially filled order",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--order-id", required=True)
 a.add_argument("--sub-account-id")
 a.add_argument("--client-id", type=int)
 a.add_argument("--market", choices=["hk", "us"],
      help="recommended: resolves product_type in one step; hk=5 (Hong Kong stocks) us=6 (US stocks); mutually exclusive with --product-type")
 a.add_argument("--product-type", type=int, choices=[5, 6],
      help="advanced usage (mutually exclusive with --market); 5=Hong Kong stocks 6=US stocks, and it must match the market of the original order")
 a.add_argument("--apply-account-id")
 a.add_argument(
  "--intent",
  required=True,
  help=(
   'Required. English intent: the order id, market, security, and side. Printed into the NEED_CONFIRMATION prompt.'
  ),
 )
 a.add_argument("--confirm", action="store_true",
      help="required: add this flag only after the user has explicitly confirmed the cancellation intent; otherwise NEED_CONFIRMATION blocks it")
 a.add_argument("--confirm-token",
      help="second-confirmation token: trigger NEED_CONFIRMATION once, copy the token from the returned message, then submit it together with --confirm")
 b = a.parse_args()
 ensure_user_confirmed(
  b.confirm,
  action="Cancel order",
  intent_summary=b.intent,
  confirm_token=b.confirm_token,
 )
 c, c, b.product_type = resolve_market_args(
  b.market, None, None, b.product_type,
  require_currency=False,
 )
 d = build_client()
 def e(sub_account_id):
  return d.trade.cancel_order(
   order_id=b.order_id,
   sub_account_id=sub_account_id,
   client_id=b.client_id,
   product_type=b.product_type,
   apply_account_id=b.apply_account_id,
  )
 f = call_with_account_retry(d, e, b.sub_account_id)
 g = ensure_order_cancel_effective(f)
 dump_with_directive(
  {"intent": b.intent, **g, "result": f},
  next_action=(
   'The cancel was sent. Report the order id and the status words in English, then stop.'
  ),
 )
if __name__ == "__main__":
 run(main)
