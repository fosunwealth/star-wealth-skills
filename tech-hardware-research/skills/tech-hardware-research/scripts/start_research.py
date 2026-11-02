#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Open a tech-hardware research session after the gate passes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from activation import require_api_key  # noqa: E402
import research_state as rs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="start a tech-hardware research session")
    parser.add_argument("--query", required=True, help="latest user question")
    args = parser.parse_args()
    require_api_key()
    session = rs.new_session(args.query)
    rs.save_session(session)
    phase = rs.infer_phase(session, has_key=True)
    print(json.dumps(rs.progress_payload(phase, session), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
