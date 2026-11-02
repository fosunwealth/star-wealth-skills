# Four-step read

This is the only file for this phase.

1. **Pipeline:** `get_clinical_trials` + `search_clinical_trials` → stage mix, indication breadth, status.
2. **Approvals and catalysts:** `get_fda_drug` + `get_ema_drugs` → approved markets, breakthrough / orphan / priority review.
3. **Patent moat:** `get_patents` + `get_fda_orange_book` → expiry and generic pressure.
4. **Literature:** `search_pubmed` → latest ORR/PFS/OS, safety, head-to-head results.
