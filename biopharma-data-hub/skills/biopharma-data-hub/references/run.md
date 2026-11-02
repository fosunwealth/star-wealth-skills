# How to run

This phase also names `source_universe.json`. Every source is listed there. Enter only through the `biopharma_data_sources` package.

```bash
cd scripts

python -m biopharma_data_sources.biopharma_tracker --config ../configs/akeso_tracking_config.json

python -c "from biopharma_data_sources.biopharma_data import get_clinical_trials; print(get_clinical_trials('zanubrutinib'))"
```

A pull uses the four functions from the four-step file. A tracking request uses the tracker command.

## Notes

1. The NMPA scraper runs headless Playwright. It needs the Chromium build from `python3 -m playwright install chromium`, not just the Python package. Every page call is capped at 30 seconds; when the site does not answer, the function prints one line and returns no rows.
2. The CDE collector runs headless Playwright on the same Chromium build. Its two list pages are capped at 40 seconds each; when a page does not answer, that list comes back empty and the rest of the pull still runs.
3. Head any write-up with time (UTC+8), model, and source list.
4. Scripts live in `biopharma_data_sources/` and stay isolated from `biopharma_strategy/`.

Chat follows the user's language. Keep official names, tickers, and INNs as published. In an English reply, Chinese names stay only as NMPA or CDE query keys.
