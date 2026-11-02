#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time

from .activation import require_api_key  # noqa: E402
from .runtime_env import load_runtime_env  # noqa: E402

load_runtime_env()                                       # Load the local runtime config (if any)
require_api_key()                                # Activation gate: no key, no run

BASE_URL = "https://www.chinadrugtrials.org.cn/"
PAGE_TIMEOUT = 30000                             # ms; every page call is bounded by this


def _unavailable(reason):
    """One line on stderr, empty result: this source is optional, the others still run."""
    print(f"[nmpa_clinical_trials] {BASE_URL} unavailable ({reason}); "
          f"returning no rows, every other source still runs", file=sys.stderr)


def _new_page(timeout=PAGE_TIMEOUT):
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = None
    try:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            locale="zh-CN",
            viewport={"width": 1280, "height": 800},
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = ctx.new_page()
        page.set_default_timeout(timeout)
        return p, browser, ctx, page
    except Exception:
        # Free what was already started, then let the caller degrade.
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        p.stop()
        raise


def _close(handles):
    for handle in handles:
        try:
            handle()
        except Exception:
            pass


def search_clinical_trials(keyword, max_results=20, timeout=PAGE_TIMEOUT):
    try:
        p, browser, _ctx, page = _new_page(timeout)
    except Exception as e:
        _unavailable(e)
        return []

    results = []
    try:
        page.goto(BASE_URL + "index.html", timeout=timeout,
                  wait_until="domcontentloaded")
        time.sleep(4)                            # let the search frame render

        # The registry renders its search box inside a frame-backed page.
        inp = page.locator("input[name='keywords']").first
        try:
            inp.fill(keyword)
        except Exception as e:
            raise RuntimeError(f"search input box not found, the page structure may have changed: {e}")
        inp.press("Enter")
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        time.sleep(4)                            # let the result table render

        # Table columns: index, registration_no, status, drug_name, indication, title
        rows = page.locator("table tr").all()
        for row in rows[1:max_results + 1]:
            cells = [c.strip() for c in row.locator("td").all_inner_texts()]
            if len(cells) >= 6 and cells[1].startswith("CTR"):
                results.append({
                    "registration_no": cells[1],
                    "status": cells[2],
                    "drug_name": cells[3],
                    "indication": cells[4],
                    "title": cells[5],
                })
    except Exception as e:
        _unavailable(e)
        return []
    finally:
        _close((browser.close, p.stop))
    return results


if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "泽布替尼"
    print(f"=== NMPA clinical trials search: {kw} ===")
    for r in search_clinical_trials(kw, max_results=10):
        print(r)
