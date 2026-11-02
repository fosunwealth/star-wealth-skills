---
name: moni-trade
description: Star Wealth paper-trading OpenAPI skill for Hong Kong and US equities. Reuses fosun.env via FOSUN_ENV_PATH, or the setup script own default path under the home directory when unset. Paper endpoints only. Does not create or repair credentials.
version: 1.8.0
requires:
  bins:
    - bash
    - curl
install: install.sh
---

# Paper trading

Language: chat replies follow the user's language. Do not print key material.

Working directory is the parent skill root (the folder that contains `SKILL.md` and `code/`). Every command is `FW_TRADE_MODE=paper python code/<script>.py`. If `FW_TRADE_MODE` is missing, the script stops before any call. Do not run files under this directory: the entry points live in `code/`.

Status words: 10 not sent, 20 waiting to send, 22 pending, 23 pending review, 40 working, 50 filled, 60 partially filled, 70 cancelled, 80 partially cancelled, 90 rejected, 100 expired. Unknown code: "unknown status X". `code=0` is "the request succeeded (code=0)". A non-zero `code` includes `message` and a plain-English reason. When both an order id and a status are present, report the order id, the result, the status words, and whether another confirmation is needed.

This file holds the decision. Flag details are `<script>.py --help`. Do not invent a flag.

## Scripts

| Script | Role |
|---|---|
| `account_list.py` | List accounts. Report and stop. Do not run it before every query |
| `sync_accounts.py` | Force-refresh the index only after the user says an account changed |
| `check_shared_env.py` | Credential health check. Not a preface to every call |
| `sim_account_create.py` | Create a paper account. `--confirm` after they agree. Starts with 1,000,000 HKD and 1,000,000 USD |
| `sim_account_reset.py` | Reset one paper account. They must name the old id. 7-day gap. `--confirm`. The old account is disabled |
| `cash_summary.py` | Cash and buying power. HKD for Hong Kong, USD for the US. No FX |
| `holdings.py` | Positions |
| `cash_flows.py` | Cash movements |
| `order_create.py` | Place an order. `--direction 1` buy, `2` sell |
| `order_modify.py` | Change an order |
| `order_cancel.py` | Cancel an order |
| `order_list.py` | List orders. No lookup by a single order id |
| `market_quote.py` / `market_orderbook.py` / `market_kline.py` / `market_min.py` / `market_tick.py` / `market_broker_list.py` | One-shot quotes |

Call only the names in this table.

## Rules

One user request, one script, then wait. Queries do not place, change, or cancel. An account error already retries inside `code/_client.py`. Do not chain `account_list` yourself. Read stdout `next_action` before the next step. Do not show it as raw JSON unless the user asked.

If `subAccountId`, `direction`, `quantity`, or `price` is unknown, ask. Do not fill a default. Use `--market hk|us` (hk = HKD / product type 5, us = USD / product type 6). Do not mix `--market` with `--market-code` / `--currency` / `--product-type`.

Symbol flags are `--code`, `--stock-code`, `--symbol`, and `--symbols`. Anything else is `INVALID_PARAM`. Prefer `--args-json` (single quotes outside, double quotes inside). Query values may be `01810`, `700`, `AAPL`, or `HK.01810`; the script normalizes them. Orders use the bare code: `--market hk --stock-code 00700`, `--market us --stock-code AAPL`. A prefix that disagrees with `--market` is rejected. Hong Kong board lot is 100.

Hong Kong and US ordinary shares only. No A-shares, no options, no `BidAskInfo`, no subscriptions, no parked or conditional orders. Order type `3` is limit, `9` is market (not `4`). `timeInForce`: `0` day, `2` US extended hours, `4` overnight. Extended and overnight hours are limit only. Prices with `power` are raw / (10^power).

A change (order, paper-account create, paper-account reset) restates the full intent in English and waits for an explicit yes, even when they already gave every field. Then pass `--intent` and `--confirm`. Missing `--intent` is `INVALID_PARAM`. Missing `--confirm` is `NEED_CONFIRMATION`. "Sure", "I guess", and "you decide" are not a yes. On `NO_MOCK_ACCOUNT` (exit 3), stop. Do not switch to live or pick another account.

## Commands

```bash
FW_TRADE_MODE=paper python code/cash_summary.py --args-json '{}'
FW_TRADE_MODE=paper python code/holdings.py --args-json '{}'
FW_TRADE_MODE=paper python code/order_list.py --args-json '{"active-only":true}'
FW_TRADE_MODE=paper python code/market_quote.py --args-json '{"code":["<CODE>"]}'
FW_TRADE_MODE=paper python code/order_create.py --market hk --stock-code 00700 --direction 1 --order-type 3 --quantity 100 --price 100.000 --intent "Buy 100 shares of Tencent (00700) in Hong Kong at HKD 100, limit order." --confirm
FW_TRADE_MODE=paper python code/order_create.py --market us --stock-code AAPL --direction 1 --order-type 9 --quantity 1 --intent "Buy 1 share of AAPL at market." --confirm
FW_TRADE_MODE=paper python code/order_modify.py --market hk --order-id <OID> --modify-type 1 --price <PRICE> --intent "<English intent>" --confirm
FW_TRADE_MODE=paper python code/order_cancel.py --market hk --order-id <OID> --intent "<English intent>" --confirm
```

`--modify-type` is only `1` (quantity and/or price). Unknown order id: `order_list.py` first. `order_list.py` fills the last 7 days when dates are omitted and defaults to `--count 20`. `APIERROR_50001`: retry once with `--count 50`.

## Errors

stderr is JSON. Read `error_code` and `next_action`. Exit 0 success, 1 APIError, 2 bad args or not confirmed, 3 no paper account.

| Code | You do |
|---|---|
| `NO_MOCK_ACCOUNT` | Stop. No paper account. Do not switch to live |
| `ENV_FILE_MISSING` / `ENV_INCOMPLETE` | `fosun-env-setup` |
| `SESSION_EXPIRED` | `check_shared_env.py`, then `fosun-env-setup`. Not "order not found" |
| `INVALID_SIGNATURE` | `fosun-env-setup`, then retry. Not "order not found" |
| `APIERROR_40010` | Stop. Renewal is on the live side (scan). Same API key. No paste |
| `APIERROR_40001` / `APIERROR_40015` | Stop. Reset on the live side. Already signed up: Forgot API parameters, then API key and server public key PEM together |
| `APIERROR_40005` / `APIERROR_40008` | Stop. Contact Star Wealth support. Do not mint a ticket |
| `NEED_CONFIRMATION` | Repeat `intent_summary`. Ask "Send this?". `--confirm` only after a clear yes |
| `SILENT_FAIL_EMPTY_DATA` | Stop. Ask them to confirm `hk00700` / `usAAPL`. Do not invent a price |
| `APIERROR_50001` | Retry once with `--count 50` |
| `APIERROR_60006` | Relay the server check. Do not guess a fix |
| `APIERROR_60009` | Over the paper limit. Suggest a smaller quantity |
| `APIERROR_60014` | Relay the risk block and wait |
| Other `APIERROR_*` | Follow `hint` / `next_action` |

Account id order: `--sub-account-id`, then `MONI_SUB_ACCOUNT_ID`, then `FSOPENAPI_ACCOUNT_INDEX`, then the account list. An account error refreshes the cache once.
