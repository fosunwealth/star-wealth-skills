#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os_compat

USAGE = """hk-ipo-analysis — gate, then MCP, then one English HTML report

Usage: run.sh <command> [args]      (Windows: py -3 scripts\\main.py, same args)

Commands
  gate                     Auth check. On failure, print the signup guide and exit 3/4/5
  gate --set-key fsk_xxx   Write the key the user pasted, then verify it
  gate --guide             Print the signup guide only
  list                     List deals, then stop. Does not run report
  report --codes …         Shot 1: fetch the source text and the layer-1 truth (does not run list).
                           Example: report --codes hk06700 --name <official name> [--refresh]
                           Payload is yours: read <code>_raw.md and write <code>.json from scripts/payload.schema.json
  render --codes …         Shot 2: check that payload against the schema, then write <code>_report.html.
                           Reuses the payload on disk, never refetches the source
  check A.html B.html      Local structure check. No network, no key

Exit codes
  0 ok   2 usage   3 key missing or malformed   4 key rejected   5 service or key check unavailable
  6 data-plane failure (failures[].error is the server text)
"""

def main(argv: list[str] | None = None) -> int:
    os_compat.setup_console()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "-?", "help"}:
        print(USAGE)
        return 0

    command, rest = args[0], args[1:]

    if command in {"gate", "key", "auth"}:
        from fintrust_gate import activation_gate

        return activation_gate.main(rest)

    if command in {"check", "structure"}:
        import check_report_structure

        return check_report_structure.main(["check_report_structure.py", *rest])

    from fintrust_gate import ensure_activated

    ensure_activated()

    if command in {"list", "new", "新股"}:
        import ipo_list

        return ipo_list.main()

    if command in {"report", "ipo", "报告"}:
        import ipo

        return ipo.main(rest, stage="report")

    if command in {"render", "html", "渲染"}:
        import ipo

        return ipo.main(rest, stage="render")

    print(f"Unknown command: {command}\n\n{USAGE}", file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
