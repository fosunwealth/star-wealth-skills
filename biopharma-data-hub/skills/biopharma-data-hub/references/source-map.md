# Source map

This is the only file for this phase. Ten sources. Do not open the call list until the queue names it.

Six base sources (`biopharma_data.py`):

| Lens | Source | Function |
| --- | --- | --- |
| Global trials | ClinicalTrials.gov | `get_clinical_trials(kw)` / `get_trial_detail(nct)` |
| US approval | FDA openFDA | `get_fda_drug(brand)` / `get_fda_orange_book(ingredient)` |
| EU approval | EMA EPAR | `get_ema_drugs(active_substance)` |
| China trials | NMPA | `search_clinical_trials(kw)` (Playwright) |
| Literature | PubMed | `search_pubmed(kw)` / `get_pubmed_summaries(pmids)` |
| Patents | Google Patents | `get_patents(kw)` |

Four upstream sources (`biopharma_tracker.py`): CDE priority review, EMA CHMP, SEC 8-K, industry RSS.
