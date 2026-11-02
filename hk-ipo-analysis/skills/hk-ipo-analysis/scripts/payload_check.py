#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

__all__ = ["check", "load_schema", "SCHEMA_PATH"]

SCHEMA_PATH = Path(__file__).resolve().with_name("payload.schema.json")

_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}

def load_schema(path: Path | None = None) -> Dict[str, Any]:
    return json.loads((path or SCHEMA_PATH).read_text(encoding="utf-8"))

def _type_ok(value: Any, want: str) -> bool:
    if want == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if want == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if want == "boolean":
        return isinstance(value, bool)
    if want == "null":
        return value is None
    return isinstance(value, _JSON_TYPES[want])

def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False

def _resolve(schema: Any, root: Dict[str, Any]) -> Dict[str, Any]:
    seen = 0
    while isinstance(schema, dict) and "$ref" in schema:
        ref = str(schema["$ref"])
        if not ref.startswith("#/"):
            return schema
        node: Any = root
        for part in ref[2:].split("/"):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        schema = node
        seen += 1
        if seen > 8:
            return {}
    return schema if isinstance(schema, dict) else {}

def _walk(node: Any, schema: Any, root: Dict[str, Any], path: str,
          errors: List[str], empties: List[str]) -> None:
    schema = _resolve(schema, root)
    if not schema:
        return

    want = schema.get("type")
    if isinstance(want, list):
        ok = any(_type_ok(node, t) for t in want if isinstance(t, str))
    elif isinstance(want, str):
        ok = _type_ok(node, want)
    else:
        ok = True
    if not ok:
        errors.append(f"{path} has the wrong type: expected {want}, got {type(node).__name__}")
        return

    allowed = schema.get("enum")
    if isinstance(allowed, list) and node not in allowed:
        errors.append(f"{path} value {node!r} is not in the allowed list {allowed}")
        return

    if node is None:
        if schema.get("x-empty") != "ok":
            empties.append(path)
        return

    if isinstance(node, dict):
        for key in schema.get("required") or []:
            if key not in node:
                errors.append(f"{path}/{key} is missing")
        props = schema.get("properties") or {}
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    errors.append(f"{path}/{key} is not in the schema (extra key)")
        for key, sub in props.items():
            if key in node:
                _walk(node[key], sub, root, f"{path}/{key}", errors, empties)
        for pair in schema.get("x-same-length") or []:
            if not (isinstance(pair, list) and len(pair) == 2):
                continue
            left, right = pair
            lv, rv = node.get(left), node.get(right)
            if isinstance(lv, list) and isinstance(rv, list) and len(lv) != len(rv):
                errors.append(f"{path}/{left} length {len(lv)} does not match {path}/{right} length {len(rv)}")
        return

    if isinstance(node, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(node):
                _walk(item, item_schema, root, f"{path}[{i}]", errors, empties)
        if not node and schema.get("x-empty") != "ok":
            empties.append(path)
        return

    if _is_empty(node) and schema.get("x-empty") != "ok":
        empties.append(path)

def check(payload: Any, schema: Dict[str, Any] | None = None) -> Dict[str, Any]:
    root = schema or load_schema()
    errors: List[str] = []
    empties: List[str] = []
    _walk(payload, root, root, "$", errors, empties)
    return {"ok": not errors and not empties, "errors": errors, "empties": empties}

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("usage: payload_check.py [--json] <payload.json>", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(paths[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"ok": False, "errors": [f"payload could not be read: {exc}"], "empties": []}
    else:
        result = check(payload)
    if as_json:
        print("PAYLOAD_CHECK_JSON " + json.dumps(result, ensure_ascii=False), flush=True)
    else:
        for line in result["errors"]:
            print(f"  error {line}", flush=True)
        for line in result["empties"]:
            print(f"  empty {line} (schema marks warn: expected but missing)", flush=True)
        print("  validation passed" if result["ok"] else
              f"  is not valid: {len(result['errors'])} hard error(s), {len(result['empties'])} empty slot(s)", flush=True)
    return 0 if result["ok"] else 7

if __name__ == "__main__":
    sys.exit(main())
