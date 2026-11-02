from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from os_compat import setup_console, skill_root

DEFAULT_SERVICE_URL = 'https://aiapi.fosunhanig.com/ai-mcp-research'
DEFAULT_GUIDE_URL = 'https://fintrustskill.com/landing?action=api-key'
ENV_KEY = 'FINTRUST_API_KEY'
ENV_SERVICE_URL = 'FINTRUST_SERVICE_URL'
ENV_VERIFY_URL = 'FINTRUST_VERIFY_URL'
ENV_GUIDE_URL = 'FINTRUST_GUIDE_URL'
ENV_MCP_URL = 'FINTRUST_MCP_URL'
_DOTENV_LOADED = False
_FSK_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')

class GuideUrlError(RuntimeError):
    pass

def _clean_base_url(value: str) -> str:
    value = (value or '').strip().strip('"').strip("'")
    if not value:
        return ''
    if '#' in value or '?' in value:
        return value
    return value.rstrip('/')

def _load_skill_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    env_path = SERVICE_ENV_PATH
    if not env_path.is_file():
        env_path = skill_root() / '.env.example'
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in (ENV_SERVICE_URL, ENV_VERIFY_URL, ENV_GUIDE_URL, ENV_MCP_URL) and value:
            os.environ.setdefault(key, value)

def guide_url() -> str:
    _load_skill_dotenv()
    value = _clean_base_url(os.getenv(ENV_GUIDE_URL) or '')
    if not value:
        for path, _ in _candidate_env_paths():
            if not path.is_file():
                continue
            value = _clean_base_url(_parse_env_file(path).get(ENV_GUIDE_URL, ''))
            if value:
                break
    if not value:
        return DEFAULT_GUIDE_URL
    if not value.startswith(('http://', 'https://')):
        raise GuideUrlError(f'{ENV_GUIDE_URL} is invalid (it must be a full http/https URL): {value}')
    return value

def guide_text() -> str:
    url = guide_url()
    return (f'A FinSkillHub API key is required.\n\n'
            f'1. Open the signup page and sign in:\n   [{url}]({url})\n'
            f'   Choose Get API Key and copy the `fsk_…` key.\n'
            f'2. Set `{ENV_KEY}` in the bot secret store (Grok Bot: Settings -> Secrets) so it arrives as an environment variable, or save it into this file yourself (create the folder if it is missing):\n'
            f'   {SERVICE_ENV_PATH}\n'
            f'   one line: {ENV_KEY}=<your key>\n'
            f'3. Say when it is saved; I re-check and continue.\n\n'
            f'Until the key is saved, this request stops.')

def service_url() -> str:
    _load_skill_dotenv()
    value = _clean_base_url(os.getenv(ENV_SERVICE_URL) or '')
    if value:
        return value
    for path, _ in _candidate_env_paths():
        if not path.is_file():
            continue
        value = _clean_base_url(_parse_env_file(path).get(ENV_SERVICE_URL, ''))
        if value:
            return value
    return DEFAULT_SERVICE_URL

def verify_url() -> str:
    _load_skill_dotenv()
    value = _clean_base_url(os.getenv(ENV_VERIFY_URL) or '')
    if value:
        return value
    for path, _ in _candidate_env_paths():
        if not path.is_file():
            continue
        value = _clean_base_url(_parse_env_file(path).get(ENV_VERIFY_URL, ''))
        if value:
            return value
    return service_url()

def _parse_env_file(path: Path) -> dict:
    values: dict = {}
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values

SERVICE_NAME = 'fintrust-skill-hub'
SERVICE_HOME_DIR = Path.home() / '.workbuddy' / SERVICE_NAME
SERVICE_ENV_PATH = SERVICE_HOME_DIR / '.env'


def _candidate_env_paths() -> list:
    candidates = []
    explicit = (os.getenv('FINTRUST_ENV_FILE') or '').strip()
    if explicit:
        candidates.append((Path(explicit), 'fintrust-env-file'))
    if SERVICE_ENV_PATH.is_file():
        candidates.append((SERVICE_ENV_PATH, 'service-env'))
    template = skill_root() / '.env.example'
    if template.is_file():
        candidates.append((template, 'skill-env-template'))
    return candidates

def find_api_key() -> tuple:
    _load_skill_dotenv()
    value = (os.getenv(ENV_KEY) or '').strip().strip('"').strip("'")
    if value:
        return (value, 'process-env')
    for path, source in _candidate_env_paths():
        if not path.is_file():
            continue
        value = _parse_env_file(path).get(ENV_KEY, '').strip()
        if value:
            return (value, source)
    return ('', '')

def is_fsk_key(key: str) -> bool:
    value = key.strip() if key else ''
    payload = value[4:] if value.startswith('fsk_') else ''
    return len(payload) >= 20 and all((char in _FSK_CHARS for char in payload))

def _default_env_target() -> Path:
    target = SERVICE_ENV_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        template = skill_root() / '.env.example'
        if template.is_file():
            try:
                target.write_text(template.read_text(encoding='utf-8'), encoding='utf-8')
            except OSError:
                pass
    target.parent.mkdir(parents=True, exist_ok=True)
    return target

def _upsert_env_key(path: Path, key_name: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding='utf-8').splitlines() if path.is_file() else []
    new_lines: list[str] = []
    found = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            new_lines.append(line)
            continue
        name, _, _ = stripped.partition('=')
        if name.strip() == key_name:
            new_lines.append(f'{key_name}={value}')
            found = True
        else:
            new_lines.append(line)
    if not found:
        if new_lines and new_lines[-1].strip():
            new_lines.append('')
        new_lines.append(f'{key_name}={value}')
    path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')

def normalize_pasted_key(raw: str) -> str:
    text = (raw or '').strip().strip('"').strip("'")
    if not text:
        return ''
    for token in text.replace('\n', ' ').split():
        candidate = token.strip().strip('"').strip("'").rstrip('.,;，。；')
        if is_fsk_key(candidate):
            return candidate
    return ''

def save_api_key(key: str, target: Path | None=None) -> Path:
    normalized = normalize_pasted_key(key)
    if not normalized:
        raise ValueError('The key must be a FinSkillHub fsk_ key. Copy it from the signup page and paste it here')
    path = target or _default_env_target()
    _upsert_env_key(path, ENV_KEY, normalized)
    return path

def _http_json(method: str, url: str, *, headers: dict | None=None, timeout: float=15.0) -> tuple[int, dict | str]:
    method = method.upper()
    data = b'' if method in ('POST', 'PUT', 'PATCH') else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    opener.addheaders = []
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            status = getattr(resp, 'status', 200) or 200
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        status = e.code
    except urllib.error.URLError as e:
        raise ConnectionError(str(e.reason if hasattr(e, 'reason') else e)) from e
    try:
        return (status, json.loads(body) if body else {})
    except json.JSONDecodeError:
        return (status, body)

def probe_api_key(key: str, base: str | None=None) -> dict:
    if not is_fsk_key(key):
        return {'ok': False, 'exit_code': 3, 'reason': 'the key is malformed (it needs the fsk_ prefix)'}
    url = f"{(base or verify_url()).rstrip('/')}/v1/keys/verify"
    try:
        status, payload = _http_json('GET', url, headers={'X-Api-Key': key})
    except ConnectionError as e:
        return {'ok': False, 'exit_code': 5, 'reason': f'key check service unreachable: {e}'}
    if status == 200 and isinstance(payload, dict) and (payload.get('ok') is True):
        return {'ok': True, 'status': 200, 'quota': payload.get('quota') or {}, 'key_prefix': payload.get('key_prefix') or key[:12]}
    if status == 401:
        detail = ''
        if isinstance(payload, dict):
            detail = str(payload.get('detail') or '')
        return {'ok': False, 'exit_code': 4, 'status': 401, 'reason': detail or 'the API key is invalid or missing'}
    if status == 503:
        detail = ''
        if isinstance(payload, dict):
            detail = str(payload.get('detail') or '')
        return {'ok': False, 'exit_code': 5, 'status': 503, 'reason': detail or 'The API key check is unavailable. Try again later'}
    return {'ok': False, 'exit_code': 5, 'status': status, 'reason': f'the key probe failed with HTTP {status}'}

_ACTIVATION: dict | None = None

def _probe_activation() -> dict:
    svc = service_url()
    ver = verify_url()
    try:
        url = guide_url()
    except GuideUrlError as e:
        err = str(e)
        return {'activated': False, 'exit_code': 2, 'reason': err, 'guide_url': '', 'guide': err, 'service_url': svc, 'verify_url': ver}
    key, source = find_api_key()
    if not key:
        return {'activated': False, 'exit_code': 3, 'reason': f'{ENV_KEY} is not set or is empty', 'guide_url': url, 'guide': guide_text(), 'service_url': svc, 'verify_url': ver}
    if not is_fsk_key(key):
        return {'activated': False, 'exit_code': 3, 'reason': 'the key is not a FinSkillHub-issued fsk_ key (a hand-made value, or an expired ak- key)', 'guide_url': url, 'guide': guide_text(), 'service_url': svc, 'verify_url': ver}
    probe = probe_api_key(key)
    if not probe.get('ok'):
        exit_code = int(probe.get('exit_code') or 4)
        if exit_code == 4:
            guide = f'API key rejected. Open the signup page, sign in, copy a new key, and paste it here.\n[{url}]({url})'
        elif exit_code == 5:
            guide = f'The research service or key check is unavailable. Try again later.\nkey check: {ver}\nservice: {svc}'
        else:
            guide = guide_text()
        return {'activated': False, 'exit_code': exit_code, 'reason': probe.get('reason', 'verification failed'), 'guide_url': url, 'guide': guide, 'service_url': svc, 'verify_url': ver, 'probe': probe}
    return {'activated': True, 'exit_code': 0, 'source': source, 'service_url': svc, 'verify_url': ver, 'guide_url': url, 'key_prefix': probe.get('key_prefix') or key[:12], 'quota': probe.get('quota') or {}, 'probe': probe}

def check_activation(refresh: bool = False) -> dict:
    global _ACTIVATION
    if _ACTIVATION is None or refresh:
        _ACTIVATION = _probe_activation()
    return _ACTIVATION

def require_activation() -> dict:
    result = check_activation()
    if result['activated']:
        return result
    print(result.get('guide') or result.get('reason') or guide_text())
    raise SystemExit(result['exit_code'])

def ensure_activated() -> None:
    require_activation()

def main(argv: list | None = None) -> int:
    setup_console()
    parser = argparse.ArgumentParser(description='FinTrust activation gate (/v1/keys/verify)')
    parser.add_argument('--guide', action='store_true', help='print the signup guide for the user only')
    parser.add_argument('--set-key', metavar='KEY', help='write the pasted fsk_ key into FINTRUST_API_KEY and probe /v1/keys/verify')
    parser.add_argument('--json', action='store_true', help='print structured JSON (for automation and debugging; the default output is for a human)')
    args = parser.parse_args(argv)
    if args.guide:
        print(guide_text())
        return 0
    if args.set_key is not None:
        try:
            path = save_api_key(args.set_key)
        except ValueError as e:
            print(json.dumps({'ok': False, 'exit_code': 3, 'error': str(e)}, ensure_ascii=False))
            return 3
        result = check_activation(refresh=True)
        if args.json:
            print(json.dumps({'ok': bool(result.get('activated')), 'exit_code': result['exit_code'], 'saved_to': str(path), 'env_key': ENV_KEY, 'activation': result}, ensure_ascii=False))
        else:
            print(_human_result(result, saved_to=path))
        return result['exit_code']
    result = check_activation()
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(_human_result(result))
    return result['exit_code']

def _human_result(result: dict, *, saved_to=None) -> str:
    if not result.get('activated'):
        return result.get('guide') or result.get('reason') or guide_text()
    prefix = result.get('key_prefix') or ''
    quota = result.get('quota') or {}
    tail = f' saved_to={saved_to}' if saved_to else ''
    quota_text = json.dumps(quota, ensure_ascii=False) if quota else '(not reported)'
    return f'[gate] activated key={prefix} quota={quota_text}{tail}'

if __name__ == '__main__':
    sys.exit(main())
