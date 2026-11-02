# Four-step read

This is the only file for this phase.

1. **Pipeline (capability):** `get_clinical_trials` + `search_clinical_trials` → stage mix, indication breadth, status. Phase III count is near-term value. Indication coverage is the longer runway.
2. **Approvals (upside):** `get_fda_drug` + `get_ema_drugs` → approved markets and breakthrough / orphan / priority review.
3. **Patents (durability):** `get_patents` + `get_fda_orange_book` → expiry and generic pressure.
4. **Literature (latest signal):** `search_pubmed` → latest ORR/PFS/OS, safety, head-to-head results.

The commands that call these functions arrive in the next phase. Do not open that file early.
