import json
import os
import re

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_config.json")
_CONFIG = None
_RESOLVE_CACHE = {}

def _load():
    global _CONFIG
    if _CONFIG is None:
        with open(_CONFIG_PATH) as f:
            raw = json.load(f)
        _CONFIG = raw
    return _CONFIG

def _resolve(value, paths):
    """Resolve ${var} placeholders recursively."""
    if not isinstance(value, str) or "${" not in value:
        return value
    cache_key = value
    if cache_key in _RESOLVE_CACHE:
        return _RESOLVE_CACHE[cache_key]
    resolved = re.sub(r'\$\{(\w+)\}', lambda m: str(paths.get(m.group(1), m.group(0))), value)
    # Handle nested resolution (up to 3 levels)
    for _ in range(3):
        if "${" not in resolved:
            break
        resolved = re.sub(r'\$\{(\w+)\}', lambda m: str(paths.get(m.group(1), m.group(0))), resolved)
    _RESOLVE_CACHE[cache_key] = resolved
    return resolved

def get_path(key: str) -> str:
    config = _load()
    paths = config["paths"]
    val = paths.get(key, "")
    return _resolve(val, paths)

def get_model(key: str) -> str:
    config = _load()
    return config["models"].get(key, "")

def get_timeout(key: str) -> int:
    config = _load()
    return config["timeouts"].get(key, 300)

def get_url(key: str) -> str:
    config = _load()
    return config["urls"].get(key, "")

def get_alert(key: str):
    config = _load()
    return config["alerts"].get(key)

def reload():
    """Force reload config (for testing)."""
    global _CONFIG, _RESOLVE_CACHE
    _CONFIG = None
    _RESOLVE_CACHE = {}

def get_workspace_root() -> str:
    return get_path("workspace_root")
