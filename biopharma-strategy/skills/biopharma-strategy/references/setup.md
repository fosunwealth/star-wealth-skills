# Add a company

This is the only file for this phase.

1. List the pipeline from the annual report, site, or prospectus: molecule names, brands, codes, and BD partners.
2. Copy `templates/tracking_config_template.json` to `<english_name>_tracking_config.json` and fill pipeline, partners, and keywords.
3. Schedule `biopharma_tracker.py --config <file>` twice a day (session and after the close).
4. Dry-run once and confirm the keywords hit EMA CHMP and the other sources.
