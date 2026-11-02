#!/usr/bin/env python3

from __future__ import annotations

import html
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from chart_options import chart_slots, specs_json
from echarts_assets import inline_block

BEIJING_TZ = timezone(timedelta(hours=8))

CSS = """
:root{--accent:#c8102e;--ink:#111827;--sub:#6b7280;--line:#e6e8ec;--bg:#f6f7f9;--card:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Segoe UI",Roboto,sans-serif;
 line-height:1.7;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:24px 20px 64px}
header.hero{background:linear-gradient(135deg,#1a1a2e 0%,#3d1220 55%,#7a1226 100%);color:#fff;
 border-radius:18px;padding:30px 32px;box-shadow:0 10px 30px rgba(20,10,20,.18)}
.hero-top{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;justify-content:space-between}
.hero h1{margin:0;font-size:30px;letter-spacing:.5px;font-weight:700}
.hero .code{opacity:.78;font-size:14px;margin-top:6px;letter-spacing:1px}
.rating-badge{text-align:center;min-width:132px;background:rgba(255,255,255,.12);
 border:1px solid rgba(255,255,255,.22);border-radius:14px;padding:12px 16px;backdrop-filter:blur(4px)}
.rating-badge .stars{font-size:20px;letter-spacing:2px;line-height:1}
.rating-badge .star{position:relative;display:inline-block;color:#ffd166;letter-spacing:0}
.rating-badge .star.half{color:rgba(255,209,102,.32)}
.rating-badge .star.half::before{content:"★";position:absolute;left:0;top:0;width:50%;overflow:hidden;color:#ffd166}
.rating-badge .num{font-size:34px;font-weight:800;line-height:1.1}
.rating-badge .cap{font-size:12px;opacity:.8}
.hero-reason{margin-top:18px;font-size:15px;background:rgba(255,255,255,.1);
 border-left:3px solid #ffd166;padding:12px 16px;border-radius:0 10px 10px 0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:22px}
.fact{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:10px 14px}
.fact .k{font-size:11.5px;opacity:.72;letter-spacing:.4px}
.fact .v{font-size:16px;font-weight:650;margin-top:2px;word-break:break-all}
nav.toc{position:sticky;top:0;z-index:20;background:rgba(246,247,249,.94);backdrop-filter:blur(8px);
 display:flex;flex-wrap:wrap;gap:8px;padding:14px 0;margin:6px 0 18px;border-bottom:1px solid var(--line)}
nav.toc a{text-decoration:none;font-size:13px;color:#374151;background:#fff;border:1px solid var(--line);
 padding:6px 12px;border-radius:999px;transition:.15s}
nav.toc a:hover{border-color:var(--accent);color:var(--accent)}
section.card{background:var(--card);border:1px solid var(--line);border-radius:16px;
 padding:22px 24px;margin-bottom:18px;box-shadow:0 1px 3px rgba(16,24,40,.04)}
section.card>h2{margin:0 0 4px;font-size:19px;display:flex;align-items:center;gap:10px}
section.card>h2 .idx{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;
 border-radius:8px;background:var(--accent);color:#fff;font-size:13px;font-weight:700;flex:none}
.interp{margin:12px 0 0}
.interp p{margin:0 0 10px;font-size:14.6px;color:#26303f;text-align:justify}
.interp p .dim{font-weight:700;color:var(--accent)}
.chart{margin:16px 0 6px;padding:14px;border:1px solid var(--line);border-radius:12px;background:#fcfcfd;overflow-x:auto}
.chart-title{font-size:12.5px;color:var(--sub);margin-bottom:8px;letter-spacing:.4px}
.chart-box{width:100%;min-height:240px}
.radar-wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;justify-content:center;
 padding:14px;border:1px solid var(--line);border-radius:12px;background:#fcfcfd;margin-top:14px}
.radar-wrap .chart{flex:1 1 280px;margin:0;border:none;padding:0;background:transparent}
.radar-score{text-align:center}
.radar-score .star-num{font-size:44px;font-weight:800;color:var(--accent);line-height:1}
.radar-score .star-unit{font-size:13px;color:var(--sub);margin-left:4px}
.kv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-top:14px}
.kv{border:1px solid var(--line);border-radius:11px;padding:10px 12px;background:#fff}
.kv-key{font-size:11.5px;color:var(--sub);letter-spacing:.3px;margin-bottom:3px}
.kv-val{font-size:15.5px;font-weight:650;word-break:break-all}
.long-text{font-size:13.4px;color:#374151;line-height:1.65}
.mini-list{margin:0;padding-left:18px;font-size:13.2px;color:#374151}
.mini-json{margin:0;font-size:11.5px;color:#374151;white-space:pre-wrap;word-break:break-all;
 font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.gauges{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-top:14px}
.gauge{border:1px solid var(--line);border-radius:11px;padding:11px 13px;background:#fff}
.gauge-head{display:flex;justify-content:space-between;font-size:12.5px;color:#374151;margin-bottom:7px}
.gauge-val{font-weight:700;color:var(--accent)}
.gauge-track{height:8px;background:#eef0f3;border-radius:99px;overflow:hidden}
.gauge-fill{height:100%;background:linear-gradient(90deg,#f0a0b0,var(--accent));border-radius:99px}
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:13.4px}
th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:#fafbfc;font-size:12px;color:var(--sub);font-weight:650;letter-spacing:.4px;white-space:nowrap}
tbody tr:hover{background:#fcfcfd}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;font-size:11px;padding:2px 8px;border-radius:99px;background:#fdecef;color:var(--accent);font-weight:600}
.tag.g{background:#e8f6ee;color:#15803d}.tag.b{background:#eaf1fe;color:#1d4ed8}.tag.gray{background:#f1f2f4;color:#6b7280}
.lottery-head{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:6px}
.lot-card{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fff;text-align:center}
.lot-card .k{font-size:12px;color:var(--sub)}
.lot-card .v{font-size:23px;font-weight:750;color:var(--accent);margin-top:4px;word-break:break-all}
.summary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:14px}
.empty{color:var(--sub);font-size:13.5px;margin:12px 0 0}
footer{margin-top:26px;padding-top:18px;border-top:1px solid var(--line);font-size:12.4px;color:var(--sub)}
footer .row{display:flex;flex-wrap:wrap;gap:6px 20px}
@media print{nav.toc{display:none}body{background:#fff}section.card{break-inside:avoid;box-shadow:none}}
@media (max-width:640px){.hero h1{font-size:23px}section.card{padding:18px 16px}.wrap{padding:14px 12px 40px}}
"""

TOC_JS = """
(function(){
  var links=document.querySelectorAll('nav.toc a');
  links.forEach(function(a){a.addEventListener('click',function(){
    var t=document.querySelector(a.getAttribute('href'));
    if(t)t.scrollIntoView({behavior:'smooth',block:'start'});
  });});
})();
"""

BOOT_JS = """;
  function boot() {
    if (typeof echarts === 'undefined') return;
    specs.forEach(function (s) {
      var el = document.getElementById(s.id);
      if (!el) return;
      el.style.height = s.height + 'px';
      var chart = echarts.init(el);
      chart.setOption(s.option);
      window.addEventListener('resize', function () { chart.resize(); });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
"""

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
NODE_ID_LEN = 22

TITLE_SUFFIX = "Hong Kong IPO analysis"
CODE_SUFFIX = "Hong Kong IPO analysis · figures in UTC+8"
RATING_CAP = "AI rating / 5"
H2_KEY_STYLE = "margin-left:auto;font-size:11.5px;color:var(--sub);font-weight:400"
EMPTY = "—"

SECTIONS = [
    ("overview", "Offer terms and five-factor score", "0", None, "Overview"),
    ("mod-ipo", "AI rating · IPO snapshot", "1", "ipo", "1. AI rating · IPO snapshot"),
    ("mod-subscription", "Subscription and demand", "2", "subscription", "2. Subscription and demand"),
    ("mod-sponsor", "Sponsor and greenshoe", "3", "sponsor", "3. Sponsor and greenshoe"),
    ("mod-cornerstone", "Cornerstone investors", "4", "cornerstone", "4. Cornerstone investors"),
    ("mod-premium", "Cross-market premium", "5", "premium", "5. Cross-market premium"),
    ("mod-valuation", "Valuation", "6", "valuation", "6. Valuation"),
    ("mod-fundamental", "Fundamentals", "7", "fundamental", "7. Fundamentals"),
    ("mod-industry", "Industry", "8", "industry", "8. Industry"),
    ("mod-market", "Market backdrop", "9", "market", "9. Market backdrop"),
    ("lottery", "Allotment estimate", "✦", None, "Allotment"),
]

SCORE_DIMENSIONS = [
    ("Subscription", "subscription_score", "Subscription score"),
    ("Fundamentals", "fundamental_score", "Fundamentals score"),
    ("Sentiment", "sentiment_score", "Sentiment score"),
    ("Industry", "industry_score", "Industry score"),
    ("Valuation", "valuation_score", "Valuation score"),
]

TAG_VARIANTS = {
    "oneLot": "tag gray",
    "groupA": "tag b",
    "groupATail": "tag b",
    "groupB": "tag g",
    "groupBHead": "tag g",
    "topHammer": "tag",
}
TAG_DEFAULT = "tag"

SUMMARY_COLUMNS = ["Tier", "Lots applied", "Expected allotted lots"]
DETAIL_COLUMNS = ["Tier", "Lots applied", "Expected allotted lots", "Average allotment rate per lot", "Probability of at least one lot"]
SUMMARY_TITLE = "Key tiers (one lot / top of group A / start of group B / top)"
DETAIL_TITLE = "All tiers"

class _Ids:

    def __init__(self) -> None:
        self._used: set[str] = set()

    def new(self) -> str:
        while True:
            value = "".join(secrets.choice(ALPHABET) for _ in range(NODE_ID_LEN))
            if value not in self._used:
                self._used.add(value)
                return value

class _Doc:

    def __init__(self) -> None:
        self.ids = _Ids()

    def open_tag(
        self,
        tag: str,
        *,
        cls: str | None = None,
        eid: str | None = None,
        style: str | None = None,
        href: str | None = None,
        extra: list[tuple[str, str]] | None = None,
    ) -> str:
        attrs: list[tuple[str, str]] = []
        if cls is not None:
            attrs.append(("class", cls))
        if eid is not None:
            attrs.append(("id", eid))
        if style is not None:
            attrs.append(("style", style))
        if href is not None:
            attrs.append(("href", href))
        for key, value in extra or []:
            attrs.append((key, value))
        attrs.append(("data-page-node-id", self.ids.new()))
        rendered = "".join(f' {key}="{_esc_attr(value)}"' for key, value in attrs)
        return f"<{tag}{rendered}>"

    def el(self, tag: str, body: str = "", **kwargs: Any) -> str:
        return f"{self.open_tag(tag, **kwargs)}{body}</{tag}>"

def _esc_attr(value: str) -> str:
    return html.escape(str(value), quote=True)

def _esc(value: Any) -> str:
    return html.escape(str(value))

def _plain(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:g}"
    if isinstance(value, int):
        return str(value)
    return str(value).strip()

def _text(value: Any, empty: str = EMPTY) -> str:
    shown = _plain(value)
    return _esc(shown) if shown else empty

def _fmt_num(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.1f}"

def _score_text(value: Any) -> str:
    text = _plain(value)
    if not text:
        return ""
    try:
        return _fmt_num(float(text))
    except ValueError:
        return text

def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool) or value is None:
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default

def _datetime_text(value: Any) -> str:
    return _plain(value)

def _price_text(price: Any, currency: str) -> str:
    value = _plain(price)
    if not value:
        return ""
    return f"{value} {currency}".strip() if currency else value

def _rate_text(value: Any) -> str:
    text = _plain(value).replace("倍", "").strip()
    if not text or not any(ch.isdigit() for ch in text):
        return text
    return text if text.endswith("x") else f"{text}x"

def _first_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        for item in value:
            text = _plain(item)
            if text:
                return text
        return ""
    return value

def _x_text(value: Any) -> str:
    text = _plain(value).replace("倍", "").strip()
    if not text:
        return ""
    if _as_float(text) == 0:
        return ""
    return text if text.endswith("x") else f"{text}x"

def _stars(value: Any, doc: _Doc) -> str:
    score = _as_float(value)
    if score <= 0:
        return ""
    full = int(score)
    parts = [doc.el("span", "★", cls="star") for _ in range(full)]
    if score - full >= 0.5:
        parts.append(doc.el("span", "★", cls="star half"))
    return "".join(parts)

def _chart_of(slots: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    for slot in slots:
        if slot["key"] == key:
            return slot
    return None

def _chart_block(slot: dict[str, Any], doc: _Doc) -> str:
    title = doc.el("div", _text(slot["title"]), cls="chart-title")
    box = doc.el("div", "", cls="chart-box", eid=slot["id"], style=f"height:{slot['html_height']}px")
    return doc.el("div", title + box, cls="chart")

def _interp(paragraphs: Any, doc: _Doc) -> str:
    items = paragraphs if isinstance(paragraphs, (list, tuple)) else []
    rendered: list[str] = []
    for item in items:
        if isinstance(item, dict):
            label = _plain(item.get("label"))
            text = _plain(item.get("text"))
        else:
            label, text = "", _plain(item)
        if not text:
            continue
        if label:
            body = doc.el("span", _esc(label + ": "), cls="dim") + _esc(text)
        else:
            body = _esc(text)
        rendered.append(doc.el("p", body))
    if not rendered:
        rendered.append(doc.el("p", EMPTY))
    return doc.el("div", "".join(rendered), cls="interp")

def _kv_grid(rows: list[tuple[str, Any]], doc: _Doc) -> str:
    cells: list[str] = []
    for label, value in rows:
        if isinstance(value, (list, tuple)):
            items = [doc.el("li", _esc(_plain(item))) for item in value if _plain(item)]
            if not items:
                continue
            body = doc.el("div", _esc(label), cls="kv-key") + doc.el("ul", "".join(items), cls="mini-list")
        else:
            shown = _plain(value)
            if not shown:
                continue
            body = doc.el("div", _esc(label), cls="kv-key") + doc.el("div", _esc(shown), cls="kv-val")
        cells.append(doc.el("div", body, cls="kv"))
    return doc.el("div", "".join(cells), cls="kv-grid")

def _facts(rows: list[tuple[str, str]], doc: _Doc, *, style: str | None = None) -> str:
    cells = []
    for key, value in rows:
        body = doc.el("div", _esc(key), cls="k") + doc.el("div", value, cls="v")
        cells.append(doc.el("div", body, cls="fact"))
    return doc.el("div", "".join(cells), cls="facts", style=style)

def _gauge(label: str, score: float, doc: _Doc) -> str:
    head = doc.el(
        "div",
        doc.el("span", _esc(f"{label} (out of 20)")) + doc.el("span", _esc(f"{_fmt_num(score)} / 20"), cls="gauge-val"),
        cls="gauge-head",
    )
    ratio = max(0.0, min(100.0, score / 20.0 * 100.0))
    fill = doc.el("div", "", cls="gauge-fill", style=f"width:{round(ratio)}%")
    return doc.el("div", head + doc.el("div", fill, cls="gauge-track"), cls="gauge")

def _table(headers: list[str], rows: list[dict[str, Any]], doc: _Doc) -> str:
    head = doc.el("tr", "".join(doc.el("th", _esc(name)) for name in headers))
    body = ""
    for row in rows:
        cells = doc.el("td", doc.el("span", _text(row.get("groupName")), cls=TAG_VARIANTS.get(str(row.get("groupKey") or ""), TAG_DEFAULT)))
        for value in row.get("cells", []):
            cells += doc.el("td", _text(value), cls="num")
        body += doc.el("tr", cells)
    return doc.el("table", doc.el("thead", head) + doc.el("tbody", body))

def _row(record: Any, keys: list[str]) -> dict[str, Any]:
    source = record if isinstance(record, dict) else {}
    return {
        "groupKey": source.get("groupKey"),
        "groupName": source.get("groupName"),
        "cells": [source.get(key) for key in keys],
    }

def _records(values: Any) -> list[dict[str, Any]]:
    return [item for item in values if isinstance(item, dict)] if isinstance(values, (list, tuple)) else []

def _h2(title: str, idx: str, key: str | None, doc: _Doc) -> str:
    body = doc.el("span", _esc(idx), cls="idx") + _esc(title)
    if key:
        body += doc.el("span", _esc(key), style=H2_KEY_STYLE)
    return doc.el("h2", body)

def _card(section_id: str, body: str, doc: _Doc) -> str:
    return doc.el("section", body, cls="card", eid=section_id)

def _overview_section(payload: dict[str, Any], doc: _Doc, slots: list[dict[str, Any]]) -> str:
    issue = payload.get("issue_params") or {}
    industry = payload.get("industry_module") or {}
    rating = payload.get("ai_rating") or {}
    subscription = payload.get("subscription") or {}
    currency = _plain(issue.get("currency"))
    prices = [
        ("Offer price low", _price_text(issue.get("offer_price_min"), currency)),
        ("Offer price high", _price_text(issue.get("offer_price_max"), currency)),
        ("Entry cost per lot", _price_text(issue.get("applyAmountMin"), currency)),
        ("Oversubscription", _rate_text(subscription.get("rate_over"))),
        ("Subscription opens", _datetime_text(issue.get("apply_start_date"))),
        ("Subscription closes", _datetime_text(issue.get("apply_end_date"))),
        ("Expected listing date", _datetime_text(issue.get("trade_date"))),
        ("Industry", _plain(issue.get("industry")) or _plain((industry.get("chart_data") or {}).get("sectorName"))),
    ]
    facts = _facts([(key, _text(value)) for key, value in prices], doc)

    gauge_rows: list[tuple[str, str, float]] = []
    scores: list[tuple[str, str]] = []
    for label, field, chip in SCORE_DIMENSIONS:
        score = _as_float(rating.get(field)) * 4.0
        gauge_rows.append((label, chip, score))
        scores.append((chip, _fmt_num(score)))
    facts += _facts([(key, _esc(value)) for key, value in scores], doc, style="margin-top:12px")

    gauges = doc.el("div", "".join(_gauge(label, score, doc) for label, _, score in gauge_rows), cls="gauges")
    radar = _chart_of(slots, "ipo")
    badge = doc.el(
        "div",
        doc.el("span", _text(_score_text(rating.get("rating_value")), "0"), cls="star-num") + doc.el("span", "/ 5.0", cls="star-unit"),
        cls="radar-score",
    )
    wrap = doc.el("div", badge + _chart_block(radar, doc), cls="radar-wrap") if radar else ""
    body = _h2("Offer terms and five-factor score", "0", None, doc) + facts + gauges + wrap
    return _card("overview", body, doc)

def _ipo_section(payload: dict[str, Any], doc: _Doc) -> str:
    rating = payload.get("ai_rating") or {}
    body = _h2("AI rating · IPO snapshot", "1", "ipo", doc) + _interp(rating.get("interpretation"), doc)
    return _card("mod-ipo", body, doc)

def _subscription_section(payload: dict[str, Any], doc: _Doc, slots: list[dict[str, Any]]) -> str:
    subscription = payload.get("subscription") or {}
    data = subscription.get("chart_data") or {}
    interp = _interp(subscription.get("interpretation"), doc)
    chart = _chart_of(slots, "subscription")
    chart_block = _chart_block(chart, doc) if chart else ""
    grid = _kv_grid(
        [
            ("As of", _first_text(data.get("growthDateTime"))),
            ("Margin funds frozen", data.get("totalMarginFrozenFunds")),
            ("Public-offer proceeds", data.get("publicOfferFundraisingAmount")),
            ("Public-offer oversubscription", data.get("publicOfferOversubscriptionMultiple")),
        ],
        doc,
    )
    body = _h2("Subscription and demand", "2", "subscription", doc) + interp + chart_block + grid
    return _card("mod-subscription", body, doc)

def _sponsor_roster(sponsor: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in sponsor.get("interpretation") or []:
        if isinstance(item, dict):
            label = _plain(item.get("label"))
            if label and label not in names:
                names.append(label)
    for name in ((sponsor.get("chart_data") or {}).get("sponsorName") or []):
        label = _plain(name)
        if label and label not in names:
            names.append(label)
    return names

def _sponsor_section(payload: dict[str, Any], doc: _Doc, slots: list[dict[str, Any]]) -> str:
    sponsor = payload.get("sponsor") or {}
    data = sponsor.get("chart_data") or {}
    interp = _interp(sponsor.get("interpretation"), doc)
    chart = _chart_of(slots, "sponsor")
    chart_block = _chart_block(chart, doc) if chart else ""
    grid = _kv_grid(
        [
            ("Sponsor", _sponsor_roster(sponsor)),
            ("Greenshoe", data.get("sponsorGreenshoeScore")),
            ("Greenshoe max score", data.get("sponsorGreenshoeMaxScore")),
        ],
        doc,
    )
    body = _h2("Sponsor and greenshoe", "3", "sponsor", doc) + interp + chart_block + grid
    return _card("mod-sponsor", body, doc)

def _cornerstone_section(payload: dict[str, Any], doc: _Doc) -> str:
    module = payload.get("cornerstone") or {}
    data = module.get("chart_data") or {}
    grid = _kv_grid(
        [
            ("Lock-up", data.get("lockupPeriod")),
            ("Share of the global offer %", data.get("allocationRatio")),
            ("Cornerstone count", data.get("cornerstoneCount")),
            ("Cornerstone amount", data.get("investmentAmount")),
            ("Cornerstone quality score", data.get("cornerstoneQualityScore")),
            ("Cornerstone quality max", data.get("cornerstoneQualityMaxScore")),
        ],
        doc,
    )
    body = _h2("Cornerstone investors", "4", "cornerstone", doc) + _interp(module.get("interpretation"), doc) + grid
    return _card("mod-cornerstone", body, doc)

def _premium_section(payload: dict[str, Any], doc: _Doc) -> str:
    module = payload.get("premium") or {}
    data = module.get("chart_data") or {}
    if data.get("isApplicable"):
        grid = _kv_grid(
            [
                ("H-share offer price", data.get("hShareFinalOfferPrice")),
                ("A-share price (HKD)", data.get("aSharePriceConvertedToHkd")),
                ("A-share prior close", data.get("aSharePriceLastTradingDayBeforeListing")),
                ("Related ticker", data.get("relatedStockCode")),
                ("H vs A discount %", data.get("hShareDiscountVsAShare")),
                ("A-share TTM P/E", data.get("aShareTtmPe")),
            ],
            doc,
        )
    else:
        grid = ""
    body = _h2("Cross-market premium", "5", "premium", doc) + _interp(module.get("interpretation"), doc) + grid
    return _card("mod-premium", body, doc)

def _valuation_section(payload: dict[str, Any], doc: _Doc) -> str:
    module = payload.get("valuation_module") or {}
    data = module.get("chart_data") or {}
    grid = _kv_grid(
        [
            ("Valuation basis", data.get("valuationType")),
            ("This offer's multiple", _x_text(data.get("hkValuation"))),
            ("Peer average", _x_text(data.get("industryAvg"))),
            ("H-share market cap", data.get("totalMarketCap")),
            ("A/US TTM multiple", _x_text(data.get("aShareTtm"))),
        ],
        doc,
    )
    body = _h2("Valuation", "6", "valuation", doc) + _interp(module.get("interpretation"), doc) + grid
    return _card("mod-valuation", body, doc)

def _fundamental_section(payload: dict[str, Any], doc: _Doc, slots: list[dict[str, Any]]) -> str:
    module = payload.get("fundamental") or {}
    data = module.get("chart_data") or {}
    chart = _chart_of(slots, "fundamental")
    chart_block = _chart_block(chart, doc) if chart else ""
    grid = _kv_grid(
        [
            ("Revenue CAGR", data.get("cagr")),
            ("Currency", data.get("currency")),
            ("Greenshoe included", data.get("hasGreenshoe")),
        ],
        doc,
    )
    body = _h2("Fundamentals", "7", "fundamental", doc) + _interp(module.get("interpretation"), doc) + chart_block + grid
    return _card("mod-fundamental", body, doc)

def _industry_section(payload: dict[str, Any], doc: _Doc) -> str:
    module = payload.get("industry_module") or {}
    data = module.get("chart_data") or {}
    grid = _kv_grid([("Segment", data.get("sectorName"))], doc)
    body = _h2("Industry", "8", "industry", doc) + _interp(module.get("interpretation"), doc) + grid
    return _card("mod-industry", body, doc)

def _market_section(payload: dict[str, Any], doc: _Doc) -> str:
    module = payload.get("market") or {}
    data = module.get("chart_data") or {}
    grid = _kv_grid(
        [
            ("Hang Seng Index", data.get("hkHSIAnalysis")),
            ("Hang Seng TECH", data.get("hkHSTECHAnalysis")),
        ],
        doc,
    )
    body = _h2("Market backdrop", "9", "market", doc) + _interp(module.get("interpretation"), doc) + grid
    return _card("mod-market", body, doc)

def _lottery_section(payload: dict[str, Any], doc: _Doc) -> str:
    lottery = payload.get("lottery") or {}
    summary_rows = _records(lottery.get("summaryRows"))
    detail_rows = _records(lottery.get("detailRows"))
    cards = [("One-lot allotment rate", _plain(lottery.get("oneLotWinRate")))]
    subscribe_lots = _plain(lottery.get("subscribeLots"))
    if subscribe_lots and subscribe_lots != "0":
        cards.append(("Lots to apply for one allotted lot", f"{subscribe_lots} lots"))
    cards.append(("Tier rows", str(len(detail_rows))))
    head = doc.el(
        "div",
        "".join(
            doc.el("div", doc.el("div", _esc(key), cls="k") + doc.el("div", _text(value), cls="v"), cls="lot-card")
            for key, value in cards
        ),
        cls="lottery-head",
    )
    table_a = doc.el("div", _esc(SUMMARY_TITLE), cls="chart-title", style="margin-top:16px")
    table_a += _table(SUMMARY_COLUMNS, [_row(record, ["subscribeLots", "expectedWinLots"]) for record in summary_rows], doc)
    table_b = doc.el("div", _esc(DETAIL_TITLE), cls="chart-title", style="margin-top:18px")
    table_b += _table(
        DETAIL_COLUMNS,
        [_row(record, ["subscribeLots", "expectedWinLots", "expectedWinRate", "predictedOneLotWinRate"]) for record in detail_rows],
        doc,
    )
    body = _h2("Allotment estimate", "✦", None, doc) + head + table_a + table_b
    return _card("lottery", body, doc)

SECTION_BUILDERS = {
    "overview": _overview_section,
    "mod-ipo": _ipo_section,
    "mod-subscription": _subscription_section,
    "mod-sponsor": _sponsor_section,
    "mod-cornerstone": _cornerstone_section,
    "mod-premium": _premium_section,
    "mod-valuation": _valuation_section,
    "mod-fundamental": _fundamental_section,
    "mod-industry": _industry_section,
    "mod-market": _market_section,
    "lottery": _lottery_section,
}

def _sections(payload: dict[str, Any], doc: _Doc, slots: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for section_id, _, _, _, _ in SECTIONS:
        builder = SECTION_BUILDERS[section_id]
        if section_id in ("overview", "mod-subscription", "mod-sponsor", "mod-fundamental"):
            out.append(builder(payload, doc, slots))
        else:
            out.append(builder(payload, doc))
    return "".join(out)

def _hero(payload: dict[str, Any], symbol: str, name: str, doc: _Doc) -> str:
    rating = payload.get("ai_rating") or {}
    left = doc.el("div", doc.el("h1", _text(name, symbol or EMPTY)) + doc.el("div", _esc(f"{symbol} · {CODE_SUFFIX}"), cls="code"))
    badge = doc.el(
        "div",
        doc.el("div", _stars(rating.get("rating_value"), doc) or "★", cls="stars")
        + doc.el("div", _text(_score_text(rating.get("rating_value")), EMPTY), cls="num")
        + doc.el("div", _esc(RATING_CAP), cls="cap"),
        cls="rating-badge",
    )
    top = doc.el("div", left + badge, cls="hero-top")
    reason = doc.el("div", _text(rating.get("highlight")), cls="hero-reason")
    return doc.el("header", top + reason, cls="hero")

def _nav(doc: _Doc) -> str:
    links = "".join(doc.el("a", _esc(label), href=f"#{section_id}") for section_id, _, _, _, label in SECTIONS)
    return doc.el("nav", links, cls="toc")

def _footer(doc: _Doc) -> str:
    stamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    row1 = doc.el(
        "div",
        doc.el("span", _esc(f"Generated: {stamp} (UTC+8)")) + doc.el("span", _esc("Generated automatically")),
        cls="row",
    )
    row2 = doc.el(
        "div",
        doc.el("span", _esc("This report is for research only. It is not investment advice and not an offer to buy or sell any security. Official HKEX and issuer announcements prevail.")),
        cls="row",
        style="margin-top:6px",
    )
    return doc.el("footer", row1 + row2)

def render(payload: dict[str, Any] | None) -> str:
    data = payload if isinstance(payload, dict) else {}
    symbol = _plain(data.get("symbol"))
    name = _plain(data.get("stock_name")) or symbol or "Hong Kong IPO"
    doc = _Doc()
    slots = chart_slots(data)

    wrap = _hero(data, symbol, name, doc) + _nav(doc) + _sections(data, doc, slots) + _footer(doc)
    third = "\n(function(){\n  var specs = " + specs_json(data) + BOOT_JS
    scripts = f"<script>{TOC_JS}</script><script>{inline_block()}</script><script>{third}</script>"

    head = (
        doc.open_tag("meta", extra=[("charset", "utf-8")])
        + "\n"
        + doc.open_tag("meta", extra=[("name", "viewport"), ("content", "width=device-width,initial-scale=1")])
        + "\n"
        + f"<title>{_esc(name)} ({_esc(symbol)}) {_esc(TITLE_SUFFIX)}</title>"
        + "\n"
        + f"<style>{CSS}</style>"
    )
    return (
        "<!DOCTYPE html>\n"
        + doc.open_tag("html", extra=[("lang", "en")])
        + "\n"
        + doc.open_tag("head")
        + "\n"
        + head
        + "\n</head>\n"
        + doc.el("body", doc.el("div", wrap, cls="wrap") + "\n" + scripts)
        + "\n</body>\n</html>\n"
    )
