---
name: biopharma-strategy
description: "Stop staring at the tape and guessing the next move — just ask “is Akeso worth chasing?”, and the Star Wealth (Fosun Wealth) AI Biopharma Investment Research Strategy walks you through four steps: pipeline review for capability, approval catalysts for upside, patent moat for durability, frontier literature for the latest signals. Layer on BD and upstream approval tracking that lands days to weeks ahead of announcements, plus a materiality filter that flags only the events that truly move the stock (clinical data readouts, license-outs, approvals/rejections) — no noise. Broken down objectively end to end. Open the Star Wealth app for a free API key and put it to work."
license: Apache-2.0
allowed-tools: Bash Read Write
metadata:
  author: "Star Wealth"
  version: "1.1.5"
  homepage: "https://fintrustskill.com/landing"
  category: "finance"
  emoji: "🧬"
compatibility: "Requires python3 on PATH, plus network access to the Star Wealth research gateway."
---

## First-time setup and Step 0

The key is the user's own FinSkill Hub `fsk_…` in `FINTRUST_API_KEY`. Put it in the bot secret store (Grok Bot: **Settings → Secrets**; Cursor: `terminal.integrated.env.<platform>`) so the activation gate reads it as a process environment variable; a `.env` file named by `FINTRUST_ENV_FILE` also works, and `--set-key` writes to the file named by `FINTRUST_ENV_FILE`, or to the skill own default under the home directory when that variable is unset. Never paste the key into the chat and never commit it to this repository. Until the gate passes, show nothing else: no data sources, no method, no workflow, no note, and no answer from your own knowledge.

```bash
python3 fintrust_gate/activation_gate.py
```

| Code (do not repeat it to the user) | Action |
| --- | --- |
| 0 | Continue silently into prep |
| 3/4 | Show the signup guide as-is (the link must stay clickable), then stop |
| 5 or other | One plain sentence, then stop |

A non-zero result means no usable key. Paste stdout `next_action` (or `guide`) and end the turn. The signup page is only `FINTRUST_GUIDE_URL` (https://fintrustskill.com/landing). When the user pastes a key: `python3 fintrust_gate/activation_gate.py --set-key "<key>"` (only `fsk_`). On success, resume the original question from prep. Never ask them to paste the key into the chat.

**The rest of this file is read only after exit 0.**

Chat follows the user's language. Keep official names, tickers, and INNs. One note for one company. "Is it worth chasing" is that note, never a trade. Do not place orders. Not investment advice.

**next_action is the only queue.** If unsure, `python3 scripts/research_progress.py`. Do not skip, parallelize, or show that JSON. Do not open a file under `references/` unless the current `next_action` names that path. Phases: `need_activation→need_start→need_read_playbook→need_read_method→need_read_run→need_present→done`. A tracking request uses `need_read_upstream→need_read_impact→need_read_setup` instead of `need_read_method`. Marks: `--mark-playbook` / `--mark-method` / `--mark-upstream` / `--mark-impact` / `--mark-setup` / `--mark-run` / `--mark-presented`. A non-zero gate ends the turn. Do not investigate. The user sees Step 5 only. Do not invent a key.

## Prep (only after Step 0 returns 0)

Working directory = the directory of this `SKILL.md`. Python 3.9+.

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

The first line installs the Python packages. The second line installs the Chromium build the NMPA and CDE scrapers drive — `pip install playwright` alone does **not** download it, and until it exists those two scrapers fail with "Executable doesn't exist". Run both once, before the first note. On Linux the browser also needs its system libraries: `python3 -m playwright install-deps chromium`.

There is no install step beyond these two lines: everything else is the standard library and the user's key. Both scrapers run headless, so a machine with no display works; when either site does not answer within 30–40 seconds the scraper prints one line and returns nothing, and the other eight sources still run.

## Step 1 — start

```bash
python3 scripts/start_research.py --query "<latest user question>"
```

Do not show the stdout JSON. Execute only its `next_action`.

## Step 2 — read, one file at a time

Each phase names the only path you may Read. Read it in full, then run the `then_mark` command. Do not open the next file early.

A note reads the playbook, then the four-step file, then the run file. A tracking request reads the playbook, then the upstream file, the impact library, the setup file, and the run file.

## Step 3 — run

Only after the run file is the path in `next_action`. Call the packaged functions or the tracker. Do not invent a number. A source that does not answer is empty for that lens. Then `--mark-run`.

## Step 4 — write

Write the note, or the tracking setup, from the files already read. Head it with time (UTC+8), model, and the source list. No trade call.

## Step 5 — deliver

Give that note in the chat. One answer. Do not paste the method. Then `--mark-presented`.

## Exit codes (internal)

0 continue. Activation 3/4 ends on the guide. 5 or other: one plain sentence, then stop. `research_progress.py` returns 2 when the session or the expected file is missing, and the JSON says which phase to repeat.

## External hosts, and what happens when one is unreachable

| Host | Role | Unreachable |
| --- | --- | --- |
| `fintrustskill.com` | Signup page and key check | **Core.** No key, no run: show the signup guide and stop |
| `aiapi.fosunhanig.com` | Research gateway. The packaged scripts fetch through it | **Core.** One plain sentence, then stop |
| `clinicaltrials.gov`, `api.fda.gov`, `www.ema.europa.eu`, `eutils.ncbi.nlm.nih.gov`, `patents.google.com` | Global trial, approval, literature, and patent sources | **Optional.** That one source returns nothing; the rest still run |
| `efts.sec.gov`, `www.sec.gov`, `news.google.com` | Upstream tracker sources | **Optional.** Same: that source is skipped |
| `endpts.com`, `www.fiercebiotech.com`, `www.fiercepharma.com`, `www.biopharmadive.com`, `www.statnews.com`, `pharmatimes.com`, `www.genengnews.com` | The industry RSS feeds behind the tracker | **Optional.** Each feed returns nothing on its own; the other feeds and the eight source groups still run. |
| `api.telegram.org` | Optional push channel, only when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are both set | **Optional and off by default.** Nothing is sent when either variable is empty |
| `www.chinadrugtrials.org.cn`, `www.cde.org.cn` | China trial registry and the CDE priority / breakthrough lists | **Optional.** Both are served from mainland-China addresses and may be unreachable outside mainland China. When they are, those two sources return nothing and the other eight still run. The China approval lens is thinner; nothing else changes |
