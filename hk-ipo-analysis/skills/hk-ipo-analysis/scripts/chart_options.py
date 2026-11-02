#!/usr/bin/env python3

from __future__ import annotations

import json
from typing import Any

PALETTE = [
    "#c8102e",
    "#1f6feb",
    "#0f9d58",
    "#f59e0b",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#65a30d",
]

SLOTS: dict[str, dict[str, Any]] = {
    "ipo": {
        "id": "chart-ipo-radar",
        "section": "overview",
        "html_height": 320,
        "height": 320,
        "title": "Five-factor score",
    },
    "subscription": {
        "id": "chart-subscription-bar-0",
        "section": "mod-subscription",
        "html_height": 240,
        "height": 280,
        "title": "Subscription multiple",
        "shape": "auto",
    },
    "sponsor": {
        "id": "chart-sponsor-yAxisLabel",
        "section": "mod-sponsor",
        "html_height": 240,
        "height": 280,
        "title": "First-day gain probability %",
        "shape": "bar",
    },
    "fundamental": {
        "id": "chart-fundamental-line-0",
        "section": "mod-fundamental",
        "html_height": 280,
        "height": 280,
        "title": "Net profit · revenue · gross margin %",
    },
}

ORDER = ["ipo", "subscription", "sponsor", "fundamental"]

IPO_RADAR_MAX = 5.0

MIN_POINTS = 2

FUNDAMENTAL_SERIES = [
    ("netProfit", "Net profit"),
    ("growth", "Revenue"),
    ("grossProfitMargin", "Gross margin %"),
]

def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None

def _nums(values: Any) -> list[float]:
    if not isinstance(values, (list, tuple)):
        return []
    out: list[float] = []
    for item in values:
        number = _num(item)
        out.append(number if number is not None else 0.0)
    return out

def _pair(chart_data: dict[str, Any], prefix: str) -> tuple[list[str], list[float]]:
    years = chart_data.get(f"{prefix}Years")
    values = _nums(chart_data.get(f"{prefix}Values"))
    labels = [str(y) for y in years] if isinstance(years, (list, tuple)) else []
    return labels, values

def _radar_option(names: list[str], maximum: float, value: list[float]) -> dict[str, Any]:
    return {
        "backgroundColor": "#FFFFFF",
        "color": ["#c8102e"],
        "tooltip": {"trigger": "item"},
        "radar": {
            "indicator": [{"name": name, "max": maximum} for name in names],
            "center": ["50%", "58%"],
            "radius": "58%",
            "splitNumber": 4,
            "axisName": {"color": "#374151", "fontSize": 12},
            "splitLine": {"lineStyle": {"color": "#e6e8ec"}},
            "splitArea": {"areaStyle": {"color": ["#fff", "#fcfcfd"]}},
        },
        "series": [
            {
                "name": "Five-factor score",
                "type": "radar",
                "data": [{"name": "Five-factor score", "value": value}],
                "symbol": "circle",
                "symbolSize": 7,
                "areaStyle": {"opacity": 0.16},
                "lineStyle": {"width": 2},
            }
        ],
    }

def _cartesian_base(legend: list[str], categories: list[str], pointer: str) -> dict[str, Any]:
    return {
        "backgroundColor": "#FFFFFF",
        "color": list(PALETTE),
        "tooltip": {"trigger": "axis", "axisPointer": {"type": pointer}},
        "legend": {
            "bottom": 4,
            "left": "center",
            "itemGap": 14,
            "data": list(legend),
            "textStyle": {"fontSize": 11},
        },
        "grid": {"left": 48, "right": 20, "top": 48, "bottom": 48, "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": list(categories),
            "splitLine": {"show": False},
            "axisLabel": {"color": "#6b7280", "fontSize": 11},
        },
        "yAxis": {
            "type": "value",
            "name": "",
            "nameTextStyle": {"color": "#6b7280", "fontSize": 11},
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "splitLine": {"lineStyle": {"color": "#e6e8ec"}},
            "axisLabel": {"color": "#6b7280", "fontSize": 11},
        },
    }

def _single_series_option(name: str, values: list[float], pointer: str, shape: str) -> dict[str, Any]:
    option = _cartesian_base([name], [str(i + 1) for i in range(len(values))], pointer)
    if shape == "auto" and len(values) > 1:
        series = {
            "name": name,
            "type": "line",
            "data": list(values),
            "itemStyle": {"color": PALETTE[0]},
            "showSymbol": True,
            "symbolSize": 8,
            "smooth": False,
        }
    else:
        series = {
            "name": name,
            "type": "bar",
            "data": list(values),
            "itemStyle": {"color": PALETTE[0]},
            "barMaxWidth": 48,
        }
    option["series"] = [series]
    return option

def _line_option(series: list[tuple[str, list[float]]], categories: list[str]) -> dict[str, Any]:
    option = _cartesian_base([name for name, _ in series], categories, "cross")
    option["series"] = [
        {
            "name": name,
            "type": "line",
            "data": list(values),
            "itemStyle": {"color": PALETTE[index % len(PALETTE)]},
            "showSymbol": True,
            "symbolSize": 8,
            "smooth": False,
        }
        for index, (name, values) in enumerate(series)
    ]
    return option

def _radar_value(*candidates: Any) -> float:
    for raw in candidates:
        number = _num(raw)
        if number is not None:
            return number
    return 0.0

def _entry(key: str, option: dict[str, Any], title: str | None = None) -> dict[str, Any]:
    slot = SLOTS[key]
    return {
        "key": key,
        "id": slot["id"],
        "section": slot["section"],
        "title": slot["title"] if title is None else title,
        "html_height": slot["html_height"],
        "height": slot["height"],
        "option": option,
    }

def _ipo_entry(payload: dict[str, Any]) -> dict[str, Any]:
    rating = payload.get("ai_rating") or {}
    value = [
        _radar_value(rating.get("subscription_score")),
        _radar_value(rating.get("sentiment_score")),
        _radar_value(rating.get("industry_score")),
        _radar_value(rating.get("fundamental_score")),
        _radar_value(rating.get("valuation_score")),
    ]
    names = ["Subscription", "Sentiment", "Industry", "Fundamentals", "Valuation margin"]
    return _entry("ipo", _radar_option(names, IPO_RADAR_MAX, value))

def _subscription_entry(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = (payload.get("subscription") or {}).get("chart_data") or {}
    values = _nums(data.get("growthValues"))
    if not values:
        return None
    return _entry("subscription", _single_series_option("Subscription multiple", values, "shadow", SLOTS["subscription"]["shape"]))

def _sponsor_entry(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = (payload.get("sponsor") or {}).get("chart_data") or {}
    values = _nums(data.get("yAxisLabel"))
    if not values:
        return None
    return _entry("sponsor", _single_series_option("First-day gain probability %", values, "shadow", SLOTS["sponsor"]["shape"]))

def _fundamental_entry(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = (payload.get("fundamental") or {}).get("chart_data") or {}
    series: list[tuple[str, list[float]]] = []
    categories: list[str] = []
    for prefix, name in FUNDAMENTAL_SERIES:
        years, values = _pair(data, prefix)
        if not values:
            continue
        series.append((name, values))
        if len(years) > len(categories):
            categories = years
    if not series:
        return None
    series.sort(key=lambda item: max(abs(v) for v in item[1]))
    if not categories:
        categories = [str(i + 1) for i in range(max(len(v) for _, v in series))]
    title = " · ".join(name for name, _ in series)
    return _entry("fundamental", _line_option(series, categories), title)

BUILDERS = {
    "ipo": _ipo_entry,
    "subscription": _subscription_entry,
    "sponsor": _sponsor_entry,
    "fundamental": _fundamental_entry,
}

def build_entries(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    payload = payload if isinstance(payload, dict) else {}
    out: list[dict[str, Any]] = []
    for key in ORDER:
        entry = BUILDERS[key](payload)
        if entry is None:
            continue
        entry = _prune_degenerate(entry)
        if entry is not None:
            out.append(entry)
    return out

def _series_points(option: dict[str, Any]) -> list[int]:
    counts: list[int] = []
    for series in option.get("series") or []:
        if not isinstance(series, dict):
            continue
        data = series.get("data")
        if series.get("type") == "radar":
            value = None
            if isinstance(data, list) and data and isinstance(data[0], dict):
                value = data[0].get("value")
            counts.append(len(value) if isinstance(value, list) else 0)
        elif isinstance(data, list):
            counts.append(len(data))
    return counts

def _prune_degenerate(entry: dict[str, Any]) -> dict[str, Any] | None:
    option = entry.get("option") or {}
    series = [s for s in (option.get("series") or []) if isinstance(s, dict)]
    points = _series_points(option)
    if not points or max(points) < MIN_POINTS:
        return None
    if any(count < MIN_POINTS for count in points):
        kept = [s for s, count in zip(series, points) if count >= MIN_POINTS]
        option = dict(option)
        option["series"] = kept
        legend = option.get("legend")
        if isinstance(legend, dict):
            legend = dict(legend)
            legend["data"] = [s.get("name") for s in kept]
            option["legend"] = legend
        entry = dict(entry)
        entry["option"] = option
    return entry

def build_specs(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        {"id": entry["id"], "height": entry["height"], "option": entry["option"]}
        for entry in build_entries(payload)
    ]

def chart_slots(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        {
            "key": entry["key"],
            "id": entry["id"],
            "section": entry["section"],
            "title": entry["title"],
            "html_height": entry["html_height"],
        }
        for entry in build_entries(payload)
    ]

def specs_json(payload: dict[str, Any] | None) -> str:
    return json.dumps(build_specs(payload), ensure_ascii=False)
