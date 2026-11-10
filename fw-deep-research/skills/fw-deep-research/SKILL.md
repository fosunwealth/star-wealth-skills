---
name: fw-deep-research
description: "Stop staring at the tape and guessing the next move — just ask “is NVIDIA worth chasing?”, and the Star Wealth (Fosun Wealth) AI HK/US Equity Deep Research Skill walks you through four steps: business model for capability, valuation for the price, financials for quality, and the latest events for catalysts. It turns a pile of filings and market data into one interactive HTML research report — charts included, broken down objectively end to end, no buy or sell calls. Open the Star Wealth app for a free API key and put it to work."
license: Apache-2.0
allowed-tools: Bash Read Write WebSearch WebFetch Skill
metadata:
  author: "Star Wealth"
  version: "3.7.56"
  homepage: "https://fintrustskill.com/landing"
  category: "finance"
  emoji: "📊"
compatibility: "Requires python3, node, npm on PATH, plus network access to the Star Wealth research gateway."
---

## First-time setup and Step 0

The key is the user's own FinSkill Hub `fsk_…` in `FINTRUST_API_KEY`. Put it in the bot secret store (Grok Bot: **Settings → Secrets**; Cursor: `terminal.integrated.env.<platform>`) so the activation gate reads it as a process environment variable; a `.env` file named by `FINTRUST_ENV_FILE` also works, and `--set-key` writes to the file named by `FINTRUST_ENV_FILE`, or to the skill own default under the home directory when that variable is unset. Never paste the key into the chat and never commit it to this repository. Until the gate passes, show nothing else: no data sources, no method, no workflow, no install, no report, and no answer from your own knowledge.

```bash
python3 fintrust_gate/activation_gate.py
```

| Code (do not repeat it to the user) | Action |
| 0 | Continue silently into prep |
| 3/4 | Show the signup guide as-is (the link must stay clickable), then stop |
| 5 or other | One plain sentence, then stop |

A non-zero result means no usable key. Paste stdout `next_action` (or `guide`) and end the turn. The signup page is only `FINTRUST_GUIDE_URL` (https://fintrustskill.com/landing). When the user pastes a key: `python3 fintrust_gate/activation_gate.py --set-key "<key>"` (only `fsk_`). On success, resume the original question from prep. Never ask them to paste the key into the chat.

**The rest of this file is read only after exit 0.**

Chat follows the user's language. The HTML report stays English. A Chinese draft is rejected. Keep official names and tickers. One report for one stock. "Can I buy it" is that report, never a trade. Do not place orders. A quote with no report is not this skill.

`westock-data` / `neodata` are optional host skills. `scripts/ensure_host_skills.py` only checks them and never installs one. When the host does not provide them, the skill runs on MCP plus the host web tools and only the facets those two would fill stay thinner. MCP is Streamable HTTP at `https://aiapi.fosunhanig.com/ai-mcp-research/mcp`, not REST `/v1/session|tool|finalize`. Not investment advice.

**next_action is the only queue.** If unsure, `python3 scripts/research_progress.py`. Do not skip, parallelize, or show that JSON. Phases: `need_activation→need_start→need_read_prompts→need_phase_a→need_phase_b→need_host_packs→need_web_sources→need_write→need_dump→need_render→need_assemble→need_present→done`. Marks: `--mark-read-prompts` / `--mark-host-packs` / `--mark-web-sources` / `--mark-presented`. A non-zero gate ends the turn. Do not investigate. The user sees Step 5 only. No Markdown, SVG, `show_widget`, "AI overall score", or a second outline. Only the commands in this file. Do not hand-write chart options or invent a key.

## Prep (only after Step 0 returns 0)

Working directory = the directory of this `SKILL.md`.

```bash
python3 -m pip install -r scripts/requirements.txt
npm install                                           # needs node_modules/echarts/dist/echarts.min.js
python3 scripts/ensure_host_skills.py --allow-neodata-degraded   # read-only check of westock + neodata; do not show the JSON
```

Charts are rendered from `nl-echarts/subSKILL.md` (do not add another `SKILL.md`). `--render-all` calls `nl-echarts/render-echarts.mjs`. Do not hand-write options.

## Step 1 — start

```bash
python3 scripts/start_research.py --query "<latest user question>"
# multi-turn: --messages-file messages.json
```

Do not show the short stdout summary. **Read** `charts_dir/prompts/writer_system.md` and `playbook.md` in full, then `--mark-read-prompts`. Also present: `writer_input.md`, `capabilities.json`.

## Step 2 — data

Silent calls. Do not narrate. Do not redirect `mcp_*.json`.

MCP first (Phase A/B). Host `westock-data` / `neodata` / `WebSearch` only fill gaps the MCP did not cover.

1. **Phase A (MCP):** `run_tool.py resolve_symbol '{"query":"<short name>"}'`. Confirm only when there are multiple candidates.
2. **Phase B (MCP):** `run_phase_b.py --code '<standard code>'` (shape `usAAPL` / `hk00700` / `sh600519`). Fill MCP coverage here. On a hole, one `run_tool.py` call.
3. **Host gaps** (skip a facet the MCP already filled). Write three host packs:

| Facet | Host command | File |
| --- | --- | --- |
| Market / technicals | `kline --period day` (the latest bar is today’s tape — there is no `quote` / `minute`) · `technical` · `chip` (A-shares only) | `host_deep_profile.json` |
| Financials | `finance --type <lrb/zcfz/xjll/zhsy/income/balance/cashflow> --num N` · `disclosure` · `dividend list --years N` · `buyback` | `host_fundamentals_pack.json` |
| Flows | `fund <flow/short/margin/block/north-holding/south-holding>` · `lhb` | `host_deep_profile.json` |
| Institutions | `rating` (HK/US) · `consensus` (A/HK) · `report list\|detail` · `score` (A) · `esg` (A) | `host_institutional_views.json` (must include rating) |
| Events | `notice list\|detail` · `risk` (A) · `suspension` · `calendar` | `host_deep_profile.json` |
| Profile / holders | `profile` · `shareholder` (A/HK) | `host_deep_profile.json` |
| Industry / macro | `sector <constituent/info/ranking/oper/valuation/forecast/finance>` · `index <list/search/constituent>` · `market-overview` · `changedist` · `macro <list/indicator/expect>` · `ipo` · `trade-calendar` | Industry section |
| Natural-language gap | `neodata` | matching host pack |
| Public web | Host `WebSearch` (`query` + `freshness`; alias `web-search`) + `WebFetch` (`url`; alias `web-fetch`) | `host_web_sources.json` (≥2 openable URLs) |

`news` / `quote` / `minute` do not exist. Tape is `kline`. News is `notice` / `report` / `calendar` plus neodata and `WebSearch`. Do not web-search a facet westock or MCP already covered. Phase C prefers two sources and does not invent a number. Peers: the subject plus 3–6 names, same basis, at least 2 metrics.

```bash
python3 scripts/run_tool.py --list
python3 scripts/run_tool.py --schema <capability_name>
python3 scripts/run_tool.py <capability_name> '<json_args>'
python3 scripts/run_phase_b.py --code '<standard code>'
westock-data <command> ...
```

**neodata:** when the host provides it, run its `query.py` with `--query "<one question>"` for news, filings, industry chain, funds, overseas, and macro. A missing skill, a missing token, or any failure means skip it and use westock plus `WebSearch`; never ask the user for a token. Then `--mark-host-packs`.

**Web sources:** `WebSearch` + `WebFetch` → `host_web_sources.json` (≥2 items, url + title) → `--mark-web-sources`. Only for primary filings, IR pages, and authoritative reporting.

## Step 3 — write

Write `raw_writer.md` from `WRITER_SYSTEM`. Do not send it to the user. Structure:

```markdown
# <short name> (<ticker>) research note
## Key takeaways
### Snapshot / ### Highlights / ### Risks / ### Catalysts
## In-depth analysis
## Fundamentals   # required ### Revenue mix (pie)
## Valuation       # required ### Relative strength (daily candles)
## Industry / ## Risk signals / ## Institutional flows / ## Events and catalysts
```

Rules: write an unlocked `###` only when it has numbers. No empty shells and no “data unavailable”. One `(Source: …)` at the end of a factual paragraph. No trade advice and no tool names. Two decimal places. Large figures carry units. Do not add `## References`. Do not add an “AI overall score”.

- **Daily candles:** `### Relative strength` + `price_technical` candlestick. If missing, dump sends you back to `need_phase_b`.
- **Revenue pie:** `### Revenue mix`. Write `host_revenue_mix.json`: `{"parts":[{"name":"…","value":85.05},…]}` (≥2). If missing, `need_write`. When geography exists, also write `host_revenue_geo.json`.
- **Peers:** subject + ≥3 comparables, **≥3 metrics on the same basis**.
- **Peer radar:** `### Peer comparison` must emit `peer_radar`. After the prose, write `host_peer_radar.json`: `{"subject":"short name","indicators":[{"name":"Gross margin","higherIsBetter":true},{"name":"Net margin","higherIsBetter":true},{"name":"Debt to assets","higherIsBetter":false}],"companies":[{"name":"Subject","values":[72.4,56.5,28.9]},{"name":"Peer 1","values":[…]}]}` — ≥3 axes, ≥2 companies, company 0 is the subject, values follow indicator order, **raw numbers only** (write `72.4`, not `72.4%`). The script min-max normalizes to 0–100. Missing file → dump returns `need_write`.
- Peer metrics: `westock-data finance <subject,peer1,peer2,peer3> --num 1` returns the same columns (gross margin, net margin, ROE, debt to assets, current ratio, asset turnover).

## Step 4 — charts and HTML

No CDN, iframe, `show_widget`, or hand-written options. `### Price target` has no chart. suggested ≤5, at most one chart per `###`. Final charts = daily `price_technical` + `revenue_mix` pie (+ `revenue_geo` when data exists) + `peer_radar`. Do not render other slugs.

```bash
python3 scripts/prepare_report.py --report-file raw_writer.md --dump-payloads
python3 scripts/prepare_report.py --render-all --charts-dir <charts_dir>
HOST_WS="$PWD"
cd "<this skill root>"
FINTRUST_PRESENT_DIR="$HOST_WS" python3 scripts/prepare_report.py \
  --report-file raw_writer.md --assemble-html --charts-dir <charts_dir>
```

Assemble inlines echarts + options into one file, injects references (at most 4), and runs `finalize_report.py`. Take `present_path` from stdout. `FINTRUST_PRESENT_DIR` sets the delivery directory; it must be a writable directory outside this skill, and when the variable is unset the script picks its own session directory.

## Step 5 — deliver

1. Hand the user that one file. Attach it when the host can attach files, and always give the full absolute path in the chat. A side preview is optional.
2. Give that **full absolute path** in the chat.
3. One or two sentences. Do not paste Markdown or HTML source. Then `--mark-presented`.

## Exit codes (internal)

0 continue; 2 bad args or no session; 3 chart or structure failure → rerun dump/render; activation 3/4 ends on the guide; 5 network or key check unavailable.

## External hosts, and what happens when one is unreachable

| Host | Role | Unreachable |
| --- | --- | --- |
| `fintrustskill.com` | Signup page and key check | **Core.** No key, no run: show the signup guide and stop |
| `aiapi.fosunhanig.com` | Research gateway (every Phase A / Phase B MCP call) | **Core.** One plain sentence, then stop |
| `registry.npmjs.org` | `npm install` fetches echarts, which the report inlines | **Required for charts.** Without it prep fails and the report cannot be rendered |
| host `westock-data` and `neodata-financial-search` | Host data tools that fill the facets the MCP left empty | **Optional.** `scripts/ensure_host_skills.py` only checks them; when one is missing the report still renders from MCP data plus `WebSearch` / `WebFetch`, and only those facets are thinner |
| host `WebSearch` / `WebFetch` | Openable public sources for the last gaps | **Optional.** The report renders without them; the reference list is then shorter than four |
