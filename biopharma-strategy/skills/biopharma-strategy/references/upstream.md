# Upstream tracking

This is the only file for this phase. The impact library is a later phase.

## Lead time

| Signal | Lead | Use |
| --- | --- | --- |
| Conference-abstract preview | 7–21 days | Best |
| FDA approval before PDUFA | 3–7 days | High |
| EMA CHMP minutes | 4–7 days | High |
| Partner SEC 8-K | Hours to days | High |
| CDE priority review | Months to a year | Calendar mark only |

## Direction

The tools catch the time. Direction is data versus the class benchmark. Do not forecast direction.

- On a readout, compare actual ORR/PFS/OS with the class benchmark: ahead, a disruptive head-to-head, or behind.
- Abstract previews cut both ways (Akeso HARMONi-A abstract about −20%, HARMONi-2 about +37.5%).

## Materiality filter

`scripts/biopharma_strategy/news_materiality_filter.py`

Four gates: 72-hour window → subject match → noise list → materiality grade → event clustering. Push only three types: clinical readout, regulatory approval or rejection, and M&A or license-out with dollars.

Material signals are sparse (about one or two per company per month). Quiet days are normal.

## Suggested cron

| Job | schedule | Command |
| --- | --- | --- |
| Daily triggers | `0 8,20 * * *` | `biopharma_tracker.py --skip-cde` |
| Weekly CDE calendar | `0 8 * * 1` | `biopharma_tracker.py --only-cde` |
| Quarterly impact-library refresh | `0 3 2 1,4,7,10 *` | knowledge-base refresh script |

Run triggers (EMA CHMP, SEC 8-K, trade press) separately from the CDE calendar. CDE Playwright is slow.
