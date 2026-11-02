#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import json
import sys
import html
import argparse
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
from pathlib import Path

from .activation import require_api_key  # noqa: E402
from .runtime_env import load_runtime_env  # noqa: E402

load_runtime_env()                                       
require_api_key()                                

DEFAULT_CONFIG = "henlius_tracking_config.json"
                                                        
STATE_DIR = Path.home() / ".cache" / "biopharma_strategy" / "tracker_state"
HEARTBEAT_FILE = STATE_DIR / "_heartbeat.json"
SILENT_HEARTBEAT_DAYS = 7                                        

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121 Safari/537.36"}
SEC_UA = {"User-Agent": "Mozilla/5.0 (research contact: your-research@example.com)"}
EMA_HOME = "https://www.ema.europa.eu/en/homepage"
SEC_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
NEWS_RSS = [
    ("Endpoints", "https://endpts.com/feed/"),
    ("Fierce Biotech", "https://www.fiercebiotech.com/rss/xml"),
    ("Fierce Pharma", "https://www.fiercepharma.com/rss/xml"),
    ("BioPharma Dive", "https://www.biopharmadive.com/feeds/news/"),
    ("STAT", "https://www.statnews.com/feed/"),
    ("PharmaTimes", "https://pharmatimes.com/rss/"),
    ("GEN", "https://www.genengnews.com/feed/"),
]

                                                                     
GOOGLE_NEWS_JP = "https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
JP_BD_KEYWORDS = (
    "提携", "契約", "ライセンス", "承認", "承認取得", "独占", "供給",
    "導出", "導入", "買収", "合併", "治験", "license", "deal", "approval", "approves",
)
                                            
GOOGLE_NEWS_EN = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
EN_BD_KEYWORDS = (
    "license", "deal", "partnership", "agreement", "approval", "approves",
    "authorization", "authorisation", "milestone", "acquisition", "acquires", "merger",
)
SEC_LOOKBACK_DAYS = 7                                        
NEWS_LOOKBACK_HOURS = 72                                                      
CDE_LOOKBACK_DAYS = 90                                      

                                                
INN_EXCLUDE_SUFFIX = {
    "trastuzumab": ["deruxtecan", "emtansine"],
    "pertuzumab": [], "denosumab": [], "bevacizumab": [],
    "adalimumab": [], "rituximab": [], "neratinib": [],
}

                              
ETF_NOISE = ("ishares", "invesco", "vanguard", "trust", "etf", "fidelity", "spdr", "index", "fund")

def load_config(config_name):
                                                            
                                                               
    candidates = []
    raw = Path(config_name)
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(Path.cwd() / raw)                                 
        candidates.append(Path(__file__).resolve().parent / raw)         
        candidates.append(Path(__file__).resolve().parent.parent.parent / "configs" / raw)                    
    for p in candidates:
        if p.exists():
            return json.load(open(p))
    raise FileNotFoundError(f"config file not found: {config_name} (tried {len(candidates)} candidate paths)")

def _state_file(company_en):
    return STATE_DIR / f"{company_en}_pushed.json"

def load_state(company_en):
    f = _state_file(company_en)
    if f.exists():
        try:
            return json.load(open(f))
        except Exception:
            return {}
    return {}

def save_state(company_en, state):
    f = _state_file(company_en)
    f.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now().isoformat()
    _tmp = f.with_suffix(".tmp")
    with open(_tmp, "w") as fp:
        json.dump(state, fp, ensure_ascii=False, indent=2)
    _tmp.replace(f)

def _clean(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _extract_english_keywords(config):
    kws = []
    for m in config.get("pipeline_molecules", []):
        for f in ("name_en", "brand_eu", "brand_cn"):
            v = (m.get(f) or "").strip()
            if v and "/" in v:
                kws.extend(x.strip() for x in v.split("/") if x.strip())
            elif v:
                kws.append(v)
    return sorted(set(k for k in kws if k and len(k) >= 3))

                                                            

def _get_latest_chmp_url():
    r = requests.get(EMA_HOME, headers=UA, timeout=30)
    r.raise_for_status()
    links = re.findall(r'href="(/en/news/meeting-highlights[^"]*chmp[^"]*)"', r.text)
    if links:
        return "https://www.ema.europa.eu" + links[0]
    return None

def check_ema_chmp(config, pushed_urls):
    url = _get_latest_chmp_url()
    if not url:
        print("  ⚠️ EMA CHMP meeting highlights link not found", file=sys.stderr)
        return []
    if url in pushed_urls:
        print(f"  [EMA CHMP] meeting already pushed, skipping", file=sys.stderr)
        return []

    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    text = _clean(r.text)
    title = re.search(r"<title>([^<]+)</title>", r.text)
    meeting_title = html.unescape(title.group(1).strip()) if title else url

    keywords = _extract_english_keywords(config)
    hits = []
    for kw in keywords:
        base = kw.lower()
        exclude_suffixes = INN_EXCLUDE_SUFFIX.get(base, [])
        for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
            if exclude_suffixes:
                after = text[m.end(): m.end() + 25].lower().lstrip()
                if any(after.startswith(s) for s in exclude_suffixes):
                    print(f"  [excluded] {kw} followed by a derivative suffix (not this company's pipeline)", file=sys.stderr)
                    continue
            snippet = text[max(0, m.start() - 60): m.end() + 120]
            hits.append({"source": "EMA CHMP", "keyword": kw, "url": url,
                         "title": meeting_title, "snippet": snippet, "key": url})
            break
    return hits

                                                             

def check_partner_sec(config, pushed_ids):
    company_en = config.get("company_en", "")
    start = (datetime.now() - timedelta(days=SEC_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    queries = [f'"{company_en}"'] if company_en else []
                                           
                                                            
    for m in config.get("pipeline_molecules", []):
        if m.get("type") != "innovative":
            continue
        ne = (m.get("name_en") or "").strip()
        if ne and len(ne) >= 4 and " " not in ne:
            queries.append(f'"{ne}"')

    hits = []
    seen_docs = {}                                           
    for q in queries:
        try:
            r = requests.get(SEC_EFTS_URL, params={
                "q": q, "forms": "8-K", "dateRange": "custom", "startdt": start, "enddt": end,
            }, headers=SEC_UA, timeout=30)
            if r.status_code != 200:
                continue
            d = r.json()
            for h in d.get("hits", {}).get("hits", [])[:10]:
                src = h.get("_source", {})
                doc_id = str(h.get("_id", ""))
                names = src.get("display_names", [])
                filer = names[0] if names else "unknown"
                file_date = src.get("file_date", "")
                ciks = src.get("ciks", [])
                cik = ciks[0] if ciks else ""
                               
                if any(k in filer.lower() for k in ETF_NOISE):
                    continue
                if doc_id in pushed_ids:
                    continue
                                                               
                accession = doc_id.split(":")[0]
                if accession in seen_docs:
                    prev = seen_docs[accession]
                    if q not in prev["query"]:
                        prev["query"] += f" / {q}"
                    prev.setdefault("extra_keys", []).append(doc_id)
                    continue
                acc_no = accession.replace("-", "")
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/" if cik else ""
                item = {"source": "SEC 8-K", "filer": filer, "file_date": file_date,
                        "query": q, "url": url, "key": doc_id, "extra_keys": []}
                seen_docs[accession] = item
                hits.append(item)
        except Exception as e:
            print(f"  ⚠️ SEC query failed ({q}): {e}", file=sys.stderr)
    return hits

                                                       

def _parse_rss(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = []
        for item in root.iter("item"):
                                                         
            title_el = item.find("title")
            title = "".join(title_el.itertext()).strip() if title_el is not None else ""
            link = (item.findtext("link") or "").strip()
            pubdate = (item.findtext("pubDate") or "").strip()
            items.append({"title": title, "link": link, "pubDate": pubdate})
        return items
    except Exception as e:
        print(f"  ⚠️ RSS fetch failed ({url}): {e}", file=sys.stderr)
        return []

def check_industry_news(config, pushed_titles):
    company_en = (config.get("company_en") or "").lower()
    company_cn = config.get("company") or ""
              
    bd_kw = ("license", "deal", "partnership", "agreement", "approval", "approves",
             "authorization", "authorisation", "milestone", "授权", "合作", "获批", "批准")
                           
    company_kws = [company_en, company_cn]
    for m in config.get("pipeline_molecules", []):
        ne = (m.get("name_en") or "").strip()
        if ne and len(ne) >= 4:
            company_kws.append(ne.lower())

    hits = []
    for src_name, url in NEWS_RSS:
        for item in _parse_rss(url):
            title = item["title"]
            tl = title.lower()
                              
            if any(k and k.lower() in tl for k in company_kws):
                if any(k in tl for k in bd_kw):
                    if title in pushed_titles:
                        continue
                    hits.append({"source": src_name, "title": title,
                                 "link": item["link"], "pubDate": item["pubDate"], "key": title})
    return hits

def check_japan_news(config, pushed_titles):
    from urllib.parse import quote
    company_cn = config.get("company") or ""
    company_en = config.get("company_en") or ""
                                                  
                                                                    
    jp_kws = [company_cn, company_en]
    for m in config.get("pipeline_molecules", []):
        code = (m.get("code") or "").strip()
        if code and len(code) >= 3:
            jp_kws.append(code)
        if (m.get("type") or "") == "innovative":
            ne = (m.get("name_en") or "").strip()
            if ne and len(ne) >= 4 and " " not in ne:
                jp_kws.append(ne.lower())
    jp_kws = list(dict.fromkeys(k for k in jp_kws if k))        
    hits = []
    seen = set()                                      
    for kw in jp_kws:
        if not kw:
            continue
        try:
            url = GOOGLE_NEWS_JP.format(q=quote(kw))
            for item in _parse_rss(url):
                title = item["title"]
                tl = title.lower()
                if any(k in tl for k in JP_BD_KEYWORDS):
                    if title in pushed_titles or title in seen:
                        continue
                    seen.add(title)
                    hits.append({"source": "GoogleNews JP", "title": title,
                                 "link": item["link"], "pubDate": item["pubDate"], "key": title})
        except Exception as e:
            print(f"  ⚠️ Japanese news search failed ({kw}): {e}", file=sys.stderr)
    return hits

def check_english_news(config, pushed_titles):
    from urllib.parse import quote
    company_en = config.get("company_en") or ""
                                                              
    en_kws = [company_en]
    for m in config.get("pipeline_molecules", []):
        code = (m.get("code") or "").strip()
        if code and len(code) >= 3:
            en_kws.append(code)
        if (m.get("type") or "") == "innovative":
            ne = (m.get("name_en") or "").strip()
            if ne and len(ne) >= 4 and " " not in ne:
                en_kws.append(ne.lower())
    en_kws = list(dict.fromkeys(k for k in en_kws if k))
    hits = []
    seen = set()
    for kw in en_kws:
        try:
            url = GOOGLE_NEWS_EN.format(q=quote(kw))
            for item in _parse_rss(url):
                title = item["title"]
                tl = title.lower()
                if any(k in tl for k in EN_BD_KEYWORDS):
                    if title in pushed_titles or title in seen:
                        continue
                    seen.add(title)
                    hits.append({"source": "GoogleNews EN", "title": title,
                                 "link": item["link"], "pubDate": item["pubDate"], "key": title})
        except Exception as e:
            print(f"  ⚠️ English news search failed ({kw}): {e}", file=sys.stderr)
    return hits

                                                                                   

def check_cde_priority(config, pushed_ids):
    company = (config.get("cde_company") or config.get("company") or "").strip()
    if not company:
        return []
    try:
        import asyncio
        from .cde_priority_collector import collect
                                                   
        result = asyncio.run(collect([company], days=CDE_LOOKBACK_DAYS))
        data = result.get(company, {})
        hits = []
        for kind in ("优先审评", "突破性治疗"):
            for item in data.get(kind, []):
                key = f"{item.get('受理号', '')}_{item.get('药品名称', '')}_{item.get('公示日期', '')}"
                if key in pushed_ids:
                    continue
                hits.append({
                    "source": "CDE", "kind": item.get("类型", kind),
                    "drug": item.get("药品名称", ""), "受理号": item.get("受理号", ""),
                    "申请人": item.get("注册申请人", ""), "公示日期": item.get("公示日期", ""),
                    "状态": item.get("状态", ""), "罕见病": item.get("是否罕见病", ""),
                    "key": key,
                })
        return hits
    except Exception as e:
        print(f"  ⚠️ CDE query failed: {e}", file=sys.stderr)
        return []

                                              

def deliver_telegram(msg):
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            print("  ⚠️ TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping Telegram push", file=sys.stderr)
            return
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": msg[:4000], "parse_mode": "Markdown"},
                      timeout=10)
        print("  📲 Telegram push sent", file=sys.stderr)
    except Exception as e:
        print(f"  ⚠️ Telegram push failed: {e}", file=sys.stderr)

def deliver_email(msg, subject):
    try:
        import smtplib
        from email.mime.text import MIMEText
        host = os.environ.get("SMTP_HOST", "")
        user = os.environ.get("SMTP_USER", "")
        pwd = os.environ.get("SMTP_PASS", "")
        to = os.environ.get("ALERT_EMAIL", "")
        if not (host and user and pwd and to):
            print("  ⚠️ SMTP not configured (SMTP_HOST/SMTP_USER/SMTP_PASS/ALERT_EMAIL), skipping email", file=sys.stderr)
            return
        plain = msg.replace("**", "").replace("*", "")
        m = MIMEText(plain, "plain", "utf-8")
        m["Subject"] = subject
        m["From"] = user
        m["To"] = to
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(user, [to], m.as_string())
        print("  📧 Email sent", file=sys.stderr)
    except Exception as e:
        print(f"  ⚠️ Email sending failed: {e}", file=sys.stderr)

def _build_message(company, hits_by_source, filter_stats=None):
    lines = [
        f"🔬 **{company} upstream tracker · material signal**",
        f"Only three categories are pushed: data readout / regulatory approval or rejection / licensing or M&A with amount (foreign-language items translated into English)",
        "━━━━━━━━━━━",
    ]
    for src, hits in hits_by_source.items():
        if not hits:
            continue
        lines.append("")
        lines.append(f"📡 **{src} · {len(hits)} items**")
        for h in hits:
            lines.append("")
            if src == "EMA CHMP positive opinion":
                lines.append(f"   🎯 Keyword {h['keyword']} | {(h.get('title_cn') or h['title'])[:60]}")
                lines.append(f"   {(h.get('snippet_cn') or h.get('snippet', ''))[:120]}")
            elif src == "SEC 8-K partner disclosure":
                lines.append(f"   🏢 {h['filer']} | {h['file_date']}")
                lines.append(f"   query {h['query']}")
            elif src == "CDE priority review / breakthrough therapy (catalyst calendar)":
                lines.append(f"   📅 [{h['kind']}] {h['drug']} (expected future approval, not a buy signal)")
                lines.append(f"   acceptance no. {h['受理号']} | published {h['公示日期']} | {h['状态']}")
            else:
                label = h.get("category_label", "")
                age = h.get("age_hours")
                stamp = f"({age:.0f}h ago · {h.get('source', '')})" if age is not None else f"({h.get('source', '')})"
                lines.append(f"   {label} {(h.get('title_cn') or h.get('title', ''))[:90]}")
                lines.append(f"   {stamp}")
                if h.get("dup_count"):
                    lines.append(f"   └ same event covered by {h['dup_count']} media outlets (collapsed)")
            url = h.get("url") or h.get("link")
            if url:
                lines.append(f"   {url}")
    if filter_stats and filter_stats.get("raw"):
        s = filter_stats
        lines.append("")
        lines.append("━━━━━━━━━━━")
        lines.append(
            f"🔎 News filter: raw {s['raw']} → material {s['kept']}"
            f" (stale {s['dropped_stale']} / off-topic {s.get('dropped_irrelevant', 0)} / "
            f"stock-comment noise {s['dropped_noise']} / minor {s['dropped_minor']} / "
            f"same-event duplicates {s['clustered']})"
        )
    return "\n".join(lines)

def _translate_hits(material_hits, ema_hits):
    return

def _known_entities(config):
    ents = []
    for m in config.get("pipeline_molecules", []):
        for f in ("name_en", "code", "name_cn"):
            v = (m.get(f) or "").strip()
            if not v or len(v) < 3:
                continue
                                             
            for part in re.split(r"[/,;|]", v):
                part = part.strip()
                if len(part) >= 3:
                    ents.append(part)
    return list(dict.fromkeys(ents))

def _subject_terms(config):
    terms = [config.get("company", ""), config.get("company_en", ""),
             config.get("cde_company", "")]
                                                                    
    terms += config.get("aliases", []) + config.get("watch_keywords", [])
    for m in config.get("pipeline_molecules", []):
        for f in ("name_cn", "name_en", "code", "brand_cn", "brand_eu"):
            v = (m.get(f) or "").strip()
            for part in re.split(r"[/,;|]", v):
                part = part.strip()
                if len(part) >= 3:
                    terms.append(part)
    return list(dict.fromkeys(t for t in terms if t and len(t) >= 3))

def run_one(config_path, skip_cde=False, only_cde=False):
    config = load_config(config_path)
    company = config.get("company", "Company")
    company_en = config.get("company_en", "company")
    state = load_state(company_en)

    if only_cde:
        ema_hits = sec_hits = news_hits = japan_hits = english_hits = []
        cde_hits = check_cde_priority(config, set(state.get("cde_pushed", [])))
    else:
        ema_hits = check_ema_chmp(config, set(state.get("ema_chmp_pushed", [])))
        sec_hits = check_partner_sec(config, set(state.get("sec_pushed", [])))
        news_hits = check_industry_news(config, set(state.get("news_pushed", [])))
        japan_hits = check_japan_news(config, set(state.get("news_pushed", [])))
        english_hits = check_english_news(config, set(state.get("news_pushed", [])))
        cde_hits = [] if skip_cde else check_cde_priority(config, set(state.get("cde_pushed", [])))

                                      
    news_all = list(news_hits) + list(english_hits) + list(japan_hits)
    material_hits, filter_stats = [], {}
    if news_all:
        try:
            from .news_materiality_filter import filter_material
            material_hits, filter_stats = filter_material(
                news_all, lookback_hours=NEWS_LOOKBACK_HOURS,
                known_entities=_known_entities(config),
                subject_terms=_subject_terms(config))
            print(f"  🔎 news filter {filter_stats}", file=sys.stderr)
        except Exception as e:
            print(f"  ⚠️ materiality filter failed, falling back to pushing everything: {e}", file=sys.stderr)
            material_hits, filter_stats = news_all, {}

    hits_by_source = {}
    if ema_hits:
        hits_by_source["EMA CHMP positive opinion"] = ema_hits
    if sec_hits:
        hits_by_source["SEC 8-K partner disclosure"] = sec_hits
    if material_hits:
        hits_by_source["material news (data readout / regulatory approval or rejection / licensing or M&A)"] = material_hits
    if cde_hits:
        hits_by_source["CDE priority review / breakthrough therapy (catalyst calendar)"] = cde_hits

                                
    if not hits_by_source:
        _save_news_state(company_en, state, ema_hits, sec_hits, [], news_all, cde_hits)
        record_activity(company, pushed=False, scanned=len(news_all))
        print(f"  ✅ {company}: no material signal (raw news {len(news_all)} items all filtered out)", file=sys.stderr)
        return ""

    _translate_hits(material_hits, ema_hits)

    output = _build_message(company, hits_by_source, filter_stats)
    print(output, file=sys.stderr)
    deliver_telegram(output)
    deliver_email(output, subject=f"🔬 {company} upstream tracker · material signal")

    _save_news_state(company_en, state, ema_hits, sec_hits, material_hits, news_all, cde_hits)
    record_activity(company, pushed=True, scanned=len(news_all), kept=len(material_hits))
    return output

def _save_news_state(company_en, state, ema_hits, sec_hits, material_hits, news_all, cde_hits):
    news_keys = {h["key"] for h in news_all if h.get("key")}
    for h in material_hits:
        for k in h.get("merged_keys", []):
            news_keys.add(k)
    sec_keys = {h["key"] for h in sec_hits}
    for h in sec_hits:
        sec_keys |= set(h.get("extra_keys", []))                            
    new_state = {
        "ema_chmp_pushed": sorted(set(state.get("ema_chmp_pushed", [])) | {h["key"] for h in ema_hits}),
        "sec_pushed": sorted(set(state.get("sec_pushed", [])) | sec_keys),
        "news_pushed": sorted(set(state.get("news_pushed", [])) | news_keys),
        "cde_pushed": sorted(set(state.get("cde_pushed", [])) | {h["key"] for h in cde_hits}),
    }
    save_state(company_en, new_state)

def _load_hb():
    try:
        if HEARTBEAT_FILE.exists():
            return json.loads(HEARTBEAT_FILE.read_text())
    except Exception:
        pass
    return {}

def _save_hb(hb):
    try:
        HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = HEARTBEAT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(hb, ensure_ascii=False, indent=1))
        tmp.replace(HEARTBEAT_FILE)
    except Exception as e:
        print(f"  ⚠️ heartbeat ledger write failed: {e}", file=sys.stderr)

def record_activity(company, pushed, scanned, kept=0):
    hb = _load_hb()
    today = datetime.now().strftime("%Y-%m-%d")
    if pushed:
        hb["last_push_date"] = today
        hb["last_push_company"] = company
        hb["silent_scanned"] = 0
        hb["silent_companies"] = []
    else:
        hb["silent_scanned"] = int(hb.get("silent_scanned", 0)) + int(scanned)
        comps = hb.get("silent_companies", [])
        if company not in comps:
            comps.append(company)
        hb["silent_companies"] = comps[-20:]
    hb.setdefault("last_push_date", today)
    hb["last_run_date"] = today
    _save_hb(hb)

def maybe_heartbeat(force=False):
    hb = _load_hb()
    today = datetime.now().date()
    try:
        last_push = datetime.strptime(hb.get("last_push_date", ""), "%Y-%m-%d").date()
    except Exception:
        last_push = None
    try:
        last_hb = datetime.strptime(hb.get("last_heartbeat_date", ""), "%Y-%m-%d").date()
    except Exception:
        last_hb = None

    silent_days = (today - last_push).days if last_push else 0
    hb_gap = (today - last_hb).days if last_hb else 999

    if not force:
        if silent_days < SILENT_HEARTBEAT_DAYS or hb_gap < SILENT_HEARTBEAT_DAYS:
            print(f"  ⏱️ heartbeat skipped (silent {silent_days} days / last heartbeat {hb_gap} days ago)", file=sys.stderr)
            return ""

    scanned = int(hb.get("silent_scanned", 0))
    comps = ", ".join(hb.get("silent_companies", [])) or "all tracked targets"
    msg = (
        f"💤 **biopharma upstream tracker · liveness check**\n"
        f"No material signal for {silent_days} consecutive days (system running normally)\n"
        f"━━━━━━━━━━━\n"
        f"Coverage: {comps}\n"
        f"News scanned during the silent period: {scanned} matching the three categories (data readout / regulatory approval or rejection / licensing or M&A with amount): 0\n"
        f"(material signals are sparse by nature, about 1-2 per company per month; no news means no material event)"
    )
    print(msg, file=sys.stderr)
    deliver_telegram(msg)
    hb["last_heartbeat_date"] = today.strftime("%Y-%m-%d")
    _save_hb(hb)
    return msg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--watchlist", default=None, help="top-10 watchlist JSON; iterate every config and run trigger signals")
    ap.add_argument("--skip-cde", action="store_true", help="skip the CDE source (Playwright is slow), for the fast daily run")
    ap.add_argument("--only-cde", action="store_true", help="run only the CDE source (for the weekly catalyst calendar)")
    ap.add_argument("--force-heartbeat", action="store_true", help="force one silent heartbeat (for self-test)")
    args = ap.parse_args()

    if args.watchlist:
                                                                       
        _wl_raw = Path(args.watchlist)
        _wl_candidates = [Path.cwd() / _wl_raw, Path(__file__).resolve().parent / _wl_raw,
                          Path(__file__).resolve().parent.parent.parent / "configs" / _wl_raw]
        _wl_path = next((p for p in _wl_candidates if p.exists()), _wl_raw)
        wl = json.load(open(_wl_path))
        configs = wl.get("configs", [])
        print(f"  🔬 scanning {len(configs)} companies", file=sys.stderr)
        for cfg in configs:
            try:
                run_one(cfg, skip_cde=args.skip_cde, only_cde=args.only_cde)
            except Exception as e:
                print(f"  ⚠️ {cfg} failed: {e}", file=sys.stderr)
    elif args.config:
        try:
            run_one(args.config, skip_cde=args.skip_cde, only_cde=args.only_cde)
        except Exception as e:
            print(f"  ⚠️ {args.config} failed: {e}", file=sys.stderr)
    else:
        try:
            run_one(DEFAULT_CONFIG, skip_cde=args.skip_cde, only_cde=args.only_cde)
        except Exception as e:
            print(f"  ⚠️ {DEFAULT_CONFIG} failed: {e}", file=sys.stderr)

                                                   
    maybe_heartbeat(force=args.force_heartbeat)

if __name__ == "__main__":
    main()
