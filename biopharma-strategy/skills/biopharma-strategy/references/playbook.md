# Playbook

This is the only file for this phase. Do not open another file until `research_progress.py` names that path.

The session already chose note or tracking. Follow that.

## Scope

A four-step read of a Hong Kong or US biopharma company, plus upstream tracking that keeps only material events. Data scripts live in this package under `biopharma_strategy/` and do not depend on `biopharma-data-sources`.

| | |
| --- | --- |
| Does | Pipeline, approval catalysts, patent moat, and literature. The materiality filter keeps clinical readouts, license-outs, and approvals or rejections. Objective only. No trade calls. |
| Does not | Does not turn "we heard it earlier" into a price forecast. Does not treat earnings as a direction signal. Does not place orders. Does not import the other data-source skill. |
| Use when | The user asks whether a named biopharma name is worth a look, or wants the BD and approval tracking method. "Is Akeso worth chasing?" becomes the four-step note, not a buy or sell. |
| Do not use when | They only want a quote, holdings, or an order, or a general report on a non-biopharma name. |
| Input | Company or drug name. For a new name, supply pipeline names (English and local), brands, codes, and BD partners for the tracking config. |
| Output | An objective four-step note. Tracking pushes only the three material event types. Silence on most days is normal. |
| Limits | Public sources, plus the user's key. NMPA and CDE run headless Playwright and need the Chromium build from `python3 -m playwright install chromium`. Not investment advice. |

## Core ideas

1. Value sits in pipeline, clinical data, patents, and regulators. SEC and HKEX financials are supporting context.
2. Earlier is not automatically useful. Track only what can move the stock. The impact library arrives in a later phase on a tracking request.
3. Track a name only if it has a meaningful innovative drug (first-in-class or a large indication).

## Names you may be asked about

BeiGene (6160) / Innovent (1801) / Akeso (9926) / Zai Lab (9688) / WuXi Biologics (2269) / CSPC (1093) / Sino Biopharm (1177) / Hansoh (3692) / HUTCHMED (0013) / Kelun-Biotech (6990) / RemeGen (9995)

These names illustrate the coverage. They are not recommendations.
