#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a tech-hardware research workspace. Standard library only.

    python3 research_scaffold.py --name "TSMC" --sector semiconductor --out ./research
    python3 research_scaffold.py --list-sectors

The gate runs before any of that. A missing or rejected key prints the signup
guide and exits. No workspace is written.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SECTORS: dict[str, dict] = {
    "semiconductor": {
        "label": "Semiconductors",
        "tag": "a strong cycle and high barriers",
        "chain": [
            "EDA/IP (license plus royalty) — Synopsys, Cadence, Arm — customers, royalty rate, new products",
            "Equipment (heavy R&D) — ASML, Applied Materials, NAURA — orders, lead time, qualification",
            "Materials (many SKUs, slow qualification) — Shin-Etsu, SUMCO, NSIG — capacity, price, customer qualification",
            "Fabless design (asset-light, high R&D) — NVIDIA, Qualcomm, HiSilicon — units, share, product cadence",
            "Foundry (heavy assets, scale) — TSMC, Samsung, SMIC — utilization, node progress, capex",
            "IDM — Intel, Samsung, Micron — capacity, price, gross margin",
            "OSAT (labor and scale) — ASE, JCET, TFME — utilization, advanced-packaging progress",
            "Distribution (spread and inventory cycle) — WPG, Avnet, CECport — inventory, receivables",
        ],
        "metrics": [
            "Utilization by link (under 70% usually means a loss)",
            "Node progress and the capex plan",
            "Distributor inventory and receivable aging (one of the earliest signals)",
            "NAND/DRAM spot (weekly, DRAMeXchange)",
            "Philadelphia Semiconductor Index, SOX (daily)",
            "SEMI equipment, materials, and fab data (monthly)",
        ],
        "questions": [
            "Equipment: how many months do orders on hand cover? Where is customer qualification stuck?",
            "Materials: which qualification stage, and how fast does share ramp after it?",
            "Design: tape-out and volume dates? Large-customer adoption? Share change?",
            "Foundry: utilization by node? Any change to the capex plan?",
            "OSAT: advanced-packaging ramp, and utilization?",
            "Distribution: how far is inventory above normal? What happened to receivable aging?",
        ],
        "warning": "On a cycle name, PE runs backwards: buy when PE is highest (the trough), sell when PE is lowest (the peak). Do not anchor memory, panels, mature-node foundry, or OSAT on PE.",
    },
    "consumer-electronics": {
        "label": "Consumer electronics",
        "tag": "a supply chain reset by each product cycle",
        "chain": [
            "Product cycle: phones yearly (Apple in September, Android in Q1–Q2), PCs 3–5 years, TWS 2–3 years, VR/AR 1–2 years",
            "Each large shift reallocates content value (3G to 4G to 5G, feature phone to smartphone, AI phone)",
            "Chain checks: prototype, pilot, volume, shipment. Each step has a signal",
            "Apple chain, in order: technology direction, supplier list, content per unit, share split, unit outlook",
        ],
        "metrics": [
            "Monthly units (IDC, Canalys, Counterpoint)",
            "Channel inventory (a high reading is a warning)",
            "BOM: which parts gained content value",
            "Replacement cycle (about 36–48 months globally; a longer cycle is the industry's main pressure)",
        ],
        "questions": [
            "Which technology directions are set for the new model? Did the supplier list change?",
            "Was NPI (new-product introduction) won, and on which module?",
            "How did content per unit change versus the prior generation? What is the share split?",
            "How many weeks of channel inventory, versus a year ago?",
        ],
        "warning": "Apple revises the supplier list every year. Cuts and swaps are normal. Do not treat a name as a permanent Apple supplier. Start the new-model chain check in Q3.",
    },
    "ai-compute": {
        "label": "AI compute hardware",
        "tag": "a super-cycle with supply and demand out of line",
        "chain": [
            "Silicon (highest content): GPUs (NVIDIA, AMD, domestic accelerators), CPUs, HBM",
            "Hardware: high-layer PCB and CCL, optical modules (800G/1.6T), connectors, power, liquid cooling, chassis",
            "Systems: server ODMs (FII, Quanta, Wistron, Inventec) and brands (Dell, HPE, Inspur)",
            "Buyers: cloud providers (Microsoft, Google, Amazon, Meta), plus internet, government, and enterprise",
        ],
        "metrics": [
            "GPU: NVIDIA quarterly data-center revenue, lead time, volume date, domestic-chip performance and software",
            "HBM: SK hynix, Samsung, Micron capacity, yield, price, and stack height",
            "Optical: 800G units, 1.6T sample and volume dates, price, customer share",
            "PCB/CCL: high-layer orders, M8/M9 qualification, capacity adds",
            "Liquid cooling: cold-plate versus immersion penetration, content per server, suppliers",
            "Quarterly capex guides and the AI share at Microsoft, Google, Amazon, and Meta",
        ],
        "questions": [
            "What share of the cloud buyer's quarterly capex guide is AI?",
            "Optical: 800G ramp? 1.6T sample and volume dates? Annual price decline?",
            "HBM: capacity, yield, stack height, and where pricing talks stand?",
            "PCB/CCL: high-layer order visibility? How far is M8/M9 qualification?",
            "Liquid cooling: cold plate or immersion, and content per server?",
        ],
        "warning": "Cross-check three paths: cloud capex, NVIDIA data-center revenue, and what the chain is actually building. A gap above 20% is the expectation gap. Do not call the top of the AI hardware cycle lightly, and do not ignore a wrong technology route.",
    },
    "display-panel": {
        "label": "Display panels",
        "tag": "heavy assets, a price cycle, and a technology shift",
        "chain": [
            "One high-generation line costs tens of billions of yuan. Depreciation is the largest cost",
            "Price wars clear the industry. Each trough has an exit or a takeover",
            "Technology path: LCD, then OLED, then MiniLED, then MicroLED",
        ],
        "metrics": [
            "Monthly panel price (WitsView, Sigmaintell, Omdia) — the core series",
            "Capacity: Korean exits (Samsung, LG Display) and new lines in China (BOE, TCL CSOT)",
            "Demand: TV units, larger average size, commercial, auto, and VR",
            "Utilization, and cash cost per square meter versus the panel price",
        ],
        "questions": [
            "Month-on-month price by size? Next month's quote?",
            "Utilization now? Any deliberate cut?",
            "How far are the Korean shutdowns? How far have the new China lines ramped?",
            "How many inches did the average size rise?",
        ],
        "warning": "Depreciation is fixed, and price clears the market. A trough looks like this: panel prices stable for 2–3 months, shutdown news, and a deliberate utilization cut.",
    },
    "communication": {
        "label": "Communications hardware",
        "tag": "a carrier capex cycle",
        "chain": [
            "RAN vendors: Huawei, Ericsson, Nokia, ZTE — the core of the industry, and the most concentrated",
            "Optical: modules, fiber, components — lifted by AI compute",
            "Base-station RF: filters, power amplifiers, antennas — the most elastic in a 5G build",
            "Switching and routing: Cisco, Arista — data-center networking follows cloud capex",
        ],
        "metrics": [
            "Annual capex plans from the major carriers (the year's compass)",
            "Build rhythm: Q1 plans, Q2 tenders, Q3–Q4 delivery and revenue",
            "5G to 5.5G to 6G, and content per site",
            "Geopolitics in export markets (sanctions on Huawei are the largest variable)",
        ],
        "questions": [
            "How does the year's carrier capex split across 5G, compute, and transport?",
            "Share of the centralized tender versus last year? Price decline?",
            "Actual 5.5G deployment, and the change in content per site?",
            "How large is the export book that sanctions or tariffs actually touch?",
        ],
        "warning": "Optical sits on both carrier capex and cloud capex. In an AI cycle the second one weighs more. Do not read an optical name off the carrier budget alone.",
    },
    "auto-electronics": {
        "label": "Automotive electronics",
        "tag": "more content per vehicle as cars electrify and automate",
        "chain": [
            "Power semiconductors: IGBT and SiC MOSFET — about 2,000–5,000 yuan per vehicle, the electrification core",
            "ADAS: compute, cameras, radar, domain controllers — L3 and above is tens of thousands of yuan per vehicle",
            "Cockpit: cockpit silicon, center display, HUD, audio — penetration rising quickly",
            "Sensors: cameras, millimeter-wave radar, lidar, pressure sensors",
            "Connectors and harnesses: high-voltage and high-speed — content per vehicle is rising",
        ],
        "metrics": [
            "Penetration: battery-electric vehicles, L2/L3, lidar",
            "Design wins and SOP dates (qualification takes 2–3 years; the win is the signal)",
            "Annual price decline (new products such as SiC often fall 10–20% a year; volume has to cover it)",
            "Room left for domestic substitution",
        ],
        "questions": [
            "Which vehicle programs are won, and what are the SOP dates?",
            "Where is AEC-Q100, and how long is left?",
            "Content per vehicle, and where did the annual price decline land?",
            "Domestic share now, and has the customer's willingness to switch changed?",
        ],
        "warning": "AEC-Q100 is a high bar. A consumer-electronics supplier does not become an automotive supplier in one step. Do not extrapolate. Take the annual price decline out of the revenue model explicitly.",
    },
}

TODAY = _dt.date.today().isoformat()


def _safe_dirname(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return cleaned or "untitled"


def _bullets(items) -> str:
    return "\n".join("- %s" % item for item in items)


def _numbered(items) -> str:
    return "\n".join("%d. %s" % (n, item) for n, item in enumerate(items, 1))


def build_files(name: str, sector_key: str) -> dict[str, str]:
    sector = SECTORS[sector_key]
    head = "> Name: **%s** | Vertical: **%s** (%s) | Opened: %s\n" % (
        name, sector["label"], sector["tag"], TODAY)

    overview = f"""# {name} · overview

{head}
> Research finds the expectation gap: where the consensus and the industry facts diverge, checked independently.
> The market prices the future, not the present.

## Status

| Step | Status | Date | Note |
| --- | --- | --- | --- |
| 1. Place the link | ☐ not started | | |
| 2. Three-layer scan | ☐ not started | | |
| 3. Desk research | ☐ not started | | |
| 4. Chain cross-check | ☐ not started | | |
| 5. Expert interviews | ☐ not started | | |
| 6. Tracking sheet | ☐ not started | | |
| 7. Pitfall review | ☐ not started | | |

## Warning for this vertical

> {sector["warning"]}

## Three questions before a conclusion

1. **What is the consensus, as a number or a story?**
   -
2. **How far is your view from it? Data gap, logic gap, or recognition gap?**
   -
3. **How many independent pieces of evidence support the gap?** (fewer than 2: the conclusion does not stand)
   -

## Depth check

- [ ] Know (the facts)
- [ ] Understand (the logic)
- [ ] **Anticipate (what happens next) — the note has to reach this line**

## Conclusion

**Claim**:

**Gap type**: ☐ data ☐ logic ☐ recognition    **Confidence**: ☐ high ☐ medium ☐ low ☐ conflict

**The other side** (required):

**If this is wrong** (a falsifier, plus the downside):
1. Falsifier A (observable, with a date):
2. Falsifier B:
3. Downside:
"""

    desk = f"""# {name} · desk research

{head}
## Five steps

- [ ] 1. Prospectus or annual report — model, product mix, customers and suppliers, risk factors, industry section
- [ ] 2. Three years of filings and the earnings calls — what management said, whether it happened, whether the story stayed consistent
- [ ] 3. At least three broker notes that disagree — industry frame, then the company, then the short comments
- [ ] 4. Draw the chain
- [ ] 5. Write the open questions into `02_open_questions.md`

## Five questions

1. **What does this company do, and how does it get paid?**
   -
2. **What drove the last three years of results?**
   -
3. **What is the industry's core tension, and where is the cycle?** (introduction 0–10% / growth 10–60% / mature 60–90% / decline above 90%)
   -
4. **What is the consensus, and where can it be wrong?** (no answer: do not start fieldwork)
   -
5. **What has to be checked in the field?**
   -

## Life cycle

| Stage | Penetration | Character | Focus | Now? |
| --- | --- | --- | --- | --- |
| Introduction | 0–10% | Immature technology, high cost, few players | Route, use case, the leader | ☐ |
| Growth | 10–60% | Penetration rising, both sides busy | Growth, share, capacity | ☐ |
| Mature | 60–90% | Slower growth, a stable structure | Cost, dividends, the cycle | ☐ |
| Decline | above 90% | Demand shrinks, capacity exits | The substitute, the exit pace | ☐ |

Penetration definition (numerator / denominator):

## TAM (at least two methods; a gap above 50% has to be explained)

| Method | Formula | Your figure | The assumption that matters |
| --- | --- | --- | --- |
| Top down | Downstream market x penetration x content per unit | | |
| Bottom up | Add the main customers' purchase plans | | |
| Analogy | A similar product's penetration curve | | |

Do not adopt the company's TAM. The reachable market can be a tenth of the slide.

## Chain map

Reference structure for this vertical:

{_bullets(sector["chain"])}

| Link | Players | Share | Gross margin | Capex, last 12 months | Bargaining | Barrier |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

Value split: high barrier 50%+, heavy assets 40%+ at the peak and a loss at the trough, assembly 10–20%, brand Apple 40%+ / Android 20–30% / white-label under 10%.

## Four structural questions

| Question | Answer |
| --- | --- |
| Concentration (CR3/CR5; CR3 above 70% is an oligopoly) | |
| Barriers (technology, capital, customer qualification, ecosystem) | |
| Bargaining (upstream, downstream, substitutes) | |
| Who might enter from outside | |

## Four company axes (1–5, plus one sentence of evidence)

| Axis | Item | Score | Evidence |
| --- | --- | --- | --- |
| Technology | R&D ratio (design is often 15–30%; under 10% is a warning) | | |
| Technology | Patent quality, cadence, technical lead's background | | |
| Customers | Inside a top chain (Apple, NVIDIA, Huawei, Tesla) | | |
| Customers | Concentration (one customer above 50% cuts both ways) | | |
| Customers | **Share inside that chain, up or down (the leading indicator)** | | |
| Cost | Gross margin versus peers, and why | | |
| Cost | Utilization (under 70% usually means a loss) | | |
| Cost | Yield | | |
| Management | Technical or commercial background, and how well they know the industry | | |
| Management | Integrity, fraud history, disposals (a problem is a veto) | | |
| Management | Equity incentives | | |
"""

    questions = f"""# {name} · open questions

{head}
> This is the fieldwork list. Each row ends as verified or as a conflict that is still open.

## Confidence

| Level | Condition | Can it be a conclusion? |
| --- | --- | --- |
| High | At least 3 independent sources agree, and at least 1 is a supplier or a customer | Yes, as a core claim |
| Medium | 2 independent sources agree | Yes, and say how far it was checked |
| Low | One source, or only the company | **No. It stays an open item** |
| Conflict | Sources disagree | The conflict is the information. Disclose it |

## Ledger

| # | Question | Why it matters | How to check | Sources so far | Confidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | ☐ open |
| 2 | | | | | | ☐ open |
| 3 | | | | | | ☐ open |

## Conflicts

| Topic | Source A | Source B | Lean | Next check |
| --- | --- | --- | --- | --- |
| | | | | |
"""

    fieldwork = f"""# {name} · fieldwork

{head}
> Compliance: do not ask for non-public earnings, unannounced orders, or unannounced deals. This is industry work, not inside information.
> An important conclusion needs 2–3 independent sources. One source, especially the company, gets a question mark.

## Order (do not shuffle it)

| Order | Who | Why | Done |
| --- | --- | --- | --- |
| 1 | Suppliers | Most objective: they see who is taking more and who is cutting | ☐ |
| 2 | Customers | Most concrete: volume, the product, the next plan | ☐ |
| 3 | Competitors | Most willing to talk about the other side's weak points | ☐ |
| 4 | Management | **Last.** You can only tell a fact from a script after you know the industry | ☐ |

## Six questions (do not ask what the annual report already answers)

1. Are this year's orders up or down versus last year, and by about how much?
2. Whose share is rising, whose is falling, and why?
3. Is the price up or down lately, and what is next?
4. What is utilization, and how many months is the build plan?
5. Is there a new technology, and who is ahead?
6. Are customers paying, or are receivables slipping?

## Questions for {sector["label"]}

{_numbered(sector["questions"])}

## How to ask an expert

| Do | Do not |
| --- | --- |
| Ask how and why | Ask a yes/no that leads the witness |
| Ask a small, concrete question | Ask "how do you see the industry" |
| Ask the same point two or three ways | Stop at the first answer |
| Ask for an example and a number | Let a vague phrase stand |
| Start open, and leave sensitive points for later | Open on a sensitive point |
| Learn the background first (company, role, years, specialty) | Start without that |

Four traps: treating the expert as an oracle; a question that is too big; hearing only what you hoped for; concluding from one expert.

## Note

### Note 1
```
Date:            Who: supplier / customer / competitor / management / expert
Background: (company / role / years / specialty)
Q1:
A1:
  · Versus the model: supports / conflicts / new
  · Still to cross-check:
New open items:
Conflicts:
Confidence now:
```
"""

    tracking = f"""# {name} · tracking

{head}
> Tracking is a reconciliation, not a scrapbook. Each row answers: versus the last assumption, is this above, in line, or below? Does the model change?

## Daily

| Date | Item | Source | This | Last | Versus the model | Change the model? |
| --- | --- | --- | --- | --- | --- | --- |
| | SOX | Bloomberg | | | | |
| | Taiwan electronics | Bloomberg | | | | |
| | Company filings | Company IR, EDGAR, HKEX, MOPS | | | | |
| | Chain news | DigiTimes | | | | |

## Weekly

| Date | Item | Source | This | Last | Versus the model | Change the model? |
| --- | --- | --- | --- | --- | --- | --- |
| | Panel price | WitsView | | | | |
| | NAND/DRAM spot | DRAMeXchange | | | | |
| | Phone units, weekly | Counterpoint / Canalys. CAICT only if it answers | | | | |
| | Channel inventory | First-hand channel | | | | |

## Monthly

| Date | Item | Source | This | Last | Versus the model | Change the model? |
| --- | --- | --- | --- | --- | --- | --- |
| | Global phone / PC / server units | IDC, Gartner | | | | |
| | Taiwan electronics monthly revenue | Company filings, TSIA | | | | |
| | Semiconductor equipment and materials | SEMI | | | | |

## Quarterly

| Date | Item | Source | This | Last | Versus the model | Change the model? |
| --- | --- | --- | --- | --- | --- | --- |
| | Company results | Company filing | | | | |
| | Cloud capex | Earnings calls | | | | |
| | Chain check | First-hand | | | | |
| | Industry series | TrendForce and peers | | | | |

## Metrics for {sector["label"]}

{_bullets(sector["metrics"])}

| Date | Metric | This | Last | Versus the model | Change the model? |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Source log

| Date | Layer (public / paid / personal) | Topic | Conclusion | Versus the model | Next action |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
"""

    pitfalls = f"""# {name} · pitfall review

{head}
## 1. Five cognitive traps

- [ ] **No straight line.** Do not extend the peak, and do not extend the trough. Hardware cycles. Nothing grows forever, and nothing stays down forever
- [ ] **No technology worship.** Cost, customers, channel, and management were weighed, not just the spec sheet
- [ ] **No story without orders.** Orders, revenue, and the profit date were checked
- [ ] **No overconfidence.** Time spent matches the size of the conclusion
- [ ] **Downside is written.** If this is wrong, how much, and on what fact?

**Falsifiers (required, observable, dated)**
1.
2.
**Downside**:

## 2. Seven fraud signals (3 or more: stop, and do not discuss valuation)

| # | Signal | Test | Hit |
| --- | --- | --- | --- |
| 1 | Gross margin 10 points above peers, with no reason that holds | Technology? Mix? Does the reason survive a second source? | ☐ |
| 2 | Lots of cash and lots of interest-bearing debt | Why borrow at a high rate if the cash is real? | ☐ |
| 3 | Receivables or inventory growing much faster than revenue | Revenue +20%, receivables +50%, inventory +60% | ☐ |
| 4 | Operating cash flow divorced from net income for a long time | Paper profit | ☐ |
| 5 | Auditor changes, especially a large firm to a small one | | ☐ |
| 6 | Large pledges or disposals by the controlling holder at a high price | The trade is the honest signal | ☐ |
| 7 | A high share of related-party sales | No real third-party customer | ☐ |

Hits: ___  One hit: explain it. Two: name the risk. Three or more: **stop**.

Hardware is manufacturing. Numbers that look too good usually are not real.

## 3. Valuation check

- [ ] If this is a cycle link (memory, panels, mature-node foundry, OSAT), **PE is not the anchor**
      (buy when PE is highest, sell when PE is lowest; use PB, EV per unit of capacity, or the price-cycle position)
- [ ] The cycle position is stated, with the evidence

## 4. Warning for this vertical

> {sector["warning"]}
"""

    return {
        "00_overview.md": overview,
        "01_desk_research.md": desk,
        "02_open_questions.md": questions,
        "03_fieldwork.md": fieldwork,
        "04_tracking.md": tracking,
        "05_pitfalls.md": pitfalls,
    }


def main(argv=None) -> int:
    from activation import require_api_key

    require_api_key()

    parser = argparse.ArgumentParser(
        description="Build a tech-hardware research workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", help='Name or topic, for example "TSMC"')
    parser.add_argument("--sector", help="Sector key. See --list-sectors")
    parser.add_argument("--out", default=".", help="Output root (default: current directory)")
    parser.add_argument("--list-sectors", action="store_true", help="List sector keys")
    parser.add_argument("--force", action="store_true", help="Overwrite files that already exist")
    args = parser.parse_args(argv)

    if args.list_sectors:
        print("sector keys:")
        for key, sector in SECTORS.items():
            print("  %-22s %s (%s)" % (key, sector["label"], sector["tag"]))
        return 0

    if not args.name or not args.sector:
        parser.error("--name and --sector are required (or use --list-sectors)")

    if args.sector not in SECTORS:
        print("unknown sector: %s" % args.sector, file=sys.stderr)
        print("choices: %s" % ", ".join(SECTORS), file=sys.stderr)
        return 2

    workdir = os.path.join(os.path.abspath(args.out), _safe_dirname(args.name))
    os.makedirs(workdir, exist_ok=True)

    files = build_files(args.name, args.sector)
    written, skipped = [], []
    for fname, content in files.items():
        fpath = os.path.join(workdir, fname)
        if os.path.exists(fpath) and not args.force:
            skipped.append(fname)
            continue
        with open(fpath, "w", encoding="utf-8") as handle:
            handle.write(content)
        written.append(fname)

    print("workspace: %s" % workdir)
    for fname in written:
        print("  [new] %s" % fname)
    for fname in skipped:
        print("  [kept] %s (already there; pass --force to replace)" % fname)
    print("Next: answer the five questions in 01_desk_research.md. Question 4 is the consensus. Do not start fieldwork without it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
