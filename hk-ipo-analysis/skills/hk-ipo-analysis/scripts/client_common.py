#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

HERE_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if HERE_SCRIPTS not in sys.path:
    sys.path.insert(0, HERE_SCRIPTS)
if os.path.dirname(HERE_SCRIPTS) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE_SCRIPTS))

import os_compat
from fintrust_gate import find_api_key, require_activation
from fintrust_gate.activation_gate import service_url

SKILL_ROOT = os_compat.skill_root()
SCRIPT_DIR = os_compat.skill_root() / "scripts"

DEFAULT_TIMEOUT = 30
ALLOWED_TOOLS = frozenset({
    "ipo_list",
    "market_snapshot",
    "ipo_dify_report",
    "deep_profile",
    "news_catalysts",
})

_URL_STOP = frozenset(" \t\n\r)\"'")

class McpToolError(RuntimeError):
    pass

def redact_signed_urls(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        http = text.find("http://", i)
        https = text.find("https://", i)
        starts = [p for p in (http, https) if p >= 0]
        if not starts:
            out.append(text[i:])
            break
        start = min(starts)
        out.append(text[i:start])
        end = start
        while end < n and text[end] not in _URL_STOP:
            end += 1
        url = text[start:end]
        q = url.find("?")
        out.append((url[:q] + "?…") if q >= 0 else url)
        i = end
    return "".join(out)

_PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
_mcp_rpc_id = 0
_mcp_rpc_id_lock = threading.Lock()

def clear_local_proxies() -> None:
    for key in _PROXY_ENV_KEYS:
        os.environ.pop(key, None)

clear_local_proxies()

def load_skill_env() -> None:
    clear_local_proxies()
    env_path = SKILL_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key in _PROXY_ENV_KEYS or key == "FINTRUST_API_KEY":
            continue
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))
    clear_local_proxies()

def auth_headers(key: str) -> dict:
    return {"X-Api-Key": key}

def mcp_url() -> str:
    raw = (os.environ.get("FINTRUST_MCP_URL") or "").strip().strip('"').strip("'")
    if raw:
        return raw.rstrip("/")
    return f"{service_url().rstrip('/')}/mcp"

def _next_rpc_id() -> int:
    global _mcp_rpc_id
    with _mcp_rpc_id_lock:
        _mcp_rpc_id += 1
        return _mcp_rpc_id

def _raise_http_error(status: int, detail: str) -> None:
    try:
        from fintrust_gate.activation_gate import guide_url

        guide_hint = f"Get an fsk_ key from the signup page: {guide_url()}"
    except Exception as e:
        guide_hint = str(e)
    if status == 401:
        print(detail or f"API key missing or rejected. {guide_hint}", file=sys.stderr)
        raise SystemExit(4)
    if status == 503:
        print(detail or "The API key check is unavailable. Try again later", file=sys.stderr)
        raise SystemExit(5)
    if status == 429:
        print(detail or "The quota is used up. Try again tomorrow.", file=sys.stderr)
        raise SystemExit(5)
    if status in (404, 410):
        print(detail or "MCP endpoint unavailable", file=sys.stderr)
        raise SystemExit(5)
    raise McpToolError(detail or f"Service error (HTTP {status})")

def _parse_http_detail(text: str) -> str:
    try:
        data = json.loads(text or "")
    except (ValueError, TypeError):
        return (text or "")[:200]
    if isinstance(data, dict):
        if data.get("detail"):
            return str(data["detail"])
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
    return (text or "")[:200]

def _extract_jsonrpc_payload(text: str, content_type: str) -> dict:
    if "text/event-stream" in (content_type or "").lower() or text.lstrip().startswith("event:"):
        for line in text.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if not chunk:
                    continue
                try:
                    obj = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict) and ("result" in obj or "error" in obj):
                    return obj
        print("MCP SSE response could not be parsed", file=sys.stderr)
        raise SystemExit(1)
    try:
        obj = json.loads(text)
    except ValueError:
        print("MCP response is not valid JSON", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(obj, dict):
        print("MCP response has an unexpected shape", file=sys.stderr)
        raise SystemExit(1)
    return obj

_RETRYABLE_HTTP = frozenset({500, 502, 503, 504})
_MAX_HTTP_RETRIES = 3

def _post_once(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, str, str]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST", headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    opener.addheaders = []
    try:
        with opener.open(request, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            return status, resp.read().decode("utf-8", errors="replace"), resp.headers.get("content-type") or ""
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        content_type = (e.headers.get("content-type") if e.headers else "") or ""
        return int(e.code), body_text, content_type
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise ConnectionError(str(reason)) from e

def _post_with_retry(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, str, str]:
    last_err: BaseException | None = None
    for attempt in range(_MAX_HTTP_RETRIES):
        clear_local_proxies()
        try:
            status, text, content_type = _post_once(url, body, headers, timeout)
        except ConnectionError as e:
            last_err = e
        else:
            if status not in _RETRYABLE_HTTP or attempt + 1 >= _MAX_HTTP_RETRIES:
                return status, text, content_type
            last_err = None
        if attempt + 1 < _MAX_HTTP_RETRIES:
            time.sleep(0.8 * 2**attempt)
    print(f"The service is unreachable. Check the network and retry.({last_err})", file=sys.stderr)
    raise SystemExit(5)

def mcp_rpc(method: str, params: dict | None = None, *, timeout: float = DEFAULT_TIMEOUT):
    require_activation()
    key, _ = find_api_key()
    url = mcp_url()
    headers = {
        **auth_headers(key),
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    body = {"jsonrpc": "2.0", "method": method, "id": _next_rpc_id()}
    if params is not None:
        body["params"] = params
    status, text, content_type = _post_with_retry(url, body, headers, timeout)
    if status != 200:
        _raise_http_error(status, _parse_http_detail(text))
    payload = _extract_jsonrpc_payload(text, content_type)
    if payload.get("error"):
        err = payload["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        data = err.get("data") if isinstance(err, dict) else None
        detail = f"{msg}" + (f": {data}" if data else "")
        if "额度" in detail or "quota" in detail.lower():
            print(detail, file=sys.stderr)
            raise SystemExit(5)
        print(detail or "MCP call failed", file=sys.stderr)
        raise SystemExit(1)
    return payload.get("result")

def mcp_tool_text(name: str, arguments: dict | None = None, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    if name not in ALLOWED_TOOLS:
        raise McpToolError(f"Calling MCP tool {name!r} is not allowed: this skill only allows {sorted(ALLOWED_TOOLS)}")
    result = mcp_rpc("tools/call", {"name": name, "arguments": arguments or {}}, timeout=timeout)
    if not isinstance(result, dict):
        print(f"MCP tools/call {name} returned an error", file=sys.stderr)
        raise SystemExit(1)
    if result.get("isError"):
        contents = result.get("content") or []
        bits = [str(c["text"]) for c in contents if isinstance(c, dict) and c.get("text")]
        detail = redact_signed_urls("; ".join(bits) or f"Tool error: {name}")
        print(detail, file=sys.stderr)
        raise McpToolError(detail)
    contents = result.get("content") or []
    for c in contents:
        if isinstance(c, dict) and c.get("type", "text") == "text" and ("text" in c):
            return str(c["text"])
    print(f"MCP tools/call {name} returned no text content", file=sys.stderr)
    raise SystemExit(1)

def mcp_tool_json(name: str, arguments: dict | None = None, *, timeout: float = DEFAULT_TIMEOUT) -> dict:
    text = mcp_tool_text(name, arguments, timeout=timeout)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"MCP tool {name} returned non-JSON: {text[:200]}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(data, dict):
        print(f"MCP tool {name} returned a non-object", file=sys.stderr)
        raise SystemExit(1)
    return data

def norm_ipo_code(code: str) -> str:
    alnum = "".join(ch for ch in str(code or "").lower() if ch.isalnum())
    if not alnum:
        return ""
    digits = alnum[2:] if alnum.startswith("hk") else alnum
    if digits.isdigit():
        return f"hk{digits.zfill(5)}"
    return alnum

def unwrap_capability(data: dict):
    if data.get("ok") is False:
        raise RuntimeError(redact_signed_urls(str(data.get("error") or "Capability call failed")))
    inner = data.get("result", data)
    if isinstance(inner, str):
        try:
            inner = json.loads(inner)
        except json.JSONDecodeError:
            return inner
    if isinstance(inner, dict):
        if str(inner.get("report") or "").strip():
            return inner
        if inner.get("error"):
            raise RuntimeError(redact_signed_urls(str(inner["error"])))
    return inner

def tool_json(name: str, arguments: dict | None = None, *, timeout: float = DEFAULT_TIMEOUT) -> dict:
    try:
        return mcp_tool_json(name, arguments, timeout=timeout)
    except SystemExit as e:
        if e.code in (2, 3, 4, 5):
            raise
        raise RuntimeError(f"MCP {name} failed") from e

def emit_next(payload: dict, *, exit_code: int = 0) -> int:
    print("NEXT_ACTION_JSON " + json.dumps(payload, ensure_ascii=False), flush=True)
    return exit_code
