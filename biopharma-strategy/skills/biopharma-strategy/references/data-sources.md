# Biopharma data sources

Ten free official sources. Six for the base analysis layer, four for the upstream tracker. Registered in `source_universe.json`.

Chinese company and drug names in the tracking configs are query keys for NMPA and CDE. Leave those strings as written.

---

## Base analysis (6) — `scripts/biopharma_data.py`

### 1. ClinicalTrials.gov (NIH, global trials)

- **Endpoint**: `https://clinicaltrials.gov/api/v2/studies`
- **Functions**: `get_clinical_trials(kw)` / `get_trial_detail(nct)`
- **Returns**: phase mix (I/II/III), indication breadth, status (recruiting/completed), NCT ids
- **Stability**: high
- **Use**: pipeline inventory. Phase III count is near-term value. Indication coverage is the longer runway.

### 2. FDA openFDA (US approvals + Orange Book)

- **Endpoint**: `https://api.fda.gov`
- **Functions**: `get_fda_drug(brand)` / `get_fda_orange_book(ingredient)`
- **Returns**: FDA approval records, Orange Book ingredient and market status (on market, generic competition)
- **Stability**: high
- **Trap**: the Orange Book has no patent expiry (approval and ingredient only). Estimate expiry from Google Patents `priority_date`.

### 3. EMA EPAR (EU approvals)

- **Endpoint**: `https://www.ema.europa.eu/en/documents/report`
- **Function**: `get_ema_drugs(active_substance)`
- **Returns**: EU approval, indication, therapeutic area
- **Stability**: high
- **Cache**: Excel download (~2,700 rows), 7-day local cache, so the ~898KB file is not fetched every run.

### 4. PubMed (NCBI literature)

- **Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- **Functions**: `search_pubmed(kw)` / `get_pubmed_summaries(pmids)`
- **Returns**: where new clinical data lands first (ASCO/ASH, ORR/PFS/OS, head-to-head, safety)
- **Stability**: high

### 5. Google Patents (global families)

- **Endpoint**: `https://patents.google.com/xhr/query` (unofficial, public)
- **Function**: `get_patents(kw)`
- **Returns**: patent family, active status by country, `priority_date` (used to estimate expiry)
- **Stability**: medium
- **Trap**: on failure, fall back to web search.

### 6. NMPA clinical-trial registry (China)

- **Endpoint**: `https://www.chinadrugtrials.org.cn`
- **Function**: `search_clinical_trials(kw)` (`nmpa_clinical_trials.py`)
- **Returns**: China CTR id, status, indication
- **Stability**: medium
- **Trap**: the page prints one record per tab-separated line, and the search box only appears after the frame loads. The scraper runs headless Playwright and caps every page call at 30 seconds. `requests` gets an empty page. Query with the Chinese INN, for example `search_clinical_trials("泽布替尼")`. When the site does not answer, the function prints one line and returns no rows.

---

## Upstream tracker (4) — `scripts/biopharma_tracker.py`

Catches BD and approval news before the company notice. The lead is days to weeks.

### 7. CDE priority review and breakthrough therapy (China, before approval)

- **Endpoint**: `https://www.cde.org.cn/main/xxgk/listpage/...` (two public lists)
- **Function**: `cde_priority_collector.py: collect([company names])`
- **Lead**: months to a year before NMPA approval (Innovent antibody: priority review May 2024, approval March 2025)
- **Stability**: medium
- **Role**: a catalyst calendar ("approval is coming"). Not a buy signal. The lead is too long to trade.
- **Trap**: Ruishu-class anti-bot. `requests` returns an empty page plus a JS challenge. Use Playwright (`headless=True`, `disable-blink-features`, hide `webdriver`). Wait about 6 seconds for the challenge, then fill the query box. Company names in the query stay Chinese.

### 8. EMA CHMP meeting highlights (EU, before approval)

- **Endpoint**: `https://www.ema.europa.eu/en/homepage` (meeting-highlights links)
- **Function**: `check_ema_chmp()`
- **Lead**: 4–7 days before the EC decision or the company notice (Henlius serplulimab: company notice 2026-03-30; EMA had already published on 23 and 26 March)
- **Stability**: high
- **Trap**: the page is English. Keywords are `name_en` / `brand_eu`. Drop biosimilar INNs so `trastuzumab` does not hit Enhertu, Kadcyla, and other ADCs.

### 9. SEC 8-K (US partner disclosure)

- **Endpoint**: `https://efts.sec.gov/LATEST/search-index` (EDGAR full-text search)
- **Function**: `check_partner_sec()`
- **Lead**: hours to days (the other side of a BD deal files first)
- **Stability**: high
- **Trap**: search the English company name plus the innovative-drug INN. Biosimilar INNs (`trastuzumab`, `rituximab`) are generic and hit dozens of unrelated firms. Check that the partner is a US listing first. A non-US partner makes this source useless.

### 10. Trade-press RSS (7 feeds)

- **Feeds**: Endpoints / Fierce Biotech / Fierce Pharma / PharmaTimes / BioPharma Dive / STAT / GenEngNews, plus Google News
- **Function**: `check_industry_news()`
- **Use**: BD leaks (Endpoints and Fierce often publish first)
- **Stability**: medium
- **Trap**: false reports happen. Cross-check a BD leak against the partner 8-K or an official filing. Fierce RSS wraps the title in `<a>`; extract with `"".join(el.itertext())`.

---

## Materiality filter (`scripts/biopharma_strategy/news_materiality_filter.py`)

Push only three kinds of item. Four gates: 72-hour window → subject match → noise list → materiality grade → cluster and dedupe.

| Kind | Test |
|------|------|
| Data readout | Pivotal data, primary endpoint hit or miss, unblinding, OS/PFS |
| Regulatory decision | NMPA/FDA/EMA approval or refusal, CRL, clinical hold, withdrawal, PDUFA |
| Deal with a number | Deal language plus an explicit amount (`$500M`, an upfront, and similar) |

Material hits are rare (about one or two per company per month). A quiet day is normal.

> Chinese headlines are an optional extra. The script prints the original title. To translate, implement `translate_batch` and call it from `_translate_hits` in `biopharma_tracker.py`.
