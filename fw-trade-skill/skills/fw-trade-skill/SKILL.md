---
name: fw-trade-skill
description: "Stop bouncing between a dozen apps just to get one trade done — just say “buy 100 shares of Tencent for me”, and the Star Wealth (Fosun Wealth) AI HK/US Intelligent Trading Skill runs the whole flow in one pass: pre-trade check, order placement, and live monitoring. It covers the full order lifecycle — market and limit orders, changes, cancels, and status — for Hong Kong and US names, with clear intent confirmation before anything is sent. You stay in control the whole way. Open the Star Wealth app for a free API key and put it to work."
license: Apache-2.0
allowed-tools: Bash Read
metadata:
  author: "Star Wealth"
  version: "2.0.5"
  homepage: "https://fintrustskill.com/landing"
  category: "finance"
  emoji: "💹"
compatibility: "Requires python3 on PATH, plus network access to the Star Wealth research gateway."
---

## First-time setup and Step 0

Gateway: `https://openapi.fosunxcz.com`. Credential: one `fosun.env` file, written by the setup script. The path is `FOSUN_ENV_PATH`; when that variable is unset the script uses its own default under the home directory (`star-wealth-openapi/fosun.env`). Keep that file outside this repository and never paste its contents into the chat. Until `status` is `valid`, show nothing else.

```bash
bash "<this skill root>/install.sh"
python3 fosun-env-setup/code/ensure_fosun_env.py
```

Prefer `$FOSUN_PY` after `install.sh`, otherwise `python3`. `valid` continues. `pending` / `error` shows `operation_guide` / `user_message` / `next_action` as-is, then stops. Never print key material.

**The rest of this file is read only after `status=valid`.** Chat follows the user's language. Every order, change, and cancel needs an explicit yes. Not investment advice.

## Prep

Working directory = this `SKILL.md` directory. Python 3.9+ on the machine that runs `install.sh`. Run `install.sh` once when the SDK is missing.

`install.sh` needs `uv`, the Python environment manager. If `uv` is already on `PATH` it is reused. If not, the script downloads the pinned installer from `astral.sh`, checks it against a SHA-256 recorded inside the script, and only then runs it — a mismatched download stops the install. `uv` then creates a virtual environment pinned to Python 3.13, so the machine's own `python3` only has to be 3.9 or newer.

## Step 1 — start

**next_action is the only queue.** `python3 scripts/progress.py --query "<latest user question>"`. Do not show that JSON. Open a subskill only when `next_action` names it. Phases: `need_activation→need_start→need_choose_route→need_read_route→need_act→done`. A question that already names paper, live, or setup skips `need_choose_route`. Marks: `--mark-route` / `--mark-done`.

## Step 2 — read

Read only the one subskill `next_action` names.

## Step 3 — act

If they did not say paper or live, ask once. "Buy" is not that choice. The first live order shows a risk notice and waits for an explicit yes. Confirm side, name, quantity, and order type. The default type is limit. Do not print keys, tokens, or PEM. Before any order, change, or cancel, show account, side, name, quantity, type, estimated amount, and risk. Send only after yes, confirm, or place it.

## Step 4 — deliver

Deliver one or two sentences, then `--mark-done`.

## Exit codes (internal)

Exit 0 continues. Exit 2 means the session or route is missing, or the Star Wealth OpenAPI credential is not `valid`.

## External hosts, and what happens when one is unreachable

| Host | Role | Unreachable |
| --- | --- | --- |
| `openapi.fosunxcz.com` | The only order and market gateway | **Core.** No gateway means no order, change, cancel, account, or quote. Stop with one plain sentence |
| the Star Wealth signup page (the URL is in the ticket the setup script prints) | First-time signup and credential renewal | **Core for setup only.** An already valid `fosun.env` keeps working |
| `openapi-docs.fosunxcz.com`, then `github.com` | `install.sh` downloads the SDK: vendor site first, GitHub archive as fallback | **Required for install only.** Both failing fails the install; an installed skill keeps running |
| `astral.sh` | `install.sh` installs `uv` when it is missing, which then creates the pinned Python 3.13 environment | **Required for install only.** If it is unreachable the install stops and says so; an installed skill keeps running |
| `pypi.org` | `install.sh` installs the SDK dependencies. No mirror | **Required for install only.** If it is unreachable the install stops and says so |
