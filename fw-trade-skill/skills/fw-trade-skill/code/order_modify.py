import argparse
from _client import (
 build_client,
 call_with_account_retry,
 dump_with_directive,
 ensure_order_modify_effective,
 ensure_supported_modify_type,
 ensure_user_confirmed,
 resolve_market_args,
 run,
 StructuredScriptError,
)
UNSUPPORTED_MODIFY_FIELD_NAMES = {
 "trig_price": "--trig-price",
 "tail_type": "--tail-type",
 "tail_amount": "--tail-amount",
 "tail_pct": "--tail-pct",
 "spread": "--spread",
 "profit_price": "--profit-price",
 "profit_quantity": "--profit-quantity",
 "stop_loss_price": "--stop-loss-price",
 "stop_loss_quantity": "--stop-loss-quantity",
}
EPILOG = 'When to call: the user says change the price or the quantity. --modify-type is only 1. --market must match the original order. Only quantity and price can change. If the order id is unknown, run order_list.py. Pass --intent and --confirm only after they explicitly agree; otherwise NEED_CONFIRMATION.'
def validate_order_modify_args(args):
 ensure_supported_modify_type(args.modify_type)
 a = [
  e
  for d, e in UNSUPPORTED_MODIFY_FIELD_NAMES.items()
  if getattr(args, d) not in (None, "")
 ]
 if a:
  b = ", ".join(f"`{field}`" for field in a)
  raise StructuredScriptError(
   f"An ordinary modification does not support these conditional fields: {b}",
   error_code="INVALID_PARAM",
   hint="Only limit and market orders are supported; modification fields for conditional orders, trailing stops, and take-profit/stop-loss are not supported.",
   next_action="Drop those fields. To change price or size, use `--price` or `--quantity` and keep `--modify-type 1`.",
   exit_code=2,
  )
 c = [
  args.quantity,
  args.price,
 ]
 if not any(value not in (None, "") for value in c):
  raise StructuredScriptError(
   "The modification request carries no field to change.",
   error_code="INVALID_PARAM",
   hint="Modifying an ordinary order needs at least a new quantity or a new price.",
   next_action="Ask which field to change, restate the full change in English, and confirm again.",
   exit_code=2,
  )
def main():
 a = argparse.ArgumentParser(
  description="Modify an unfilled or partially filled order",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--order-id", required=True)
 a.add_argument("--modify-type", type=int, required=True,
      help="only 1 is allowed, meaning modify an ordinary order")
 a.add_argument("--quantity")
 a.add_argument("--sub-account-id")
 a.add_argument("--client-id", type=int)
 a.add_argument(
  "--price",
  help="new limit price after the change: used only when modifying an ordinary limit or market order",
 )
 a.add_argument("--trig-price", help=argparse.SUPPRESS)
 a.add_argument("--tail-type", type=int, help=argparse.SUPPRESS)
 a.add_argument("--tail-amount", help=argparse.SUPPRESS)
 a.add_argument("--tail-pct", help=argparse.SUPPRESS)
 a.add_argument("--spread", help=argparse.SUPPRESS)
 a.add_argument("--profit-price", help=argparse.SUPPRESS)
 a.add_argument("--profit-quantity", help=argparse.SUPPRESS)
 a.add_argument("--stop-loss-price", help=argparse.SUPPRESS)
 a.add_argument("--stop-loss-quantity", help=argparse.SUPPRESS)
 a.add_argument("--market", choices=["hk", "us"],
      help="recommended: resolves product_type in one step; hk=5 (Hong Kong stocks) us=6 (US stocks); mutually exclusive with --product-type")
 a.add_argument("--product-type", type=int, choices=[5, 6],
      help="advanced usage (mutually exclusive with --market); 5=Hong Kong stocks 6=US stocks, and it must match the market of the original order")
 a.add_argument("--apply-account-id")
 a.add_argument(
  "--intent",
  required=True,
  help=(
   'Required. English intent: the order id, market, and the fields being changed. Printed into the NEED_CONFIRMATION prompt.'
  ),
 )
 a.add_argument("--confirm", action="store_true",
      help="required: add this flag only after the user has explicitly confirmed the modification intent; otherwise NEED_CONFIRMATION blocks it")
 a.add_argument("--confirm-token",
      help="second-confirmation token: trigger NEED_CONFIRMATION once, copy the token from the returned message, then submit it together with --confirm")
 b = a.parse_args()
 ensure_user_confirmed(
  b.confirm,
  action="Modify order",
  intent_summary=b.intent,
  confirm_token=b.confirm_token,
 )
 c, c, b.product_type = resolve_market_args(
  b.market, None, None, b.product_type,
  require_currency=False,
 )
 validate_order_modify_args(b)
 d = build_client()
 def e(sub_account_id):
  return d.trade.order_modify(
   sub_account_id=sub_account_id,
   order_id=b.order_id,
   modify_type=b.modify_type,
   client_id=b.client_id,
   quantity=b.quantity,
   price=b.price,
   trig_price=b.trig_price,
   tail_type=b.tail_type,
   tail_amount=b.tail_amount,
   tail_pct=b.tail_pct,
   spread=b.spread,
   profit_trig_price=b.profit_price,
   profit_quantity=b.profit_quantity,
   stop_loss_trig_price=b.stop_loss_price,
   stop_loss_quantity=b.stop_loss_quantity,
   product_type=b.product_type,
   apply_account_id=b.apply_account_id,
  )
 f = call_with_account_retry(d, e, b.sub_account_id)
 g = ensure_order_modify_effective(f)
 dump_with_directive(
  {"intent": b.intent, **g, "result": f},
  next_action=(
   'The change was sent. Report the order id and the status words in English, then stop.'
  ),
 )
if __name__ == "__main__":
 run(main)
