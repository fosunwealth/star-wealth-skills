---
name: real-trade
description: Star Wealth live OpenAPI skill for Hong Kong and US equities. Reuses the shared fosun.env via FOSUN_ENV_PATH. When unset, the runtime resolves the setup script own default path under the home directory. Accounts, balances, quotes, orders, and trades after the user has chosen the live account.
version: 1.8.0
requires:
  bins:
    - bash
    - curl
install: install.sh
---

# Live trading

Language: chat replies follow the user's language. Do not print key material.

Same scripts, same flags, and same error codes as `moni-trade-skill/subSKILL.md`, with three differences: the mode is live, there is no paper-account create/reset, and a missing live stock account is `NO_REAL_STOCK_ACCOUNT` (do not fall back to paper).

Working directory is the parent skill root. Every command is `FW_TRADE_MODE=live python code/<script>.py`. A missing mode stops the script before any call.

Do not call this skill until they have chosen live. One shared `fosun.env` (`FOSUN_ENV_PATH`, or the setup script own default path). Do not copy a second credential file.

Before the first live call:

```bash
python fosun-env-setup/code/ensure_fosun_env.py
```

`status=valid`: continue. `status=pending`: give `exact_open_url` character for character, then retry after they finish. `status=error`: stop and repair before any live call. Repair with `--repair` when a credential exists but is damaged.

A live order, change, or cancel restates market, name, side, quantity, price or order id, and order type, then waits for an explicit yes. "Sure", "I guess", and "you decide" are not a yes. Only then add `--intent` and `--confirm`.

Queries report and stop. One request, one script.
