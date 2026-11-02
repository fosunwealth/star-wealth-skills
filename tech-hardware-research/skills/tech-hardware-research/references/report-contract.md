# Report contract

This phase also names the HTML template. Copy that file. Do not open any other file.

Change the figures and the judgment. Do not change the sections. A missing field is **unavailable** with the three-part reason. No empty shell. No invented number.

## One question

Use this skeleton. A framework with no numbers and no conclusion is not an answer.

1. The conclusion, in one to three sentences.
2. The body, tables first, a number after each claim.
3. The one or two metrics that matter for this link, and the current reading.
4. The trap that belongs to this link, from the sector card.
5. Sources and dates.
6. Anything still missing is **unavailable** (where you looked, why, substitute). No estimates.

## Full study and report-only

```markdown
# <name> research note
> As of YYYY-MM-DD | Link: <chain step> | Data through: <date>

## Judgment in one sentence
A judgment, not a description. Name the main tension (what is tearing, or what contradicts the obvious). If none of the four tests hit, say there is no material tension.

## 1. Where it sits in the cycle
Vertical and chain step. Life-cycle band. For a cycle link, give PB, utilization, or price position. Do not anchor on PE.
TAM you calculated. Do not adopt the company's TAM.

## 2. Chain and who keeps the profit
Upstream, midstream, downstream. Who earns it, and why.
The binding constraint: physical, technical, license, brand, network, switching cost, scale, or channel.

## 3. Structure and the company
Concentration, barriers, substitutes, bargaining power.
Four axes, each 1–5 plus one sentence of evidence: technology, customers, cost, management.

## 4. The metrics that matter, and the current reading
The one to three metrics on the sector card.
Current reading, historical rank, and what it implies.

## 5. Consensus and the gap
Who says what, and what that implies.
Where it can be wrong.
Your judgment, the reason, and the direction of the gap versus consensus.

## 6. Pitfall review
Seven fraud signals, ticked. Three or more hits: stop. Do not discuss valuation.
Five cognitive traps: straight-line extrapolation, technology worship, story without orders, overconfidence, ignored downside.

## 7. What to watch, and what would prove this wrong
Each watch item has a time, a data point, and a source. Do not write "keep an eye on it".
The falsifier: which observable fact, by which date, would make this judgment wrong. Then rewrite the conclusion.

## Appendix: sources and definitions
Source, date, definition, the unavailable items, and the completion line.
```

| Section | Hard rule |
| --- | --- |
| One-sentence judgment | A judgment, and a main tension, or an explicit "no material tension" |
| Every number | Source and date, then one sentence of "so what" |
| Cycle position | No PE anchor on a cycle link |
| Four axes | 1–5 plus evidence. Any axis at 2 or below is named as a risk. An integrity or fraud history on management is a veto |
| Expectation gap | Direction versus consensus, and the falsifier |
| Watch list | Time, data, source. No "keep an eye on it" |
| Missing data | **unavailable**, with the three-part reason. Never invented |

## Finding the main tension

Do not start the one-sentence judgment until one of these hits. A forced tension is worse than none.

| Test | How | Shape |
| --- | --- | --- |
| D1 | Readings on the same name point different ways | Profit up much faster than revenue, while one customer is most of sales |
| D2 | Two sources disagree on the same fact | The company says it is full; the chain says channel inventory is high |
| D3 | Consensus and the industry fact point opposite ways | Brokers are positive while the customer's capex guide is down |
| D4 | Flows and fundamentals diverge | Fundamentals worsen and the price makes a high |

Say what is tearing, or what contradicts the obvious, and which test it is.

If none hit, write "no material tension". That is a result. Do not invent one.

## Depth

| | Full note and report-only | One question |
| --- | --- | --- |
| Completion | All 26 fields accounted for | Every field the question actually needs |
| History | At least 3 real years | 3 years when the question is about a cycle or a trend |
| Tension | Required, or an explicit "none" | Required when the question is a judgment |
| The other side | Where the consensus can be wrong | Required when there is a judgment |
| Falsifier | Observable, with a date | Required when there is a judgment |
| Visible text | 8,000–15,000 words. 8,000 is the floor | 3,000–6,000 words. 3,000 is the floor |

Visible text means the words a reader sees. Strip `style`, `script`, comments, and tags before counting. Do not count CSS.

| # | Block | Full and report-only | One question |
| --- | --- | --- | --- |
| 1 | Technology routes: how each works, the advantage, the constraint, where it fits | yes | yes |
| 2 | Competitive tiers, with the barrier and the names | yes | yes |
| 3 | Peer table, at least 5 names, gross margin and technical character | yes | partial |
| 4 | History, at least 3 years of state and readings | yes | yes |
| 5 | Bull / base / bear, each with a trigger and a probability | yes | no |
| 6 | A section on the upstream or the binding link | yes | yes |
| 7 | How to use the conclusion | yes | yes |

Below the floor means a block is missing. Add the block. Do not lengthen sentences.

Shared floor: no "not yet fetched"; every number has a source, a date, and a "so what"; one self-contained HTML file; metric cards and an inline chart.

## HTML

The deliverable is one HTML file, not Markdown. Double-click to read, safe to forward.

Copy the template this phase names and replace the placeholders. No CDN, no external CSS, JS, or images. Charts are inline SVG.

| # | Rule | Full and report-only | One question |
| --- | --- | --- | --- |
| 1 | One file, zero external resources | yes | yes |
| 2 | Inline SVG charts | 2–4 | at least 1 |
| 3 | Cards and tables | at least 4 cards and 8 tables | at least 3 cards and 2 tables |
| 4 | Source marks | at least 15 | at least 6 |
| 5 | A `.verdict` close on each section | all sections | at least the conclusion |
| 6 | Up = red, down = green | yes | yes |
| 7 | A `.toc` | yes | no |
| 8 | Responsive and printable | yes | yes |
| 9 | No script names, debug lines, or logs in the report | yes | yes |
| 10 | Skeleton | the 8 sections above | the 6-part skeleton |
| 11 | Completion | 26 fields | the fields the question needs |

Count visible text with:

```python
b = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
b = re.sub(r"<script.*?</script>", "", b, flags=re.DOTALL)
n = len(re.sub(r"\s+", "", re.sub(r"<[^>]*>", "", b)))
```

After the file is final, run the `--mark-written --report` command this phase names. The path has to be the HTML file.

## Before delivery

Do not deliver with any box open. **Full** applies to a full study and to report-only. **One question** applies to that mode. Unmarked lines apply to both.

- [ ] The report does not contain "not yet fetched"
- [ ] Key fields have at least two independent sources
- [ ] Every number has a source, a date, and a "so what"
- [ ] One HTML file, zero external resources
- [ ] Inline SVG (full: 2–4; one question: at least 1)
- [ ] Cards and tables (full: at least 4 and 8; one question: at least 3 and 2)
- [ ] Source marks (full: at least 15; one question: at least 6)
- [ ] Up is red, down is green
- [ ] No script names, debug text, or logs
- [ ] Full: all 26 fields. One question: every field the question needs
- [ ] Full: all 8 sections. One question: all 6 parts
- [ ] Full: the first sentence is a judgment and names the tension, or says there is none
- [ ] Full: at least 3 historical years. One question: the same when the question is a cycle or a trend
- [ ] Full: seven fraud signals ticked. Unticked means the note has no decision weight, and it says so
- [ ] Full: four axes scored, with evidence. A score of 2 or below is named as a risk
- [ ] Full: the gap section states the direction versus consensus and the falsifier
- [ ] Full: every watch item has time, data, and source
- [ ] Completion is stated on the matching scale
- [ ] Visible text: full 8,000–15,000; one question 3,000–6,000. The floor is a hard line
- [ ] The seven depth blocks that apply to this mode are present
- [ ] The HTML file was delivered
