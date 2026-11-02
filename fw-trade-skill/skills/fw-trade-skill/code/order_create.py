import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from _client import (
 build_client,
 call_with_account_retry,
 dump_with_directive,
 ensure_hk_order_time_window,
 ensure_order_create_effective,
 ensure_supported_order_type,
 ensure_us_night_session_order_supported,
 ensure_user_confirmed,
 normalize_trade_stock_code,
 resolve_market_args,
 run,
 StructuredScriptError,
)
ORDER_TYPE_LABELS = {
 3: "limit order",
 9: "market order",
}
_US_MARKET_TZ = ZoneInfo("America/New_York")
_US_PRE_START = 4 * 60
_US_REGULAR_START = 9 * 60 + 30
_US_REGULAR_END = 16 * 60
_US_AFTER_END = 20 * 60
UNSUPPORTED_ORDER_FIELD_NAMES = {
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
EPILOG = 'When to call: the user says buy, sell, or place an order and the market is already chosen. --market hk (HKD, product type 5) or --market us (USD, product type 6). Do not mix --market with the explicit trio. Only order type 3 (limit) and 9 (market). US extended hours (timeInForce=2) and overnight (timeInForce=4) are limit only. No conditional, stop, auction, or grey-market orders. Hong Kong board lot is 100. Hong Kong and US stocks only. Pass --intent and --confirm only after the user explicitly agrees; otherwise NEED_CONFIRMATION.'
def _raise_missing_for_order_type(args, missing):
 a = ORDER_TYPE_LABELS.get(args.order_type, f"orderType={args.order_type}")
 b = ", ".join(f"`--{field}`" for field in missing)
 raise StructuredScriptError(
  f"{a} missing required fields: {b}",
  error_code="INVALID_PARAM",
  hint=(
   "A limit order must carry a price; the script blocks it locally so an incomplete order request never reaches the gateway."
  ),
  next_action=(
   f"Fill in {b} and then restate the full order intent; only after the user agrees explicitly may you run it with `--confirm`."
  ),
  exit_code=2,
 )
def validate_order_create_args(args):
 ensure_supported_order_type(args.order_type)
 a = [
  e
  for d, e in UNSUPPORTED_ORDER_FIELD_NAMES.items()
  if getattr(args, d) not in (None, "")
 ]
 if a:
  b = ", ".join(f"`{field}`" for field in a)
  raise StructuredScriptError(
   f"Limit and market orders do not support these conditional fields: {b}",
   error_code="INVALID_PARAM",
   hint=(
    "Only limit orders (3) and market orders (9) are available; conditional triggers, "
    "trailing stops, and take-profit/stop-loss fields are not supported."
   ),
   next_action="Drop those fields. If they want a conditional, stop, or bracket order, tell them this entry does not support it.",
   exit_code=2,
  )
 c = []
 if args.order_type == 3 and not args.price:
  c.append("price")
 if c:
  _raise_missing_for_order_type(args, c)
 if args.order_type == 9 and args.price:
  raise StructuredScriptError(
   "A market order (orderType=9) must not receive `--price`.",
   error_code="INVALID_PARAM",
   hint="A market order is expressed by orderType=9 and needs no price; carrying a price easily makes the user intent and the request body disagree.",
   next_action="Drop `--price`. Restate the market order in English and confirm again before you send it.",
   exit_code=2,
  )
def _resolve_us_session():
 a = datetime.now(_US_MARKET_TZ)
 b = a.hour * 60 + a.minute
 if _US_PRE_START <= b < _US_REGULAR_START:
  return "pre-market", 2
 if _US_REGULAR_START <= b < _US_REGULAR_END:
  return "regular session", 0
 if _US_REGULAR_END <= b < _US_AFTER_END:
  return "after-hours", 2
 return "night session", 4
def apply_us_time_in_force_policy(args):
 if (args.market_code or "").strip().lower() != "us":
  return
 a, b = _resolve_us_session()
 if args.time_in_force is None:
  args.time_in_force = b
 if args.time_in_force in (2, 4) and args.order_type == 9:
  raise StructuredScriptError(
   f"US stocks{a} does not support market orders (orderType=9).",
   error_code="INVALID_PARAM",
   hint=(
    f"The current ET session is {a}, and the script automatically uses timeInForce={args.time_in_force}; this session "
    "only supports limit orders."
   ),
   next_action="Retry as a limit order (orderType 3 with --price), or wait for the session and send a market order.",
   exit_code=2,
  )
def main():
 a = argparse.ArgumentParser(
  description="Submit an order",
  epilog=EPILOG,
  formatter_class=argparse.RawDescriptionHelpFormatter,
 )
 a.add_argument("--sub-account-id")
 a.add_argument(
  "--stock-code", "--code", "--symbol", "--symbols",
  required=True,
  help=(
   'Bare security code. Preferred: 00700 for Hong Kong, AAPL for the US. Do not send hk00700 on an order. A prefixed value is stripped only as a fallback, and a prefix that disagrees with --market is rejected.'
  ),
 )
 a.add_argument("--direction", type=int, required=True, choices=[1, 2], help="1=buy 2=sell")
 a.add_argument(
  "--order-type",
  type=int,
  required=True,
  help=(
   "order type: 3=limit order, 9=market order; "
   "market is 9, not 4."
  ),
 )
 a.add_argument("--quantity", required=True)
 a.add_argument("--market", choices=["hk", "us"],
      help="recommended: expands the market trio in one step; hk=Hong Kong stocks (HKD/5) us=US stocks (USD/6); mutually exclusive with --market-code/--currency/--product-type")
 a.add_argument("--market-code", choices=["hk", "us"],
      help="advanced usage (mutually exclusive with --market); hk=Hong Kong stocks us=US stocks")
 a.add_argument("--currency", choices=["HKD", "USD"],
      help="advanced usage (mutually exclusive with --market); pass HKD for Hong Kong stocks and USD for US stocks")
 a.add_argument("--product-type", type=int, choices=[5, 6],
      help="advanced usage (mutually exclusive with --market); 5=Hong Kong stocks 6=US stocks, and it must be aligned with --market-code")
 a.add_argument(
  "--price",
  help=(
   "order price: required for a limit order (orderType=3); not passed for a market order (orderType=9)."
  ),
 )
 a.add_argument("--client-id", type=int)
 a.add_argument(
  "--time-in-force",
  type=int,
  help="time in force (timeInForce): 0=day only 2=allow the US pre-market and after-hours 4=allow the night session; when omitted for US stocks it is filled in from the ET session (pre-market/after-hours=2, night session=4, otherwise 0)",
 )
 a.add_argument(
  "--exp-type",
  type=int,
  help="order expiry expType: the common value 1 means day only (see the OrderCreate request-body documentation for details)",
 )
 a.add_argument("--short-sell-type")
 a.add_argument("--trig-price", help=argparse.SUPPRESS)
 a.add_argument("--tail-type", type=int, help=argparse.SUPPRESS)
 a.add_argument("--tail-amount", help=argparse.SUPPRESS)
 a.add_argument("--tail-pct", help=argparse.SUPPRESS)
 a.add_argument("--spread", help=argparse.SUPPRESS)
 a.add_argument("--profit-price", help=argparse.SUPPRESS)
 a.add_argument("--profit-quantity", help=argparse.SUPPRESS)
 a.add_argument("--stop-loss-price", help=argparse.SUPPRESS)
 a.add_argument("--stop-loss-quantity", help=argparse.SUPPRESS)
 a.add_argument("--apply-account-id")
 a.add_argument(
  "--intent",
  required=True,
  help=(
   'Required. English intent: buy or sell, market, security, quantity, price (say when a market order has no price), and order type. Example: Buy 100 shares of Tencent (00700) in Hong Kong at HKD 270, limit order. Printed into the NEED_CONFIRMATION prompt.'
  ),
 )
 a.add_argument("--confirm", action="store_true",
      help="required: add this flag only after the user has explicitly confirmed the order intent; otherwise NEED_CONFIRMATION blocks it")
 a.add_argument("--confirm-token",
      help="second-confirmation token: trigger NEED_CONFIRMATION once, copy the token from the returned message, then submit it together with --confirm")
 b = a.parse_args()
 b.market_code, b.currency, b.product_type = resolve_market_args(
  b.market, b.market_code, b.currency, b.product_type,
  require_currency=True,
 )
 b.stock_code = normalize_trade_stock_code(b.stock_code, b.market_code)
 validate_order_create_args(b)
 apply_us_time_in_force_policy(b)
 ensure_hk_order_time_window(b.market_code)
 ensure_us_night_session_order_supported(
  b.market_code,
  b.order_type,
  b.time_in_force,
 )
 ensure_user_confirmed(
  b.confirm,
  action="Place an order",
  intent_summary=b.intent,
  confirm_token=b.confirm_token,
 )
 c = build_client()
 def d(sub_account_id):
  return c.trade.create_order(
   sub_account_id=sub_account_id,
   stock_code=b.stock_code,
   direction=b.direction,
   order_type=b.order_type,
   quantity=b.quantity,
   price=b.price,
   market_code=b.market_code,
   currency=b.currency,
   client_id=b.client_id,
   time_in_force=b.time_in_force,
   exp_type=b.exp_type,
   short_sell_type=b.short_sell_type,
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
 e = call_with_account_retry(c, d, b.sub_account_id)
 f = ensure_order_create_effective(e)
 dump_with_directive(
  {"intent": b.intent, "orderId": f, "result": e},
  next_action=(
   'The order was sent. Report the order id and the status words in English, then stop. Do not place another order.'
  ),
 )
if __name__ == "__main__":
 run(main)
