# Playbook

This is the only file for this phase. Do not open another file under `references/` or `assets/` until `research_progress.py` names that path.

The session already chose the mode and, when it could, the vertical. Follow that. Do not switch mode on your own.

## Principle

Research finds the **expectation gap**: where the market's consensus and the industry's facts diverge, checked independently. The market prices the future, not the present. Once everyone knows the good news, it is already in the price.

| Depth | Content | Bar |
| --- | --- | --- |
| Know | What happened | A filing or a news item is enough |
| Understand | Why it happened | Supply chain and supply-demand |
| Anticipate | What happens next | This is the point of the work |

A note that stops at Know has no use.

## When to use it

| | |
| --- | --- |
| Does | A research frame, a supply-chain map, and a tracking list for the six verticals. A workflow from fetch to desk work to cross-checks to expert interviews to a tracking sheet. A pitfall list: cognitive traps, the cycle-valuation trap, seven fraud signals, and the compliance line. |
| Does not | A live quote terminal. A score engine. A buy or sell instruction. |
| Use when | A new tech-hardware name or vertical, a cycle-position or TAM question, a supply-chain or expert-interview list, a tracking sheet, or a pitfall review. "How do I research this industry?" is this skill. |
| Do not use when | They only want a quote or a filing with no analysis. They only want a buy or sell. The name is outside the six verticals (pharma, consumer staples, banks). Say so and stop. Do not reuse this skill's industry assumptions. |
| Input | A company or a vertical inside the six. A sector key when they want a workspace. |
| Output | One self-contained HTML report, or a six-file workspace. Objective only. No trade calls. |
| Limits | Public pages, plus the user's key. A figure that cannot be found is marked unavailable. Not investment advice. |

## Three ways to run

The session mode is one of these. A later phase names the files. This list does not.

**Full study.** "Research this name." Fetch, walk the six steps, deliver the report.

**One question.** "How do I research semiconductors?" or "Map the optical-module chain." Fetch, read the one sector file the queue names, answer. Do not build a workspace.

**Report only.** The user already supplied the notes and the figures. Write the report. Skip desk work, the chain cross-check, and the expert interview.

**Workspace.** They asked for a research workspace. After this file, run the scaffold command the queue names. The six files are the deliverable. Do not also write the HTML report unless they asked for one.

## Six steps

Each later file arrives in `next_action`. Do not open it early.

| Step | Do | Output |
| --- | --- | --- |
| 0 | Fetch. Required, except report-only, where the user already supplied the figures | A sourced table |
| 1 | Place the link: which semiconductor step, which consumer chain, which AI layer | One sentence |
| 2 | Three layers: life cycle and TAM / value split and structure / the company on four axes | Notes |
| 3 | Desk work: prospectus and annual report, three years of filings and calls, several brokers, a chain map, an open-question list | Desk notes |
| 4 | Cross-check: suppliers, then customers, then competitors, management last | Field notes |
| 5 | Expert interview. Do not ask what the annual report already answers | Notes |
| 6 | Daily / weekly / monthly / quarterly tracking, three source layers | A tracking sheet |

Every round must answer: **what is the consensus, and where can it be wrong?** If it cannot, the work is not finished.

One question uses steps 0 and 1, then the report contract for a short note. Report-only uses steps 1, 2, and 6. A workspace runs the scaffold, which lays these steps out as files.

## Which key

If the queue asks you to set `--sector`, use one key:

| The name sits in | Key |
| --- | --- |
| EDA, equipment, materials, design, foundry, IDM, OSAT, memory, distribution | `semiconductor` |
| Phones, PCs, TWS, VR, the Apple chain | `consumer-electronics` |
| GPU, HBM, optical modules, PCB, liquid cooling, server ODMs | `ai-compute` |
| LCD, OLED, MiniLED, MicroLED | `display-panel` |
| RAN, carrier optical, RF, switching | `communication` |
| Power semis, ADAS, cockpit, sensors, auto connectors | `auto-electronics` |

Optical modules are `ai-compute`. Carrier optical is `communication`.

## Sector card

| Vertical | Cycle | The metric | The trap |
| --- | --- | --- | --- |
| Semiconductors | Strong cycle, high barriers | Foundry: utilization. Design: units and share. Equipment: orders | Buying the low PE at the peak |
| Consumer electronics | Annual product cycle | Monthly units (IDC, Canalys, Counterpoint) and channel inventory | "Always an Apple supplier" |
| AI compute | Super-cycle, mismatched supply | Quarterly capex guide of the cloud buyers | The wrong technology route is an exit |
| Displays | Heavy assets, strong cycle | Monthly panel price (WitsView, Sigmaintell, Omdia) | Depreciation is the largest cost; the trough loses money |
| Communications hardware | Carrier capex | The year's capex plans from the major carriers | Geopolitics |
| Automotive electronics | Penetration | Design wins and penetration | AEC-Q100 takes years. A consumer supplier does not become automotive on a press release |

## Red lines

| # | Line |
| --- | --- |
| 1 | Compliance. Do not ask for or seek non-public earnings, unannounced orders, or unannounced deals. Conclusions rest on public information and industry common sense |
| 2 | Cycle valuation runs backwards. Do not buy a cycle name on a low PE at the peak (memory and panels look cheapest when earnings are best). Do not sell on a high PE at the trough. The buy is when PE is highest. The sell is when PE is lowest |
| 3 | No straight-line extrapolation, at the peak or at the trough |
| 4 | One source is not enough, especially the company's own. Two or three independent sources |
| 5 | Do not adopt the company's TAM. The reachable market can be a tenth of the slide |
| 6 | Hardware is manufacturing. Numbers that look too good are not a result until the fraud screen has been run. A full note runs that screen in a later phase. A one-question note names the trap on this card and does not pretend the seven signals were ticked |

## FAQ

**A quick judgment — do I walk all six steps?** No. Fetching is still required. That is the one-question mode.

**A number is missing. Can the report still go out?** Yes, if the gap is **unavailable** with the three-part reason, and the completion line says the note has no decision weight until that gap is filled. Naming the gap is not the same as filling it.

**Why a source on every number?** One source is not enough. A number without a source is not a number.

**Are the company names in the sector files recommendations?** No. They illustrate the business model of that link.

**Must the report follow one skeleton?** Full and report-only, yes, so notes can be compared. One question uses the six-part skeleton. Both skeletons are in the report contract, which arrives at the write phase.

**Can I use only the question bank?** Only after the verification phase names it. It is not this phase.
