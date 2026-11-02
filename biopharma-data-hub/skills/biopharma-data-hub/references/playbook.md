# Playbook

This is the only file for this phase. Do not open another file until `research_progress.py` names that path.

The session already chose a pull or a tracking pass. Follow that.

## Scope

Pull pipeline, clinical, approval, patent, and literature data for a named Hong Kong or US biopharma company, or track BD and approval signals that land before the company announcement. Stay inside this scope.

| | |
| --- | --- |
| Does | Pull public sources: ClinicalTrials.gov, FDA, EMA, NMPA trials, PubMed, Google Patents, plus CDE priority review, EMA CHMP, SEC 8-K, and industry RSS. Objective only. No trade calls. |
| Does not | Does not predict price direction. Does not treat financial statements as the main analysis. Does not promise NMPA/CDE scrapes without a GUI. Does not import the `biopharma-strategy` package. |
| Use when | The user names a biopharma company or drug and wants pipeline, approvals, patents, literature, or upstream BD/approval tracking. Example: "take a look at Akeso". |
| Do not use when | They only want a quote or an order, or a general equity report on a non-biopharma name. |
| Input | Company, English drug name, brand, or INN; or an existing tracking config under `configs/`. |
| Output | Structured data from the scripts. If you write it up, head the note with generation time (UTC+8), the model, and the source list. |
| Limits | The data sources are public. Runtime also needs the user's own key. Never hardcode a key. Not investment advice. |

## Core idea

Biopharma value sits in pipeline, clinical data, patents, and regulators. SEC and HKEX financials are supporting context only.
