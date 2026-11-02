# Fetch checklist

This phase also names the house catalog. Read that file for the substitute when a host does not answer. Do not open any other file.

Skipping the fetch leaves a complete skeleton and empty numbers. `WebSearch` then `WebFetch` is the default, not an optional extra.

Stop at the first layer that works:

1. Figures the user already gave → use them and name the source.
2. `WebSearch` for the lead, then `WebFetch` for the page. Every key field needs **at least two independent sources**.
3. Still missing after a real search → label it **unavailable**, with where you looked, why it is not public, and a substitute metric. Do not invent a number. Do not write "not yet fetched". That phrase means the search was skipped, and the delivery is rejected.

If the network is actually down, say so in the first line of the report and state the completion rate. Do not pretend the fetch happened.

## The 26 fields

This list is the only completion score. Each row is either a sourced figure or an **unavailable** mark. "Not yet fetched" does not count.

A full study accounts for all 26. A one-question study accounts for every row the question actually needs, and at least one.

| # | Section | Field | Query shape | Source type |
| --- | --- | --- | --- | --- |
| 1 | Cycle | Penetration, life-cycle band | "<vertical> penetration" | Third-party house |
| 2 | Cycle | Price or utilization | "<link> price latest" | Association or third party |
| 3 | TAM | Downstream units or market size | "<vertical> market size forecast" | IDC, Canalys, TrendForce |
| 4 | TAM | Content per unit | "<product> content per unit" | Chain work. Often unavailable |
| 5 | Structure | Gross margin by link | "<link> gross margin" | Company filings |
| 6 | Structure | The tight link | "<link> capacity gap" | Industry notes |
| 7 | Structure | CR3 / CR5 | "<link> share ranking" | Third party |
| 8 | Technology | R&D amount and ratio | "<company> R&D" | Annual report |
| 9 | Technology | Patents or a milestone | "<company> patents" | Annual report, conferences |
| 10 | Customers | Top-five customer share | "<company> customer concentration" | Annual report |
| 11 | Cost | Gross margin, utilization, yield | "<company> gross margin utilization" | Filings, checks |
| 12 | Management | Auditor and opinion | "<company> auditor opinion" | Annual report |
| 13 | Management | Pledges and disposals | "<company> pledge disposal" | Exchange filing |
| 14 | Tracking | Metric 1 from the sector card | "<link> <metric> latest" | The metric named in the playbook sector card |
| 15 | Tracking | Metric 2 | same | same |
| 16 | Tracking | Operating cash flow versus net income, receivables | "<company> cash flow receivables" | Filings |
| 17 | Consensus | EPS, target, rating | "<company> target rating" | Broker notes |
| 18 | Consensus | Actual versus that consensus | compute from 8 and 11 | — |
| 19 | Fraud 1 | Gross margin versus peers | compute from 5 | — |
| 20 | Fraud 2 | Cash and interest-bearing debt together | "<company> cash debt" | Annual report |
| 21 | Fraud 3 | Receivables and inventory versus profit | "<company> receivables inventory" | Filings |
| 22 | Fraud 4 | Operating cash flow versus net income | compute from 16 | — |
| 23 | Fraud 5 | Auditor changes | from 12 plus prior years | — |
| 24 | Fraud 6 | Pledge ratio, disposal size and price | from 13 | — |
| 25 | Fraud 7 | Related-party amounts and nature | "<company> related party" | Exchange filing |
| 26 | Watch | Falsifier, observable, dated | derived from 1–25 | — |

Rows 12, 13, 20, and 25 are the ones a search skips unless you ask for them. They are the only source for the management axis and for fraud signals 2, 5, 6, and 7.

Rows 14 and 15 use the metric on the sector card you already read. Do not open another sector file to pick a second metric.

## Fetch order

1. WebSearch for leads.
2. Prefer a primary page: company filing, then an original news report, then a broker note, then a repost.
3. WebFetch the page and extract the field.
4. Check the same field on a second independent source.

Filing order, and the substitute when a host does not answer, are in the other file this phase names.

| Label | Meaning | Acceptable |
| --- | --- | --- |
| not yet fetched | The search was not done | No |
| unavailable | Searched, not public, reason given | Yes |

An unavailable mark needs three parts: where you looked, why it is not there, and the substitute.

Example: "Foundry utilization is unavailable: Samsung, SK hynix, and Micron do not disclose it. Substitute: inventory weeks. SK hynix at 4 weeks is a historical low."

## Write sources.json

Write the file at `sources_path` from this phase. Shape:

```json
{
  "items": [
    {"field": "1", "value": "…", "source": "…", "date": "YYYY-MM-DD", "url": "https://…"},
    {"field": "4", "unavailable": {"looked": "…", "why": "…", "substitute": "…"}}
  ]
}
```

A full study needs 26 accepted items. A one-question study needs at least one. An item counts when it has `value`, `source`, and `date`, or an `unavailable` object with `looked`, `why`, and `substitute`. Then run the `--mark-fetch` command this phase names.

## Completion

1. Every number traces to a company or a house, and a date.
2. Separate "not yet fetched" from "unavailable". The first means keep looking. The second needs the reason and the substitute.
3. State completion in the 26-row sense: "Completion 100%: all 26 fields are sourced or marked unavailable (4 unavailable, each with a reason and a substitute)."

100% does not mean every figure exists. It means every gap is accounted for. There is no "not yet fetched" left.

Minimum before a full report is drafted:

| Section | Fetch |
| --- | --- |
| Company | Revenue, net income, gross margin, R&D ratio, top-customer concentration |
| Tracking | The one or two metrics on the sector card |
| Consensus | Broker target, rating mix |
| Fraud screen | Receivables, inventory, operating cash flow, pledges and disposals |
