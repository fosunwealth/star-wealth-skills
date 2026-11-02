# How to run

This phase also names the source-pitfall note. Read that file for NMPA and CDE scrape limits. Do not open any other file.

```bash
cd scripts

python -m biopharma_strategy.biopharma_tracker --config ../configs/akeso_tracking_config.json

python -c "from biopharma_strategy.biopharma_data import get_clinical_trials; print(get_clinical_trials('zanubrutinib'))"
```

A note uses the four functions from the four-step file. A tracking request uses the tracker command and the config from the setup phase.

## Notes

 1. NMPA and CDE both run headless Playwright, so no display is needed. Both need the Chromium build from `python3 -m playwright install chromium`, not just the Python package. Every page call is capped at 30–40 seconds; when a site does not answer, that source prints one line and returns no rows, and the rest still run. The pitfall note in this phase is the detail.
2. Search SEC 8-K with the English company name plus the innovative-drug INN. Check first that the partner is US-listed.
3. EMA CHMP keywords are English plus INN, with negative filters for derivative products.
4. A trade-press BD rumor needs the partner's 8-K as a cross-check.
5. Head any write-up with time (UTC+8), model, and source list.
6. Runtime state, locks, and cache are isolated (`~/.biopharma/strategy/` and `~/.cache/biopharma_strategy/`).

Chat follows the user's language. Keep official names, tickers, and INNs as published. In an English reply, Chinese names stay only as NMPA or CDE query keys.
