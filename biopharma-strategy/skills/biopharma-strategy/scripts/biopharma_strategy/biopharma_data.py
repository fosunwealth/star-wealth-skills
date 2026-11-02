#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

from .task_guard import retry_with_backoff  # noqa: E402
from .activation import require_api_key  # noqa: E402
from .runtime_env import load_runtime_env  # noqa: E402

load_runtime_env()                                       
require_api_key()                                

CLINICALTRIALS_BASE = "https://clinicaltrials.gov/api/v2/studies"
OPENFDA_BASE = "https://api.fda.gov"
UA = {"User-Agent": "BiopharmaDataSources/1.1 (research contact: your-research@example.com)"}

@retry_with_backoff(max_retries=3, base_delay=2)
def _get_json(url, params=None, timeout=30):
    import requests
    r = requests.get(url, params=params, timeout=timeout, headers=UA)
    r.raise_for_status()
    return r.json()

                                                          
import json as _json
CACHE_DIR = Path(__file__).parent / "data" / "biopharma_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3 * 86400                         

def _cached_call(name, fetch_fn, ttl=CACHE_TTL):
    import time
    cache_file = CACHE_DIR / f"{name}.json"
    try:
        result = fetch_fn()
        try:
            cache_file.write_text(
                _json.dumps(result, ensure_ascii=False, default=str), encoding="utf-8")
        except Exception:
            pass
        return result
    except Exception:
        if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < ttl:
            try:
                return _json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        raise

def get_clinical_trials(keyword, max_results=20):
    def _fetch():
        data = _get_json(CLINICALTRIALS_BASE, params={
            "query.term": keyword,
            "pageSize": max_results,
            "format": "json",
        })
        out = []
        for s in data.get("studies", []):
            ps = s.get("protocolSection", {})
            ident = ps.get("identificationModule", {})
            status = ps.get("statusModule", {})
            design = ps.get("designModule", {})
            sponsor = ps.get("sponsorCollaboratorsModule", {})
            out.append({
                "nct_id": ident.get("nctId"),
                "title": ident.get("briefTitle"),
                "overall_status": status.get("overallStatus"),
                "phases": design.get("phases", []),
                "start_date": (status.get("startDateStruct") or {}).get("date"),
                "completion_date": (status.get("completionDateStruct") or {}).get("date"),
                "sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
            })
        return out
    return _cached_call(f"clinical_{keyword}_{max_results}", _fetch)

def get_trial_detail(nct_id):
    return _get_json(f"{CLINICALTRIALS_BASE}/{nct_id}", params={"format": "json"})

def get_fda_drug(brand_name, limit=5):
    def _fetch():
        data = _get_json(f"{OPENFDA_BASE}/drug/drugsfda.json", params={
            "search": f'products.brand_name:"{brand_name}"',
            "limit": limit,
        })
        out = []
        for r in data.get("results", []):
            for p in r.get("products", []):
                out.append({
                    "brand_name": p.get("brand_name"),
                    "active_ingredients": [ai.get("name") for ai in p.get("active_ingredients", [])],
                    "marketing_status": p.get("marketing_status"),
                    "application_number": p.get("application_number"),
                    "sponsor_name": (r.get("openfda") or {}).get("manufacturer_name"),
                })
        return out
    return _cached_call(f"fda_drug_{brand_name}_{limit}", _fetch)

def get_fda_orange_book(active_ingredient, limit=10):
    def _fetch():
        data = _get_json(f"{OPENFDA_BASE}/drug/orangebook.json", params={
            "search": f'products.active_ingredients.name:"{active_ingredient.upper()}"',
            "limit": limit,
        })
        out = []
        for r in data.get("results", []):
            for p in r.get("products", []):
                out.append({
                    "brand_name": p.get("brand_name"),
                    "active_ingredients": [ai.get("name") for ai in p.get("active_ingredients", [])],
                    "marketing_status": p.get("marketing_status"),
                    "application_number": p.get("application_number"),
                    "dosage_form": p.get("dosage_form"),
                    "route": p.get("route"),
                })
        return out
    return _cached_call(f"fda_orangebook_{active_ingredient}_{limit}", _fetch)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pubmed(keyword, max_results=20):
    data = _get_json(f"{EUTILS_BASE}/esearch.fcgi", params={
        "db": "pubmed",
        "term": keyword,
        "retmode": "json",
        "retmax": max_results,
    })
    return data.get("esearchresult", {}).get("idlist", [])

def get_pubmed_summaries(pmids):
    if not pmids:
        return []
    ids = ",".join(str(p) for p in pmids)
    data = _get_json(f"{EUTILS_BASE}/esummary.fcgi", params={
        "db": "pubmed",
        "id": ids,
        "retmode": "json",
    })
    result = data.get("result", {})
    out = []
    for pid in pmids:
        r = result.get(str(pid))
        if r and isinstance(r, dict):
            out.append({
                "pmid": str(pid),
                "title": r.get("title"),
                "journal": r.get("fulljournalname"),
                "pubdate": r.get("pubdate"),
                "authors": [a.get("name") for a in r.get("authors", [])[:3]],
            })
    return out

GPATENTS_BASE = "https://patents.google.com/xhr/query"

def get_patents(query, max_results=20):
    def _fetch():
        data = _get_json(GPATENTS_BASE, params={"url": f"q={query}"})
        out = []
        for cluster in data.get("results", {}).get("cluster", []):
            for r in cluster.get("result", []):
                p = r.get("patent", {})
                fm = (p.get("family_metadata", {}).get("aggregated", {})
                      .get("country_status", []))
                active = [c.get("country_code") for c in fm
                          if (c.get("best_patent_stage") or {}).get("state") == "ACTIVE"]
                out.append({
                    "patent_number": p.get("publication_number"),
                    "title": p.get("title"),
                    "assignee": p.get("assignee"),
                    "priority_date": p.get("priority_date"),
                    "grant_date": p.get("grant_date"),
                    "active_countries": active,
                })
                if len(out) >= max_results:
                    return out
        return out
    return _cached_call(f"patents_{query}_{max_results}", _fetch)

EMA_XLSX_URL = ("https://www.ema.europa.eu/en/documents/report/"
                "medicines-output-medicines-report_en.xlsx")
EMA_CACHE = Path.home() / ".cache" / "biopharma_strategy" / "ema_medicines.xlsx"
EMA_CACHE_TTL = 7 * 86400          

def _load_ema_df():
    import time
    import pandas as pd
    if EMA_CACHE.exists() and (time.time() - EMA_CACHE.stat().st_mtime) < EMA_CACHE_TTL:
        return pd.read_excel(EMA_CACHE, header=8)
    import requests
    r = requests.get(EMA_XLSX_URL, headers=UA, timeout=90)
    r.raise_for_status()
    EMA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    EMA_CACHE.write_bytes(r.content)
    return pd.read_excel(EMA_CACHE, header=8)

def get_ema_drugs(active_substance, limit=20):
    df = _load_ema_df()
    mask = df["Active substance"].str.contains(
        active_substance, case=False, na=False)
    sub = df[mask].head(limit)
    out = []
    for _, row in sub.iterrows():
        out.append({
            "name": row.get("Name of medicine"),
            "active_substance": row.get("Active substance"),
            "inn": row.get("International non-proprietary name (INN) / common name"),
            "status": row.get("Medicine status"),
            "therapeutic_area": row.get("Therapeutic area (MeSH)"),
            "ema_number": row.get("EMA product number"),
        })
    return out

if __name__ == "__main__":
    import json
    kw = sys.argv[1] if len(sys.argv) > 1 else "zanubrutinib"
    print(f"=== Clinical trials: {kw} ===")
    for t in get_clinical_trials(kw, max_results=5):
        print(json.dumps(t, ensure_ascii=False))
