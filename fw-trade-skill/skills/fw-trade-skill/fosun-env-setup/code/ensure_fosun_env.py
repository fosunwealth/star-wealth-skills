from __future__ import annotations
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import types
from urllib.parse import quote, urlparse
import uuid
from typing import Any
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from credential_scenarios import (
 ACTION_CONTACT_SUPPORT,
 CONTACT_SUPPORT_USER_MESSAGE,
 SCENARIO_RENEW,
 SCENARIO_RESET,
 SCENARIO_SETUP,
 build_open_url,
 operation_guide,
 scenario_fields,
)
from api_key_check import (
 classify_api_key_error_code,
 parse_api_key_check_status,
)
from qr_artifact import apply_qr_delivery
SETUP_ROOT = Path(__file__).resolve().parent.parent
FW_TRADE_ROOT = SETUP_ROOT.parent
LOCAL_SDK_ROOT = FW_TRADE_ROOT / "openapi-python-sdk-develop-sim-trade"
SERVICE_HOME_DIR = Path.home() / ".workbuddy" / "star-wealth-openapi"
DEFAULT_ENV_NAME = "fosun.env"
DEFAULT_BASE_URL = "https://openapi.fosunxcz.com"
PROD_BASE_URL_HOST = "openapi.fosunxcz.com"
DEFAULT_SDK_ZIP_FALLBACK_URL = "https://openapi-docs.fosunxcz.com/download/sdk/openapi-python-sdk-1.2.0.zip"
DEFAULT_BACKUP_KEEP_COUNT = 10
VERIFY_TLS_ENV_KEY = "FSOPENAPI_VERIFY_TLS"
CA_BUNDLE_ENV_KEY = "FSOPENAPI_CA_BUNDLE"
API_KEY_STATUS_KEY = "FSOPENAPI_API_KEY_STATUS"
API_KEY_VERIFIED_AT_KEY = "FSOPENAPI_API_KEY_VERIFIED_AT"
TICKET_KEY = "FSOPENAPI_TICKET"
TICKET_STATUS_KEY = "FSOPENAPI_TICKET_STATUS"
TICKET_EXPIRE_TIME_KEY = "FSOPENAPI_TICKET_EXPIRE_TIME"
OPEN_URL_KEY = "FSOPENAPI_OPEN_URL"
MAC_ID_KEY = "FSOPENAPI_MAC_ID"
API_KEY_KEY = "FSOPENAPI_API_KEY"
BASE_URL_KEY = "FSOPENAPI_BASE_URL"
PRIVATE_KEY_KEY = "FSOPENAPI_CLIENT_PRIVATE_KEY"
SERVER_PUBLIC_KEY_KEY = "FSOPENAPI_SERVER_PUBLIC_KEY"
ACCOUNT_INDEX_KEY = "FSOPENAPI_ACCOUNT_INDEX"
BACKUP_DIR_ENV_KEY = "FOSUN_ENV_BACKUP_DIR"
PENDING_STATE_VERSION = 1
_TRANSIENT_AUTH_KEYS = {
 TICKET_KEY,
 TICKET_STATUS_KEY,
 TICKET_EXPIRE_TIME_KEY,
 OPEN_URL_KEY,
 MAC_ID_KEY,
}
_TICKET_BINDING_KEYS = (
 TICKET_KEY,
 TICKET_STATUS_KEY,
 TICKET_EXPIRE_TIME_KEY,
 OPEN_URL_KEY,
)
_KEEP_FOR_FRESH_TICKET = frozenset({PRIVATE_KEY_KEY, MAC_ID_KEY, BASE_URL_KEY})
_CANONICAL_ENV_KEYS = {
 ACCOUNT_INDEX_KEY,
 API_KEY_KEY,
 API_KEY_STATUS_KEY,
 API_KEY_VERIFIED_AT_KEY,
 BASE_URL_KEY,
 CA_BUNDLE_ENV_KEY,
 PRIVATE_KEY_KEY,
 SERVER_PUBLIC_KEY_KEY,
 VERIFY_TLS_ENV_KEY,
}
_PEM_WRAPPERS = {
 PRIVATE_KEY_KEY: ("-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----"),
 SERVER_PUBLIC_KEY_KEY: ("-----BEGIN PUBLIC KEY-----", "-----END PUBLIC KEY-----"),
}
_ACCOUNT_TYPE_LABELS = {
 0: "real_stock",
 1: "real_option",
 2: "mock",
}
def shared_env_path():
 a = (os.environ.get("FOSUN_ENV_PATH") or DEFAULT_ENV_NAME).strip()
 b = Path(os.path.expandvars(os.path.expanduser(a)))
 if not b.is_absolute():
  b = SERVICE_HOME_DIR / b
 return b.resolve()
def _parse_env_file(text):
 a: dict[str, str] = {}
 b = text.splitlines()
 c = 0
 while c < len(b):
  d = b[c].strip()
  if not d or d.startswith("#"):
   c += 1
   continue
  e, f, g = d.partition("=")
  if not f:
   c += 1
   continue
  e = e.strip()
  g = g.strip()
  if g.startswith("-----BEGIN "):
   h = [g]
   c += 1
   while c < len(b):
    i = b[c].rstrip()
    h.append(i)
    if i.strip().startswith("-----END "):
     c += 1
     break
    c += 1
   g = "\n".join(h)
  elif g.startswith('"') and not g.endswith('"'):
   j = [g[1:]]
   c += 1
   while c < len(b):
    k = b[c]
    if k.endswith('"'):
     j.append(k[:-1])
     c += 1
     break
    j.append(k)
    c += 1
   g = "\n".join(j)
  else:
   if g.startswith('"') and g.endswith('"'):
    g = g[1:-1]
   c += 1
  if e:
   a[e] = g
 return a
def _ensure_pem(key_name, value):
 value = str(value or "").strip()
 if not value or value.startswith("-----BEGIN "):
  return value
 a = _PEM_WRAPPERS.get(key_name)
 if not a:
  return value
 try:
  b = base64.b64decode(value).decode("utf-8")
  if b.strip().startswith("-----BEGIN "):
   return b.strip()
 except Exception:
  pass
 c, d = a
 e = value.replace("\n", "").replace("\r", "").replace(" ", "")
 f = [e[g:g + 64] for g in range(0, len(e), 64)]
 return c + "\n" + "\n".join(f) + "\n" + d
def _encode_env_value(key, value):
 if value is None:
  return ""
 value = str(value).strip()
 if key in _PEM_WRAPPERS and value.startswith("-----BEGIN "):
  return base64.b64encode(value.encode("utf-8")).decode("utf-8")
 return value
def coerce_prod_base_url(value):
 a = str(value or "").strip().rstrip("/")
 if not a:
  return DEFAULT_BASE_URL, False
 if (urlparse(a).hostname or "") == PROD_BASE_URL_HOST:
  return a, False
 return DEFAULT_BASE_URL, True
def load_env_entries(env_path = None):
 a = env_path or shared_env_path()
 if not a.is_file():
  return {}
 b = _parse_env_file(a.read_text(encoding="utf-8"))
 if b.get(BASE_URL_KEY):
  b[BASE_URL_KEY], c = coerce_prod_base_url(b[BASE_URL_KEY])
  if c:
   print(
    f"[fw-trade] this skill only uses PROD: {a} contained a non-PROD gateway, which was pulled back to {DEFAULT_BASE_URL}",
    file=sys.stderr,
   )
 return b
def _pending_state_path(env_path):
 return env_path.with_name(f".{env_path.name}.pending.json")
def _read_pending_document(env_path):
 a = _pending_state_path(env_path)
 if not a.is_file():
  return {}
 try:
  b = json.loads(a.read_text(encoding="utf-8"))
 except (OSError, ValueError):
  return {}
 return b if isinstance(b, dict) else {}
def _load_pending_state(env_path):
 a = _read_pending_document(env_path)
 b = a.get("entries")
 if not isinstance(b, dict):
  return {}
 c = {str(e): f for e, f in b.items()}
 if c.get(API_KEY_KEY):
  d = _sanitize_api_key(c[API_KEY_KEY])
  if d:
   c[API_KEY_KEY] = d
  else:
   c.pop(API_KEY_KEY, None)
 return c
_PENDING_CREDENTIAL_KEYS = (
 BASE_URL_KEY,
 PRIVATE_KEY_KEY,
 SERVER_PUBLIC_KEY_KEY,
)
def _merge_pending_credentials_into_entries(
 entries,
 env_path,
 *,
 user_api_key = None,
 overwrite_from_pending = False,
):
 a = _load_pending_state(env_path)
 if not a:
  return False
 for b in _PENDING_CREDENTIAL_KEYS:
  c = a.get(b)
  if not c:
   continue
  if overwrite_from_pending or not str(entries.get(b, "") or "").strip():
   entries[b] = c
 if user_api_key:
  entries[API_KEY_KEY] = str(user_api_key).strip()
  entries[API_KEY_STATUS_KEY] = "unknown"
  entries[API_KEY_VERIFIED_AT_KEY] = ""
 return True
def _save_pending_state(
 entries,
 env_path,
 *,
 ticket,
 open_url,
 expire_time,
 credential_scenario = SCENARIO_SETUP,
):
 a = _pending_state_path(env_path)
 a.parent.mkdir(parents=True, exist_ok=True)
 b = {
  BASE_URL_KEY: entries.get(BASE_URL_KEY),
  PRIVATE_KEY_KEY: _ensure_pem(PRIVATE_KEY_KEY, entries.get(PRIVATE_KEY_KEY)),
  API_KEY_KEY: entries.get(API_KEY_KEY),
  SERVER_PUBLIC_KEY_KEY: _ensure_pem(
   SERVER_PUBLIC_KEY_KEY,
   entries.get(SERVER_PUBLIC_KEY_KEY),
  ),
  API_KEY_STATUS_KEY: "pending",
  API_KEY_VERIFIED_AT_KEY: "",
  TICKET_KEY: ticket,
  TICKET_STATUS_KEY: entries.get(TICKET_STATUS_KEY, "active"),
  OPEN_URL_KEY: open_url,
  TICKET_EXPIRE_TIME_KEY: expire_time,
  MAC_ID_KEY: entries.get(MAC_ID_KEY),
 }
 c = {
  "version": PENDING_STATE_VERSION,
  "createdAt": _now_ts(),
  "credential_scenario": credential_scenario,
  "entries": b,
 }
 a.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
 try:
  a.chmod(0o600)
 except OSError:
  pass
def _delete_pending_state(env_path):
 try:
  _pending_state_path(env_path).unlink()
 except FileNotFoundError:
  pass
def _write_api_key_to_pending(env_path, api_key):
 a = _pending_state_path(env_path)
 if not a.is_file():
  return False
 b = _read_pending_document(env_path)
 c = b.get("entries")
 if not isinstance(c, dict):
  return False
 c[API_KEY_KEY] = api_key
 c[API_KEY_STATUS_KEY] = "unknown"
 c[API_KEY_VERIFIED_AT_KEY] = ""
 b["entries"] = c
 a.write_text(
  json.dumps(b, ensure_ascii=False, indent=2),
  encoding="utf-8",
 )
 try:
  a.chmod(0o600)
 except OSError:
  pass
 return True
def _apply_user_api_key_backfill(
 env_path,
 api_key,
 *,
 server_public_key,
):
 a = _ensure_pem(
  SERVER_PUBLIC_KEY_KEY,
  str(server_public_key or "").strip(),
 )
 if not a:
  raise ValueError(
   "When writing back the credentials of an already-activated account you must also provide the server public key shown on the page (--server-public-key). The server "
   "public key displayed on the page differs from the one TicketCreate returned temporarily, and supplying only the apikey cannot complete the integration."
  )
 b = load_env_entries(env_path)
 c = _merge_pending_credentials_into_entries(
  b,
  env_path,
  user_api_key=api_key,
  overwrite_from_pending=True,
 )
 b[SERVER_PUBLIC_KEY_KEY] = a
 if not _has_complete_key_material(b):
  raise RuntimeError(
   "The client private key in the pending state is missing, or the server public key cannot be parsed, so the credential cannot be "
   "written. Run ensure_fosun_env.py first to issue the activation QR code; after the user finishes the reset on the page, write back the "
   "API Key and the server public key from the page together."
  )
 _drop_transient_auth_entries(b)
 save_env_entries(b, env_path)
 if not _write_api_key_to_pending(env_path, api_key):
  raise RuntimeError(
   "Cannot write the pending state: .fosun.env.pending.json is missing or its content is invalid. Run "
   "ensure_fosun_env.py first to issue the activation QR code, then write the API Key back."
  )
 return b, c
def _canonicalize_env_entries(entries):
 a = {b: entries.get(b) for b in _CANONICAL_ENV_KEYS if b in entries}
 a.setdefault(BASE_URL_KEY, DEFAULT_BASE_URL)
 a.setdefault(API_KEY_STATUS_KEY, "unknown")
 a.setdefault(API_KEY_VERIFIED_AT_KEY, "")
 return a
def save_env_entries(entries, env_path = None):
 a = env_path or shared_env_path()
 a.parent.mkdir(parents=True, exist_ok=True)
 entries = _canonicalize_env_entries(entries)
 b = {
  e: _encode_env_value(e, f)
  for e, f in entries.items()
  if f is not None
 }
 c = a.with_name(f".{a.name}.tmp.{os.getpid()}")
 try:
  with c.open("w", encoding="utf-8") as d:
   for e in sorted(b.keys()):
    d.write(f"{e}={b[e]}\n")
  os.replace(c, a)
 finally:
  try:
   c.unlink()
  except FileNotFoundError:
   pass
def credential_backup_dir():
 a = (os.environ.get(BACKUP_DIR_ENV_KEY) or "").strip()
 if a:
  b = Path(os.path.expandvars(os.path.expanduser(a)))
 elif os.name == "nt":
  c = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
  b = Path(c) / "fw-trade-skill" / "fosun-env-backups"
 elif sys.platform == "darwin":
  b = Path.home() / "Library" / "Application Support" / "fw-trade-skill" / "fosun-env-backups"
 else:
  c = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
  b = Path(c) / "fw-trade-skill" / "fosun-env-backups"
 if not b.is_absolute():
  b = Path.home() / b
 return b.resolve()
def _backup_file_stem(entries):
 a = str(entries.get(BASE_URL_KEY) or DEFAULT_BASE_URL).strip().rstrip("/")
 b = _sanitize_api_key(entries.get(API_KEY_KEY))
 c = hashlib.sha256(f"{a}\n{b}".encode("utf-8")).hexdigest()[:12]
 d = b[-8:] if b else "noapikey"
 e = datetime.now().strftime("%Y%m%d-%H%M%S")
 return f"fosun-{c}-{d}-{e}"
def _prune_credential_backups(backup_dir):
 a = sorted(
  backup_dir.glob("fosun-*.env"),
  key=lambda path: path.stat().st_mtime,
  reverse=True,
 )
 for b in a[DEFAULT_BACKUP_KEEP_COUNT:]:
  try:
   b.unlink()
  except OSError:
   pass
def _persist_credential_backup(entries):
 if str(entries.get(API_KEY_STATUS_KEY, "")).strip().lower() != "valid":
  return None
 if not _sanitize_api_key(entries.get(API_KEY_KEY)) or not _has_complete_key_material(entries):
  return None
 a = credential_backup_dir()
 a.mkdir(parents=True, exist_ok=True)
 try:
  a.chmod(0o700)
 except OSError:
  pass
 b = a / f"{_backup_file_stem(entries)}.env"
 save_env_entries(entries, b)
 try:
  b.chmod(0o600)
 except OSError:
  pass
 _prune_credential_backups(a)
 return b
def _restore_candidate_paths():
 a = credential_backup_dir()
 if not a.is_dir():
  return []
 return sorted(
  a.glob("fosun-*.env"),
  key=lambda path: path.stat().st_mtime,
  reverse=True,
 )
def _drop_transient_auth_entries(entries):
 for a in _TRANSIENT_AUTH_KEYS:
  entries.pop(a, None)
def _drop_bound_credential_entries(entries):
 for a in (
  ACCOUNT_INDEX_KEY,
  API_KEY_KEY,
  API_KEY_STATUS_KEY,
  API_KEY_VERIFIED_AT_KEY,
  SERVER_PUBLIC_KEY_KEY,
 ):
  entries.pop(a, None)
def _trim_pending_for_fresh_ticket(
 pending_entries,
):
 if not pending_entries:
  return {}
 return {
  a: b
  for a, b in pending_entries.items()
  if a in _KEEP_FOR_FRESH_TICKET
 }
def _discard_stale_ticket_binding(entries):
 for a in _TICKET_BINDING_KEYS:
  entries.pop(a, None)
def _reset_pending_and_ticket(
 entries,
 pending_entries,
):
 _discard_stale_ticket_binding(entries)
 return _trim_pending_for_fresh_ticket(pending_entries)
def _mark_invalid_and_save(entries, env_path):
 entries[API_KEY_STATUS_KEY] = "invalid"
 save_env_entries(entries, env_path)
def _generate_device_id(entries):
 a = str(entries.get(MAC_ID_KEY, "")).strip()
 if not a:
  a = uuid.uuid4().hex
  entries[MAC_ID_KEY] = a
 return a
def _generate_client_key_pair():
 a = ec.generate_private_key(ec.SECP384R1())
 b = a.private_bytes(
  encoding=serialization.Encoding.PEM,
  format=serialization.PrivateFormat.PKCS8,
  encryption_algorithm=serialization.NoEncryption(),
 ).decode("utf-8").strip()
 c = a.public_key().public_bytes(
  encoding=serialization.Encoding.PEM,
  format=serialization.PublicFormat.SubjectPublicKeyInfo,
 ).decode("utf-8").strip()
 return b, c
def _derive_public_key(private_key_pem):
 a = serialization.load_pem_private_key(
  private_key_pem.encode("utf-8"),
  password=None,
 )
 b = a.public_key()
 return b.public_bytes(
  encoding=serialization.Encoding.PEM,
  format=serialization.PublicFormat.SubjectPublicKeyInfo,
 ).decode("utf-8").strip()
def _rotate_client_key_pair(entries):
 a, b = _generate_client_key_pair()
 entries[PRIVATE_KEY_KEY] = a
 entries[API_KEY_STATUS_KEY] = "unknown"
 entries[API_KEY_VERIFIED_AT_KEY] = ""
 return a
def _ensure_client_key_pair(entries):
 a = _ensure_pem(PRIVATE_KEY_KEY, entries.get(PRIVATE_KEY_KEY))
 if a:
  entries[PRIVATE_KEY_KEY] = a
  return False, a
 a, b = _generate_client_key_pair()
 entries[PRIVATE_KEY_KEY] = a
 entries[API_KEY_STATUS_KEY] = "unknown"
 return True, a
def _has_complete_key_material(entries):
 a = _ensure_pem(PRIVATE_KEY_KEY, entries.get(PRIVATE_KEY_KEY))
 b = _ensure_pem(SERVER_PUBLIC_KEY_KEY, entries.get(SERVER_PUBLIC_KEY_KEY))
 if not a or not b:
  return False
 try:
  serialization.load_pem_private_key(a.encode("utf-8"), password=None)
  serialization.load_pem_public_key(b.encode("utf-8"))
 except Exception:
  return False
 entries[PRIVATE_KEY_KEY] = a
 entries[SERVER_PUBLIC_KEY_KEY] = b
 return True
def _now_ts():
 return int(datetime.now().timestamp())
def _format_expire_time(expire_time):
 try:
  a = int(expire_time)
 except (TypeError, ValueError):
  return "unknown"
 if a <= 0:
  return "unknown"
 return datetime.fromtimestamp(a).strftime("%Y-%m-%d %H:%M:%S")
def _extract_ticket_from_url(open_url):
 a = str(open_url or "").strip()
 b = "ticket="
 if b not in a:
  return ""
 return a.split(b, 1)[1].split("&", 1)[0].strip()
def _append_ticket_to_url(url, ticket):
 a = quote(ticket, safe="")
 if "#" in url:
  b, c = url.split("#", 1)
  if "?" in c:
   return f"{b}#{c}&ticket={a}"
  return f"{b}#{c}?ticket={a}"
 if "?" in url:
  return f"{url}&ticket={a}"
 return f"{url}?ticket={a}"
def _authority_open_url(open_url, ticket = ""):
 a = str(open_url or "").strip()
 b = str(ticket or "").strip() or _extract_ticket_from_url(a)
 if a.startswith(("http://", "https://")):
  if b and "ticket=" not in a:
   a = _append_ticket_to_url(a, b)
  return a
 if b:
  raise RuntimeError(
   "The TicketCreate response has no activation page url, so the authorization link cannot be built; "
   "check that the OpenAPI gateway and the TicketCreate response are healthy."
  )
 return ""
def _assert_authority_open_url(open_url):
 a = str(open_url or "").strip()
 if not a.startswith(("http://", "https://")):
  raise RuntimeError(f"The OpenAPI authorization link has a malformed format: {a!r}")
 if not _extract_ticket_from_url(a):
  raise RuntimeError(f"The OpenAPI authorization link is missing the ticket parameter: {a!r}")
 return a
def _authority_host_from_url(open_url):
 return urlparse(str(open_url or "").strip()).netloc
def _auth_headers():
 return {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Request-Id": str(uuid.uuid4()),
 }
class OpenApiResponseError(RuntimeError):
 def __init__(self, message, *, code = None, response = None):
  super().__init__(message)
  self.code = code
  self.response = response
def _extract_response_data(body):
 if not isinstance(body, dict):
  raise RuntimeError(f"The authentication API returned a malformed response: {body!r}")
 a = body.get("code")
 if a not in (None, 0):
  b = body.get("message") or "The authentication API call failed"
  raise OpenApiResponseError(
   f"{b} (code={a})",
   code=a,
   response=body,
  )
 c = body.get("content")
 if isinstance(c, dict):
  d = c.get("data")
  if isinstance(d, dict):
   return d
  return c
 d = body.get("data")
 if isinstance(d, dict):
  return d
 return body
def _post_auth_json(base_url, path, payload):
 a = f"{base_url.rstrip('/')}{path}"
 b: bool | str = os.environ.get(VERIFY_TLS_ENV_KEY, "1").strip().lower() not in {
  "0",
  "false",
  "no",
  "off",
 }
 c = (os.environ.get(CA_BUNDLE_ENV_KEY) or "").strip()
 if c:
  b = c
 d = requests.post(
  a,
  json=payload,
  headers=_auth_headers(),
  timeout=15,
  verify=b,
 )
 d.raise_for_status()
 return _extract_response_data(d.json())
def _validate_api_key(base_url, api_key):
 try:
  a = _post_auth_json(
   base_url,
   "/api/v1/auth/APIKeyCheck",
   {"apiKey": api_key},
  )
 except OpenApiResponseError as b:
  c = classify_api_key_error_code(b.code)
  if c:
   return c, {}
  raise
 if not isinstance(a, dict):
  return parse_api_key_check_status(a), {}
 return parse_api_key_check_status(a), a
def _coerce_sub_account_id(value):
 if value is None:
  return ""
 return str(value).strip()
def _normalize_account_index(payload):
 a = (((payload or {}).get("data") or {}).get("subAccounts")) or []
 b: dict[str, list[dict[str, Any]]] = {
  e: [] for e in _ACCOUNT_TYPE_LABELS.values()
 }
 for c in a:
  if not isinstance(c, dict):
   continue
  d = c.get("subAccountType")
  if not isinstance(d, int) or d not in _ACCOUNT_TYPE_LABELS:
   continue
  e = _ACCOUNT_TYPE_LABELS[d]
  b[e].append({
   "subAccountId": _coerce_sub_account_id(c.get("subAccountId")),
   "subAccountType": d,
   "chineseName": c.get("chineseName"),
   "englishName": c.get("englishName"),
   "status": c.get("status"),
  })
 return {"refreshedAt": int(time.time()), **b}
def _refresh_account_index(entries, base_url, api_key):
 a = LOCAL_SDK_ROOT / "fsopenapi"
 if LOCAL_SDK_ROOT.is_dir() and str(LOCAL_SDK_ROOT) not in sys.path:
  sys.path.insert(0, str(LOCAL_SDK_ROOT))
 if a.is_dir():
  b = sys.modules.get("fsopenapi")
  if b is None or not hasattr(b, "__path__"):
   b = types.ModuleType("fsopenapi")
   b.__path__ = [str(a)]
   sys.modules["fsopenapi"] = b
 os.environ[BASE_URL_KEY] = base_url
 os.environ[API_KEY_KEY] = api_key
 os.environ.setdefault(VERIFY_TLS_ENV_KEY, "1")
 os.environ.setdefault(CA_BUNDLE_ENV_KEY, "")
 entries.setdefault(VERIFY_TLS_ENV_KEY, "1")
 entries.setdefault(CA_BUNDLE_ENV_KEY, "")
 os.environ[PRIVATE_KEY_KEY] = _ensure_pem(PRIVATE_KEY_KEY, entries.get(PRIVATE_KEY_KEY))
 os.environ[SERVER_PUBLIC_KEY_KEY] = _ensure_pem(
  SERVER_PUBLIC_KEY_KEY,
  entries.get(SERVER_PUBLIC_KEY_KEY),
 )
 from fsopenapi.api.account import AccountAPI
 from fsopenapi.client import OpenAPIClient
 c = OpenAPIClient(base_url, api_key)
 d = AccountAPI(c)
 e = _normalize_account_index(d.list_accounts())
 entries[ACCOUNT_INDEX_KEY] = json.dumps(e, ensure_ascii=False)
 return e
def _is_auth_material_error(exc):
 a = str(exc)
 return (
  type(exc).__name__ in {"AuthenticationError", "ValueError"}
  or "Handshake signature verification failed" in a
  or "Missing FSOPENAPI_CLIENT_PRIVATE_KEY" in a
  or "Missing FSOPENAPI_SERVER_PUBLIC_KEY" in a
  or "Invalid server signature" in a
 )
def _api_key_error_code(exc):
 a = getattr(exc, "code", None)
 if a is None:
  return None
 try:
  return int(a)
 except (TypeError, ValueError):
  return None
def _mark_api_key_status(entries, status):
 entries[API_KEY_STATUS_KEY] = status
 if status == "valid":
  entries[API_KEY_VERIFIED_AT_KEY] = str(_now_ts())
 else:
  entries[API_KEY_VERIFIED_AT_KEY] = ""
def _contact_support_payload(env_path, *, message = ""):
 return {
  "ok": False,
  "status": "blocked",
  "env_path": str(env_path),
  "error_code": "OPENAPI_ACCOUNT_CONTACT_SUPPORT",
  "account_action": ACTION_CONTACT_SUPPORT,
  "user_message": message or CONTACT_SUPPORT_USER_MESSAGE,
  "hint": "The apikey has been disabled or revoked; contact Star Wealth customer support and do not issue a TicketCreate QR code.",
  "next_action": "Tell the user in English to contact Star Wealth support. Do not generate a QR code.",
 }
def _credential_recovery_payload(
 entries,
 env_path,
):
 a = str(entries.get(API_KEY_STATUS_KEY, "") or "").strip().lower()
 if a not in {"expired", "disabled"}:
  return None
 save_env_entries(entries, env_path)
 if a == "disabled":
  return _contact_support_payload(env_path)
 b = issue_credential_ticket(scenario=SCENARIO_RENEW, created=True)
 b["api_key_check_status"] = "expired"
 b["renew_trigger"] = "api_key_check"
 return b
def _valid_payload(
 entries,
 env_path,
 next_action,
):
 a = {}
 try:
  a = json.loads(str(entries.get(ACCOUNT_INDEX_KEY) or "{}"))
 except ValueError:
  a = {}
 return {
  "ok": True,
  "status": "valid",
  "env_path": str(env_path),
  "accounts_summary": {
   "real_stock": len(a.get("real_stock") or []),
   "real_option": len(a.get("real_option") or []),
   "mock": len(a.get("mock") or []),
  },
  "next_action": next_action,
 }
def _finalize_valid_credentials(
 entries,
 env_path,
 base_url,
 next_action,
):
 a = str(entries.get(API_KEY_KEY, "") or "").strip()
 if not a or not _has_complete_key_material(entries):
  return None
 b = "unknown"
 c: dict[str, Any] = {}
 try:
  b, c = _validate_api_key(base_url, a)
  if b in {"expired", "disabled"}:
   _mark_api_key_status(entries, b)
   save_env_entries(entries, env_path)
   return None
  _mark_api_key_status(entries, "unknown")
  _refresh_account_index(entries, base_url, a)
 except Exception as d:
  e = classify_api_key_error_code(_api_key_error_code(d))
  if e in {"expired", "disabled", "invalid"}:
   _mark_api_key_status(entries, e)
   save_env_entries(entries, env_path)
   return None
  if _is_auth_material_error(d):
   _mark_api_key_status(entries, "invalid")
   save_env_entries(entries, env_path)
   return None
  raise
 _mark_api_key_status(entries, "valid")
 _drop_transient_auth_entries(entries)
 save_env_entries(entries, env_path)
 f = _valid_payload(entries, env_path, next_action)
 f["api_key_check_status"] = b
 if isinstance(c.get("expiresAt"), (int, float)) and c.get("expiresAt"):
  f["api_key_expires_at"] = int(c["expiresAt"])
 g = _persist_credential_backup(entries)
 if g:
  f["backup_path"] = str(g)
  f["backup_dir"] = str(g.parent)
 return f
def _restore_valid_credentials_from_backup(
 env_path,
 base_url,
):
 for a in _restore_candidate_paths():
  b = load_env_entries(a)
  if not b:
   continue
  _drop_transient_auth_entries(b)
  if not b.get(BASE_URL_KEY):
   b[BASE_URL_KEY] = base_url
  c = str(b.get(BASE_URL_KEY) or base_url).rstrip("/")
  b[BASE_URL_KEY] = c
  d = _finalize_valid_credentials(
   b,
   env_path,
   c,
   "fosun.env has been restored automatically from the user-level local backup and the account index has been refreshed, so you can continue with the business at hand.",
  )
  if d:
   d["restored_from_backup"] = str(a)
   d.setdefault("backup_dir", str(a.parent))
   return d
 return None
def _has_api_key_and_complete_material(entries):
 return bool(str(entries.get(API_KEY_KEY, "") or "").strip()) and _has_complete_key_material(entries)
def _try_finalize_pending_authority(
 entries,
 env_path,
 base_url,
):
 a = str(entries.get(API_KEY_KEY, "") or "").strip()
 if not a or not _has_complete_key_material(entries):
  return None
 b = _finalize_valid_credentials(
  entries,
  env_path,
  base_url,
  "Web authorization is complete; the API Key, local private key, server public key, and account index have been written into the shared credential, so you can continue with the business at hand.",
 )
 if b:
  _delete_pending_state(env_path)
 return b
def _sanitize_api_key(value):
 a = str(value or "")
 b = re.search(r"ak_[A-Za-z0-9_\-=]{20,}", a)
 return b.group(0) if b else ""
def _merge_ticket_create_material(entries, data):
 a = _sanitize_api_key(data.get("apiKey"))
 b = str(
  data.get("serverPubKey")
  or data.get("serverPublicKey")
  or ""
 ).strip()
 if a:
  entries[API_KEY_KEY] = a
 if b:
  entries[SERVER_PUBLIC_KEY_KEY] = b
def _pending_payload(
 env_path,
 *,
 created,
 open_url,
 ticket_expire_time,
 scenario = SCENARIO_SETUP,
):
 open_url = _assert_authority_open_url(open_url.strip())
 if scenario == SCENARIO_RENEW:
  open_url = build_open_url(open_url, is_expired=True)
 elif scenario in {SCENARIO_SETUP, SCENARIO_RESET}:
  open_url = build_open_url(open_url, is_expired=False)
 a = scenario_fields(scenario)
 b: dict[str, Any] = {
  "ok": True,
  "status": "pending",
  "env_path": str(env_path),
  "created_new_ticket": created,
  "open_url": open_url,
  "exact_open_url": open_url,
  "authority_host": _authority_host_from_url(open_url),
  "delivery_mode": "remote",
  "operation_guide": operation_guide(scenario),
  "url_copy_rule": (
   "The exact_open_url / open_url field value must be sent to the user character for character as it is; do not retype it, rewrite it, or "
   "reassemble the domain by hand."
  ),
  "ticket_expire_time": ticket_expire_time,
  "ticket_expire_time_text": _format_expire_time(ticket_expire_time),
  **a,
 }
 return apply_qr_delivery(b, open_url)
def _create_ticket(
 entries,
 env_path,
 base_url,
 private_key_pem,
 *,
 scenario = SCENARIO_SETUP,
):
 _drop_bound_credential_entries(entries)
 if scenario == SCENARIO_RESET:
  private_key_pem = _rotate_client_key_pair(entries)
 a = {
  "macId": str(entries.get(MAC_ID_KEY, "")).strip(),
  "clientPubKey": _derive_public_key(private_key_pem),
 }
 b = _post_auth_json(base_url, "/api/v1/auth/TicketCreate", a)
 _merge_ticket_create_material(entries, b)
 c = str(b.get("ticket", "")).strip()
 d = _authority_open_url(b.get("url"), c)
 e = str(b.get("expireTime", "0") or "0")
 if not all([c, d]):
  raise RuntimeError("The TicketCreate response is missing required fields, so the local credential cannot be written.")
 entries[TICKET_KEY] = c
 entries[TICKET_STATUS_KEY] = "active"
 entries[TICKET_EXPIRE_TIME_KEY] = e
 entries[OPEN_URL_KEY] = d
 _save_pending_state(
  entries,
  env_path,
  ticket=c,
  open_url=d,
  expire_time=e,
  credential_scenario=scenario,
 )
 return _pending_payload(
  env_path,
  created=True,
  open_url=d,
  ticket_expire_time=e,
  scenario=scenario,
 )
def ensure_fosun_env(
 *,
 repair_existing = False,
 force_new_ticket = False,
 api_key = None,
 server_public_key = None,
 base_url = None,
):
 a = shared_env_path()
 b = load_env_entries(a)
 _drop_transient_auth_entries(b)
 c = str(base_url or b.get(BASE_URL_KEY) or DEFAULT_BASE_URL).rstrip("/")
 if (
  not force_new_ticket
  and not api_key
  and not server_public_key
  and (not b or not _has_api_key_and_complete_material(b))
 ):
  d = _restore_valid_credentials_from_backup(a, c)
  if d:
   return d
  b = load_env_entries(a)
  _drop_transient_auth_entries(b)
 e = _load_pending_state(a)
 if force_new_ticket:
  e = _reset_pending_and_ticket(b, e)
 if e:
  for f, g in e.items():
   if not b.get(f):
    b[f] = g
 _generate_device_id(b)
 h, i = _ensure_client_key_pair(b)
 if not b.get(BASE_URL_KEY):
  b[BASE_URL_KEY] = DEFAULT_BASE_URL
 if base_url:
  b[BASE_URL_KEY] = str(base_url).strip().rstrip("/")
 j = str(b.get(BASE_URL_KEY) or DEFAULT_BASE_URL).rstrip("/")
 b[BASE_URL_KEY] = j
 if api_key:
  b[API_KEY_KEY] = api_key.strip()
  b[API_KEY_STATUS_KEY] = "unknown"
 if server_public_key:
  b[SERVER_PUBLIC_KEY_KEY] = server_public_key.strip()
 k = str(b.get(API_KEY_KEY, "")).strip()
 l = str(
  b.get(API_KEY_STATUS_KEY, "unknown") or "unknown"
 ).strip().lower()
 m = _has_complete_key_material(b)
 if (
  k
  and l == "valid"
  and m
  and not force_new_ticket
  and not repair_existing
 ):
  if b.get(ACCOUNT_INDEX_KEY):
   _drop_transient_auth_entries(b)
   save_env_entries(b, a)
   n = _persist_credential_backup(b)
   _delete_pending_state(a)
   o = _valid_payload(b, a, "The shared credential has been marked valid, so you can continue with the business at hand.")
   if n:
    o["backup_path"] = str(n)
    o["backup_dir"] = str(n.parent)
   return o
  p = _finalize_valid_credentials(
   b,
   a,
   j,
   "The shared credential has been marked valid and the account index has been refreshed, so you can continue with the business at hand.",
  )
  if p:
   _delete_pending_state(a)
   return p
  q = _credential_recovery_payload(b, a)
  if q:
   return q
  _mark_invalid_and_save(b, a)
 if (
  not force_new_ticket
  and not h
  and str(b.get(TICKET_KEY, "")).strip()
 ):
  p = _try_finalize_pending_authority(
   b, a, j
  )
  if p:
   return p
  q = _credential_recovery_payload(b, a)
  if q:
   return q
  e = _reset_pending_and_ticket(b, e)
 if k and not force_new_ticket and not m:
  return issue_credential_ticket(scenario=SCENARIO_RESET, created=True)
 if k and not force_new_ticket:
  p = _finalize_valid_credentials(
   b,
   a,
   j,
   "The API Key passed validation and the account index has been refreshed, so you can continue with the business at hand.",
  )
  if p:
   _delete_pending_state(a)
   return p
  q = _credential_recovery_payload(b, a)
  if q:
   return q
  e = _reset_pending_and_ticket(b, e)
  _mark_invalid_and_save(b, a)
 q = _credential_recovery_payload(b, a)
 if q:
  return q
 if force_new_ticket:
  r = SCENARIO_SETUP
 else:
  s = str(
   b.get(API_KEY_STATUS_KEY, "") or l
  ).strip().lower()
  if s == "expired":
   return issue_credential_ticket(scenario=SCENARIO_RENEW, created=True)
  if s == "disabled":
   return _contact_support_payload(a)
  r = (
   SCENARIO_RESET
   if k or m or s == "invalid"
   else SCENARIO_SETUP
  )
 t = _create_ticket(
  b,
  a,
  j,
  i,
  scenario=r,
 )
 p = _try_finalize_pending_authority(b, a, j)
 if p:
  return p
 return t
_BACKFILL_UPDATE_CMD = (
 "python3 fosun-env-setup/code/ensure_fosun_env.py "
 "--api-key <API key from the page> --server-public-key '<server public key PEM from the page>'"
)
def _apikey_backfill_rejected_payload(env_path):
 a = _load_pending_state(env_path)
 b = str(a.get(OPEN_URL_KEY, "") or "").strip()
 if not b:
  return issue_credential_ticket(scenario=SCENARIO_RESET, created=True)
 c = str(a.get(TICKET_EXPIRE_TIME_KEY, "0") or "0")
 d = _pending_payload(
  env_path,
  created=False,
  open_url=b,
  ticket_expire_time=c,
  scenario=SCENARIO_RESET,
 )
 d["ok"] = False
 d["api_key_rejected"] = True
 d["user_message"] = (
  "The API key was rejected. Do not scan a new QR code. "
  "On the page for the current QR code, tap Forgot API parameters, reset, "
  "and send the new API key and server public key PEM from that page together. "
  "Do not resend an old key."
 )
 d["next_action"] = (
  "The current QR code is reused (created_new_ticket=false, the key pair stays the same); remind the user to click \"Forgot API parameters\" on that page, send "
  f"back the newly displayed API Key, and run {_BACKFILL_UPDATE_CMD} again. Never "
  "re-issue a ticket or rotate keys: doing so invalidates the page binding the user just completed and causes an endless loop. Run the default entry "
  "point to re-issue only when the user explicitly asks to start over."
 )
 return d
def update_api_key(
 api_key,
 *,
 server_public_key,
 finalize = True,
):
 api_key = str(api_key or "").strip()
 if not api_key:
  raise ValueError("The API Key must not be empty")
 a = shared_env_path()
 b, c = _apply_user_api_key_backfill(
  a,
  api_key,
  server_public_key=server_public_key,
 )
 d = {
  "api_key_updated": True,
  "promoted_from_pending": c,
  "api_key_written_to_env_and_pending": True,
 }
 if not finalize:
  return {"api_key": api_key, "env_path": str(a), **d}
 e = str(b.get(BASE_URL_KEY) or DEFAULT_BASE_URL).rstrip("/")
 f = _finalize_valid_credentials(
  b,
  a,
  e,
  "The API Key write-back passed validation; the local private key, the server public key, and the account index have been written into the shared credential, so you can continue with the business at hand.",
 )
 if f:
  _delete_pending_state(a)
  f.update(d)
  return f
 g = _credential_recovery_payload(b, a)
 if g:
  g.update(d)
  return g
 h = _apikey_backfill_rejected_payload(a)
 h.update(d)
 return h
def _mint_renew_ticket():
 a = shared_env_path()
 b = load_env_entries(a)
 _generate_device_id(b)
 c = str(b.get(BASE_URL_KEY) or DEFAULT_BASE_URL).rstrip("/")
 b[BASE_URL_KEY] = c
 if not str(b.get(API_KEY_KEY, "")).strip():
  raise RuntimeError("Renewal needs an API Key that already exists locally, so it cannot be overwritten.")
 if not _has_complete_key_material(b):
  raise RuntimeError("Renewal needs a server public key that already exists locally, so it cannot be overwritten.")
 d, e = _ensure_client_key_pair(b)
 f = {
  "macId": str(b.get(MAC_ID_KEY, "")).strip(),
  "clientPubKey": _derive_public_key(e),
 }
 g = _post_auth_json(c, "/api/v1/auth/TicketCreate", f)
 h = str(g.get("ticket", "")).strip()
 i = _authority_open_url(g.get("url"), h)
 j = str(g.get("expireTime", "0") or "0")
 if not all([h, i]):
  raise RuntimeError("The TicketCreate response is missing required fields, so the local credential cannot be written.")
 b[TICKET_KEY] = h
 b[TICKET_STATUS_KEY] = "active"
 b[TICKET_EXPIRE_TIME_KEY] = j
 b[OPEN_URL_KEY] = i
 save_env_entries(b, a)
 return {
  "open_url": i,
  "expire_time": j,
  "ticket": h,
  "renew_only": True,
  "base_url": c,
 }
def _prepare_entries_for_ticket(env_path):
 a = load_env_entries(env_path)
 _drop_transient_auth_entries(a)
 b = _load_pending_state(env_path)
 for c, d in b.items():
  if not a.get(c):
   a[c] = d
 _generate_device_id(a)
 e, f = _ensure_client_key_pair(a)
 if not a.get(BASE_URL_KEY):
  a[BASE_URL_KEY] = DEFAULT_BASE_URL
 g = str(a.get(BASE_URL_KEY) or DEFAULT_BASE_URL).rstrip("/")
 a[BASE_URL_KEY] = g
 return a, f, g
def issue_credential_ticket(*, scenario, created = True):
 if scenario not in {SCENARIO_SETUP, SCENARIO_RENEW, SCENARIO_RESET}:
  raise ValueError(f"Unknown credential scenario: {scenario}")
 a = shared_env_path()
 if scenario == SCENARIO_RENEW:
  b = _mint_renew_ticket()
  return _pending_payload(
   a,
   created=created,
   open_url=b["open_url"],
   ticket_expire_time=b["expire_time"],
   scenario=SCENARIO_RENEW,
  )
 c, d, e = _prepare_entries_for_ticket(a)
 return _create_ticket(
  c,
  a,
  e,
  d,
  scenario=scenario,
 )
def renew_openapi_credentials():
 return issue_credential_ticket(scenario=SCENARIO_RENEW)
def reset_openapi_credentials():
 return issue_credential_ticket(scenario=SCENARIO_RESET)
def issue_apikey_error_payload(
 *,
 scenario,
 code,
 message = "",
 label = "",
):
 a = issue_credential_ticket(scenario=scenario, created=True)
 a["ok"] = False
 a["code"] = code
 a["message"] = message or label
 if scenario == SCENARIO_RENEW:
  a["error_code"] = "OPENAPI_ACCOUNT_RENEW"
 elif scenario == SCENARIO_RESET:
  a["error_code"] = "OPENAPI_ACCOUNT_RESET"
 else:
  a["error_code"] = "OPENAPI_ACCOUNT_SETUP"
 return a
def _build_parser():
 a = argparse.ArgumentParser(
  description="Generate or repair the shared fosun.env credential file for fw-trade-skill",
 )
 a.add_argument(
  "--repair",
  action="store_true",
  help="Run the credential state machine to validate, complete, or refresh even when fosun.env already exists",
 )
 a.add_argument(
  "--force-new-ticket",
  action="store_true",
  help="Skip the finalize attempt for the old ticket and issue a new activation URL through TicketCreate right away",
 )
 a.add_argument(
  "--renew",
  action="store_true",
  help="Scenario 2: renew an expired apikey; run TicketCreate and return an activation URL and QR code carrying isExpired=1",
 )
 a.add_argument(
  "--reset-credentials",
  action="store_true",
  help="Scenario 3: the credential is invalid or damaged; rotate the client keys and return a reset URL and QR code (after finishing the reset on the page, write it back with --api-key)",
 )
 a.add_argument(
  "--api-key",
  help="Page write-back: used together with --server-public-key (required for the already-activated and forgotten-API-parameters scenarios)",
 )
 a.add_argument(
  "--server-public-key",
  help="Page write-back: the server public key PEM shown on the authorization page, used together with --api-key (required)",
 )
 a.add_argument(
  "--base-url",
  help=f"Override the gateway address; only PROD is supported (default {DEFAULT_BASE_URL}, anything other than PROD is pulled back)",
 )
 a.add_argument(
  "--print-env-path",
  action="store_true",
  help="Only print the resolved absolute path of fosun.env; write nothing",
 )
 return a
def main():
 a = _build_parser().parse_args()
 if a.print_env_path:
  print(shared_env_path())
  return
 try:
  if a.renew and a.reset_credentials:
   raise ValueError("--renew and --reset-credentials are mutually exclusive; pick only one.")
  b = a.api_key
  c = a.server_public_key
  if a.renew:
   d = renew_openapi_credentials()
  elif a.reset_credentials:
   d = reset_openapi_credentials()
  elif b and not a.repair and not a.force_new_ticket:
   if not c:
    raise ValueError(
     "The write-back must provide both --api-key and --server-public-key (the full server public key PEM from the page). Supplying only the apikey makes "
     "the code use the temporary ticket public key, which does not match the page binding."
    )
   d = update_api_key(
    b,
    server_public_key=c,
    finalize=True,
   )
  else:
   e, f = coerce_prod_base_url(a.base_url)
   if f:
    print(
     f"[fw-trade] --base-url only supports PROD: {a.base_url} was pulled back to {DEFAULT_BASE_URL}",
     file=sys.stderr,
    )
   d = ensure_fosun_env(
    repair_existing=a.repair,
    force_new_ticket=a.force_new_ticket,
    api_key=b,
    server_public_key=c,
    base_url=e,
   )
  print(json.dumps(d, ensure_ascii=False, indent=2))
 except Exception as g:
  d = {
   "ok": False,
   "status": "error",
   "env_path": str(shared_env_path()),
   "message": f"{type(g).__name__}: {g}",
   "next_action": "Fix the local dependency, network, or auth error named in message, then retry. Do not run a business script that needs the credential.",
  }
  print(json.dumps(d, ensure_ascii=False, indent=2), file=sys.stderr)
  sys.exit(1)
if __name__ == "__main__":
 main()
