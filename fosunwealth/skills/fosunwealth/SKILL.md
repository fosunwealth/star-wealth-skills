---
name: fosunwealth
description: Query Hong Kong, US, and China A-share stock codes, real-time quotes, K-lines, ETFs, IPO calendars, and financial reports through the Fosun Wealth connector, or hand a whole request to the Star AI assistant.
---

# FosunWealth AI

Two ways in, and they are not interchangeable.

- **`ask_star_ai` — one request, whole service.** Star AI runs its own tools, so this reaches everything the app does: quotes, K-lines, ETFs, IPOs, financial statements, deep research reports, the signed-in user's holdings, and the trading flows its own confirmation rules guard. Use it for opinions, multi-step work, reports, and anything about the user's own positions or account.
- **The ten read-only tools** — single, cheap lookups. Use one when the user asks for one thing: a code, a quote, some bars, one statement.

Prefer one of the ten when it answers the question. Reach for `ask_star_ai` otherwise.

## Authentication

- On first use, the host prompts the user to sign in with their Fosun Wealth account through OAuth 2.1 with PKCE in the browser, and stores the token on the host's connector backend. The tools are called with that token; the model never sees it.
- Never ask the user to paste an API key, a password, or an SMS verification code into the chat.
- If a tool call fails with an authentication error (401), ask the user to re-authorize the Fosun Wealth plugin: **Customize** in Cursor, **Connect apps** in Grok Bot.

## Using `ask_star_ai`

1. **Pass the request through, don't rewrite it.** Write the user's own words into `question`, plus the context Star AI cannot see from the host (the ticker they were just discussing, the period they asked about). Do not answer the question yourself and do not split it into several calls.
2. **One call per request.** It can take a while — Star AI may run several tools. Wait for the answer instead of calling it twice.
3. **Continue with `thread_id`.** The answer ends with `thread_id: …`. Pass that value as `thread_id` on the next call when the user keeps talking about the same thing; leave it empty for a new topic.
4. **The answer is text.** Star AI's web app renders cards and interactive charts; here you only get the text, so summarise or reformat it for the user rather than claiming a chart exists.
5. **Do not invent anything it did not say.** If the answer says a source was unavailable, or that it produced only part of an answer, pass that along.

## Using the read-only tools

1. **Discover tools from `tools/list`**: read each tool's parameter schema (`inputSchema`) before calling it. The server owns the catalogue, so calls stay valid as it adds or changes tools.
2. **Resolve the code first**: when the user gives a company name, or a ticker without a market suffix (`.HK`, `.US`, `.SH`, `.SZ`), search the code first and confirm the exact `<ticker>.<market>` identifier before querying quotes, K-lines, or statements.
3. **Ground every figure in tool output**: report prices, percentages, dates, currencies, and financial metrics strictly as returned. If a query returns nothing or the upstream source is down, say so plainly and never invent a number.

## Boundaries

- The ten read-only tools place no orders and change nothing. `ask_star_ai` can reach the trading flows, but those sit behind Star AI's own confirmation steps: never claim an order was placed unless the returned answer says so.
- For account changes, fund transfers, and anything the connector cannot do, point the user to the Fosun Wealth app.
- On analytical answers, add one line that market data and research summaries are for reference only and are not investment advice.
