# Playbook

This is the only file for this phase. Do not open the rules or the payload schema until the queue names them.

## Scope

One path for a Hong Kong IPO: gate, list, HTML report, deliver one path.

| | |
| --- | --- |
| Does | Lists current Hong Kong IPOs, or builds one HTML report for a named deal (offer terms, subscription, sponsor, cornerstone, premium, valuation, fundamentals, industry, market, allotment). Objective only. |
| Does not | Does not browse, curl, or download a prospectus on its own. Does not guess a list. Does not edit this package. Does not place an order. |
| Use when | The user asks which Hong Kong IPOs are open, or names one deal. Example: "run the numbers on MINIMAX". |
| Do not use when | They want a general equity report on a listed name, or a trade. |
| Input | A list request, or a code plus name (`hk06700`). |
| Output | `list` prints the list and stops. `report` ends by handing the user the single `<code>_report.html`. |
| Limits | Python 3.8+ and Node.js. Not investment advice. |

One chain: **gate → our MCP → HTML report**.

`list` and `report` are independent. A list question runs `list` and stops. A named code or name runs `report` only. Do not `list` first. They share no state.

## At a glance

| Command | When | Result |
| --- | --- | --- |
| `list` | They only want the list | Print it and stop. Do not run report |
| `report --codes hk06700 --name <official name>` | They named one deal | Does not run list. Writes `data/<code>/<code>_report.html` |
| Delivery | The HTML exists | The chat names that one path |

## Entry

| OS | Command |
| --- | --- |
| macOS / Linux | `bash "<skill root>/run.sh" <command> [args]` |
| Windows (cmd / PowerShell) | `py -3 "<skill root>\scripts\main.py" <command> [args]` |

`<skill root>` is the directory of `SKILL.md`. Do not execute `run.sh` directly. On macOS and Linux always use `bash`. If `py` is missing, use `python`. Set `HK_PYTHON=<interpreter>` to pin one on macOS and Linux.

| Command | Role |
| --- | --- |
| `gate` | Auth check |
| `gate --set-key <key>` | Write the pasted key |
| `list` | List deals, then stop |
| `report --codes hk06700 --name <official name>` | Fetch the source text and the layer-1 truth. Writes `<code>_raw.md` / `<code>_primary.json` |
| `report … --refresh` | Refetch the source |
| `render --codes hk06700` | Check the `<code>.json` you wrote, then write `<code>_report.html` |
| `check A.html B.html` | Local structure check. No network, no key |

The receipt self-reports its version from `version:` in `SKILL.md`. If it does not match, you are running a stale copy.
