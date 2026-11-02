#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import sys
import argparse
from datetime import datetime

from .activation import require_api_key  # noqa: E402
from .runtime_env import load_runtime_env  # noqa: E402

load_runtime_env()                                       # Load the local runtime config (if any)
require_api_key()                                # Activation gate: no key, no run

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

PRIORITY_URL = 'https://www.cde.org.cn/main/xxgk/listpage/2f78f372d351c6851af7431c7710a731'          # priority-review list page
BREAK_URL = 'https://www.cde.org.cn/main/xxgk/listpage/da6efd086c099b7fc949121166f0130c'             # breakthrough-therapy list page
SOURCE_TIMEOUT = 40000                            # ms; every page call is bounded by this


def _unavailable(url, reason):
    """One line on stderr, empty result: this source is optional, the others still run."""
    print(f'[cde_priority_collector] {url} unavailable ({reason}); '
          f'returning no rows, every other source still runs', file=sys.stderr)


def parse_table_rows(text, marker_start, marker_end):
    rows = []
    idx = text.find(marker_start)
    if idx < 0:
        return rows
    seg = text[idx: text.find(marker_end, idx) if text.find(marker_end, idx) > 0 else idx + 2000]
    # The page prints one record per tab-separated line.
    lines = [seg_line for seg_line in seg.split('\n') if '\t' in seg_line]
    for line in lines:
        cols = [c.strip() for c in line.split('\t')]
        if len(cols) >= 7 and cols[1] and cols[1] != '受理号':
            # Repeat the header check: the marker can start mid-table.
            if cols[1] in ('受理号',) and cols[2] == '药品名称':
                continue
            rows.append(cols)
    return rows


async def fetch_company_priority(company, days=None, kind='priority'):
    url = PRIORITY_URL if kind == 'priority' else BREAK_URL
    field_id = 'companyInclude' if kind == 'priority' else 'companyBreakInclude'
    marker = '纳入优先审评品种名单' if kind == 'priority' else '突破性治疗'

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            try:
                ctx = await browser.new_context(user_agent=UA)
                await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                page = await ctx.new_page()
                page.set_default_timeout(SOURCE_TIMEOUT)
                await page.goto(url, wait_until='domcontentloaded', timeout=SOURCE_TIMEOUT)
                await page.wait_for_timeout(6000)            # let the JS challenge settle
                await page.fill(f'#{field_id}', company)
                await page.evaluate(f"""() => {{
                    const inp = document.getElementById('{field_id}');
                    let el = inp;
                    while (el && el !== document.body) {{
                        el = el.parentElement;
                        if (el) {{
                            const btn = el.querySelector('.searchBtn');
                            if (btn) {{ btn.click(); return true; }}
                        }}
                    }}
                    return false;
                }}""")
                await page.wait_for_timeout(4000)
                text = await page.evaluate("() => document.body.innerText")
            finally:
                await browser.close()
    except Exception as e:
        _unavailable(url, e)
        return []

    rows = parse_table_rows(text, marker, '共 ')
    # Build one record per row; a short row simply lacks the tail fields.
    results = []
    for cols in rows:
        item = {
            '受理号': cols[1] if len(cols) > 1 else '',
            '药品名称': cols[2] if len(cols) > 2 else '',
            '注册申请人': cols[3] if len(cols) > 3 else '',
            '承办日期': cols[4] if len(cols) > 4 else '',
            '申请日期': cols[5] if len(cols) > 5 else '',
            '公示日期': cols[6] if len(cols) > 6 else '',
            '状态': cols[7] if len(cols) > 7 else '',
            '是否罕见病': cols[8] if len(cols) > 8 else '',
            '类型': '优先审评' if kind == 'priority' else '突破性治疗',
        }

        if days:
            try:
                d = datetime.strptime(item['公示日期'], '%Y-%m-%d')
                if (datetime.now() - d).days > days:
                    continue
            except (ValueError, TypeError):
                pass
        results.append(item)
    return results


async def collect(companies, days=None):
    out = {}
    for company in companies:
        out[company] = {'优先审评': [], '突破性治疗': []}
        out[company]['优先审评'] = await fetch_company_priority(company, days, 'priority')
        out[company]['突破性治疗'] = await fetch_company_priority(company, days, 'break')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--company', action='append', required=True, help='company name (may be passed multiple times); fuzzy matching supported, e.g. "Innovent"')
    ap.add_argument('--days', type=int, default=None, help='only publications from the last N days (default: all)')
    args = ap.parse_args()

    result = asyncio.run(collect(args.company, args.days))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
