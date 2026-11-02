# Biopharma event-to-price case library

Generated: 2026-08-25 23:28 (UTC+8) · Sample: 10 Hong Kong biopharma leaders · lookback 500 trading days · large-move threshold |move| ≥ 8.0%

## Why this file exists (tracking rule)

Judge the tracker by **how much the information moves the price**, not by how early it arrives.
The method is **start from the price history and work back to the event**, not "the signal exists, so it is useful".
This file is step one of that work-back: list every session that actually moved the price, then attribute each one.

## Move profile by name

| Code | Name | Focus | Days | Up days | Down days | Best day | Worst day | Large-move rate |
|---|---|---|---|---|---|---|---|---|
| 09926 | Akeso | Innovative — bispecific PD-1/VEGF | 500 | 15 | 10 | +16.1% | -24.6% | 5.0% |
| 02696 | Henlius | Innovative — biosimilar + PD-1 | 500 | 18 | 9 | +18.9% | -19.1% | 5.4% |
| 06160 | BeiGene | Innovative — BTK/PD-1, global | 500 | 5 | 5 | +11.2% | -22.8% | 2.0% |
| 01801 | Innovent | Innovative — PD-1/GLP-1 | 500 | 11 | 4 | +17.4% | -21.1% | 3.0% |
| 09995 | RemeGen | Innovative — ADC / autoimmune | 500 | 38 | 15 | +20.1% | -21.7% | 10.6% |
| 01548 | GenScript Biotech | CXO + CAR-T (Legend Biotech) | 500 | 17 | 9 | +16.2% | -19.7% | 5.2% |
| 06990 | Kelun-Biotech | Innovative — ADC | 500 | 12 | 5 | +13.0% | -21.7% | 3.4% |
| 02616 | CStone | Innovative — small cap, high beta | 500 | 32 | 18 | +24.6% | -32.4% | 10.0% |
| 01877 | Junshi | Innovative — PD-1 | 500 | 23 | 12 | +33.7% | -21.6% | 7.0% |
| 03692 | Hansoh | Innovative — generic plus innovative | 500 | 2 | 3 | +13.6% | -13.2% | 1.0% |

## Events still to attribute (263 trading days, sorted by move size)

⚠️ **Attribution rule**: find a **specific event** on that session or the prior session (readout/approval/BD/financing/selling/index rebalance/a market-wide selloff).
If no specific event is found, mark it "no clear event - liquidity or sector" and **do not invent a story**.

| # | Code | Name | Date | Move | Side | Attribution (open) |
|---|---|---|---|---|---|---|
| 1 | 01877 | Junshi | 2025-08-05 | **+33.75%** | up | |
| 2 | 02616 | CStone | 2026-06-01 | **-32.42%** | down | |
| 3 | 02616 | CStone | 2025-04-07 | **-28.57%** | down | |
| 4 | 09926 | Akeso | 2025-04-07 | **-24.62%** | down | |
| 5 | 02616 | CStone | 2025-08-15 | **+24.56%** | up | |
| 6 | 06160 | BeiGene | 2025-04-07 | **-22.84%** | down | |
| 7 | 09995 | RemeGen | 2024-10-08 | **-21.75%** | down | |
| 8 | 06990 | Kelun-Biotech | 2025-04-07 | **-21.68%** | down | |
| 9 | 01877 | Junshi | 2025-04-07 | **-21.63%** | down | |
| 10 | 01801 | Innovent | 2025-04-07 | **-21.09%** | down | |
| 11 | 02616 | CStone | 2026-03-27 | **+20.72%** | up | |
| 12 | 09995 | RemeGen | 2025-06-12 | **+20.10%** | up | |
| 13 | 01548 | GenScript Biotech | 2025-04-07 | **-19.67%** | down | |
| 14 | 02696 | Henlius | 2025-04-07 | **-19.06%** | down | |
| 15 | 02696 | Henlius | 2025-02-26 | **+18.92%** | up | |
| 16 | 01877 | Junshi | 2025-02-26 | **+18.74%** | up | |
| 17 | 09995 | RemeGen | 2025-04-07 | **-18.49%** | down | |
| 18 | 01801 | Innovent | 2025-03-27 | **+17.41%** | up | |
| 19 | 09995 | RemeGen | 2025-03-17 | **+17.28%** | up | |
| 20 | 09995 | RemeGen | 2025-04-24 | **+17.14%** | up | |
| 21 | 09995 | RemeGen | 2024-09-27 | **+16.77%** | up | |
| 22 | 09995 | RemeGen | 2025-04-10 | **+16.34%** | up | |
| 23 | 01877 | Junshi | 2024-10-04 | **+16.23%** | up | |
| 24 | 09995 | RemeGen | 2025-06-24 | **+16.22%** | up | |
| 25 | 09995 | RemeGen | 2025-05-20 | **+16.19%** | up | |
| 26 | 01548 | GenScript Biotech | 2026-08-07 | **+16.18%** | up | |
| 27 | 09926 | Akeso | 2024-09-16 | **+16.14%** | up | |
| 28 | 01548 | GenScript Biotech | 2025-06-09 | **+16.14%** | up | |
| 29 | 02616 | CStone | 2024-09-27 | **+16.00%** | up | |
| 30 | 09926 | Akeso | 2024-09-09 | **+15.77%** | up | |
| 31 | 02616 | CStone | 2025-05-20 | **+15.65%** | up | |
| 32 | 01877 | Junshi | 2024-09-30 | **+15.61%** | up | |
| 33 | 09995 | RemeGen | 2026-04-01 | **+15.24%** | up | |
| 34 | 09995 | RemeGen | 2025-07-04 | **+15.01%** | up | |
| 35 | 01877 | Junshi | 2025-05-29 | **+14.96%** | up | |
| 36 | 09995 | RemeGen | 2024-11-01 | **+14.61%** | up | |
| 37 | 09995 | RemeGen | 2026-06-29 | **+14.43%** | up | |
| 38 | 09926 | Akeso | 2025-07-03 | **+14.33%** | up | |
| 39 | 01548 | GenScript Biotech | 2024-09-27 | **+14.16%** | up | |
| 40 | 01548 | GenScript Biotech | 2026-05-27 | **+14.16%** | up | |
| 41 | 01801 | Innovent | 2025-06-04 | **+14.14%** | up | |
| 42 | 09995 | RemeGen | 2024-10-30 | **+14.13%** | up | |
| 43 | 02616 | CStone | 2025-07-17 | **+14.02%** | up | |
| 44 | 09995 | RemeGen | 2024-10-04 | **+13.87%** | up | |
| 45 | 02616 | CStone | 2025-03-05 | **+13.69%** | up | |
| 46 | 09995 | RemeGen | 2025-08-14 | **+13.65%** | up | |
| 47 | 03692 | Hansoh | 2024-08-28 | **+13.64%** | up | |
| 48 | 01548 | GenScript Biotech | 2026-08-20 | **+13.62%** | up | |
| 49 | 02696 | Henlius | 2026-06-29 | **+13.60%** | up | |
| 50 | 01877 | Junshi | 2025-08-18 | **+13.25%** | up | |
| 51 | 09926 | Akeso | 2026-07-17 | **-13.21%** | down | |
| 52 | 03692 | Hansoh | 2025-04-07 | **-13.18%** | down | |
| 53 | 02616 | CStone | 2025-07-04 | **+13.07%** | up | |
| 54 | 06990 | Kelun-Biotech | 2025-02-21 | **+13.03%** | up | |
| 55 | 09995 | RemeGen | 2026-01-07 | **+12.93%** | up | |
| 56 | 02616 | CStone | 2025-08-21 | **+12.87%** | up | |
| 57 | 09926 | Akeso | 2025-04-01 | **+12.86%** | up | |
| 58 | 01801 | Innovent | 2024-11-04 | **+12.84%** | up | |
| 59 | 01877 | Junshi | 2026-07-17 | **-12.76%** | down | |
| 60 | 09926 | Akeso | 2026-04-23 | **-12.66%** | down | |

## Next step (for the agent)

1. For each top event in the table above, search that day's news and filings (`biopharma_tracker.py` news feeds `check_industry_news` / `check_japan_news` / `check_english_news`, plus web search)
2. Classify the event type: (1) clinical readout (2) regulatory decision or refusal (3) BD / license-out with a stated amount
 ④financing/placing ⑤insider selling ⑥index change ⑦sector/market move ⑧no clear event
3. For each event type, judge **whether an upstream source can catch it** (known before the company notice), and the **historical average impact**
4. write the conclusion back into the "event-type impact ranking" section of this file. That is what the tracker should watch
---

## 🔴 Split: strip market-wide days before scoring the tracker

Rule: on one session, 3 or more names moving the same way means market-wide or sector; 1-2 names means a single-name event.

| Class | Rows | Share | Meaning |
|---|---|---|---|
| market-wide/sector move | 99 | **37.6%** | the market or the sector fell together, spread across 24 trading days.**a company-event tracker will not catch these, and does not need to** |
| single-name events | 164 | **62.4%** | that is the real target of an event tracker |

### Top 10 market-wide sessions

| Date | Side | Names same way | Average move | Names |
|---|---|---|---|---|
| 2025-04-07 | down | 10 | -21.1% | CStone, Akeso, BeiGene, Kelun-Biotech, Junshi, Innovent |
| 2024-10-04 | up | 7 | +11.6% | Junshi, RemeGen, CStone, Innovent, Akeso, Kelun-Biotech |
| 2026-07-17 | down | 6 | -11.5% | Akeso, Junshi, CStone, Henlius, RemeGen, GenScript Biotech |
| 2024-10-08 | down | 5 | -13.0% | RemeGen, Junshi, CStone, Kelun-Biotech, GenScript Biotech |
| 2024-09-30 | up | 5 | +10.9% | Junshi, CStone, RemeGen, BeiGene, GenScript Biotech |
| 2026-04-01 | up | 5 | +10.4% | RemeGen, Junshi, Henlius, GenScript Biotech, Kelun-Biotech |
| 2026-06-29 | up | 5 | +12.1% | RemeGen, Henlius, Junshi, CStone, Akeso |
| 2025-07-17 | up | 5 | +10.3% | CStone, Akeso, BeiGene, GenScript Biotech, Kelun-Biotech |
| 2024-09-27 | up | 4 | +14.5% | RemeGen, CStone, GenScript Biotech, Junshi |
| 2026-08-07 | up | 4 | +11.1% | GenScript Biotech, CStone, RemeGen, Henlius |

### Top 15 single-name moves (attribute one by one)

| Date | Code | Name | size | Attribution (open) |
|---|---|---|---|---|
| 2025-08-15 | 02616 | CStone | **+24.56%** | |
| 2026-03-27 | 02616 | CStone | **+20.72%** | |
| 2025-06-12 | 09995 | RemeGen | **+20.10%** | |
| 2025-03-17 | 09995 | RemeGen | **+17.28%** | |
| 2025-04-24 | 09995 | RemeGen | **+17.14%** | |
| 2025-04-10 | 09995 | RemeGen | **+16.34%** | |
| 2025-06-24 | 09995 | RemeGen | **+16.22%** | |
| 2025-05-20 | 09995 | RemeGen | **+16.19%** | |
| 2024-09-16 | 09926 | Akeso | **+16.14%** | |
| 2025-06-09 | 01548 | GenScript Biotech | **+16.14%** | |
| 2024-09-09 | 09926 | Akeso | **+15.77%** | |
| 2025-05-29 | 01877 | Junshi | **+14.96%** | |
| 2024-11-01 | 09995 | RemeGen | **+14.61%** | |
| 2026-05-27 | 01548 | GenScript Biotech | **+14.16%** | |
| 2025-06-04 | 01801 | Innovent | **+14.14%** | |

### What this means for the tracker

1. About **38% are market-wide** (tariff panic, the US biotech sector, liquidity). This part **should not be the company-event tracker's job**. It belongs with the macro layer and the sector monitor.
2. Single-name events that can actually be tracked are **62%**. That is the ceiling of what a tracker can be worth. Do not use total moves as the denominator, or coverage will always look short.
3. Next: for the top 15 single-name events, look up that day's filing and news one by one. Classify each as readout, approval, BD, financing or selling, index change, or no clear event. Count each class's average impact and how early it can be caught.