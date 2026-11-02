# Report rules

This phase also names `scripts/payload.schema.json`. That file is the shape. Do not open another file.

## Rules

- **The source text is yours to read, and the payload is yours to write.** `data/<code>/<code>.json` must be written by you from `<code>_raw.md`, in full, following the schema this phase names. Leave a slot empty when the source is silent. Write every sentence in English. Copy every numeric value verbatim (2.3 stays 2.3). Never rescale, never compute, never grab a stray number out of the prose. The five-factor scores and the overall stars each live in exactly one slot. A missing payload stops `render` at exit 2. A payload that does not match the schema stops at 7. Do not hand-write `<code>_report.html`. `render` is the only path to it.
- **One network exit:** host `WebSearch` / `WebFetch`. Use them only when all four layers left an issue-date slot empty, and only to fill `issue_params` dates. Do not search the list, the prospectus, or a replacement data source.
- **`hooks/pretool.py` blocks by capability:** other network tools are rejected. Writes to this package's source are rejected (`data/<code>/*.json` outputs are allowed). `curl` / `wget` are rejected.
- Do not `ls`, `env`, probe `127.0.0.1`, or look for a second entry.
- **`report` runs to completion.** Bash `timeout` must be `1800000`. A silent stall retries with `retry`, at most 4 attempts. A deterministic failure stops immediately. Do not kill it halfway.

## Source priority

Truth is `scripts/ipo_sources.py`. One merge rule: `payload_merge.merge_prefer` (a filled value wins; empty does not overwrite).

| Layer | Who | Tool | Supplies | If missing |
| --- | --- | --- | --- | --- |
| 1 | our MCP | `ipo_list`, `market_snapshot` | List rows, official name, currency | Continue empty. Do not overwrite the source text |
| 2 | our MCP | `ipo_dify_report` | Full note. Every semantic payload slot is written by the agent that reads it. The script stores the text and never parses it | Leave that slot empty |
| 3 | our MCP | `deep_profile`, `news_catalysts` | Text only, and only slots still empty after layers 1 and 2. Do not overwrite numbers | Leave the slot empty. Still render |
| 4 | host CLI | `westock-data ipo --market hk --raw` | Only empty `issue_params` dates | Leave the slot empty |
| 4b | host tools | `WebSearch` / `WebFetch` | One still-empty date | Leave the slot empty |

Layers 1 and 3 spend the same key quota. Layer 3 calls only when a slot is empty. Layer 4 never overwrites the source text. Do not take `westock-data` `price` / `hy`. Source-text dates win. Switches: `IPO_MCP_PRIMARY=0`, `IPO_MCP_SUPPLEMENT=0`, `IPO_HOST_SOURCES=0`. All default on.

## Flow

Inside `report` the order is layer 1 → 2 → 3 → 4. One report is on the order of 10 minutes. `report` may wait 1800 seconds. If the source text is already local, do not pass `--refresh`.

When `report` writes a source whose content differs and `<code>.json` exists, the old payload moves to `<code>.json.stale` and stdout `next_action` asks you to rewrite it.

## Outputs

Three files under `IPO_DATA_DIR` (default `data/<code>/`): `<code>_raw.md`, `<code>.json`, `<code>_report.html`.

The report is one HTML file: 11 `section.card` blocks, a hero, `nav.toc`, two allotment tables, and at most 4 echarts charts (one five-factor radar, plus one line chart each for subscription, sponsor, and fundamentals). echarts is inlined. Swap data only. Do not change structure. Module 10 (hot Q&A) is not extracted and not rendered. A series with fewer than 2 points drops the whole chart.

Follow stdout `next_action` from `report`: write the payload, then `render`. If `next_action` says the narrative is still Chinese, rewrite those sentences in `<code>.json` into English (keep the official issuer name, the `hk` code, and the numbers), then `render` again.

## Delivery

Deliver only the `{symbol}_report.html` the script printed. Do not copy it outside the package. One path. In the chat, name that one path.

## Exit codes for the report

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 2 | Usage (`next_action` says what is missing) |
| 6 | Data-plane failure: relay `failures[].error` as-is. Do not switch to web search |

Gate codes 3, 4, and 5 stop on the signup guide or one sentence. They are not a reason to search the web.
