from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import logging
HERE = Path(__file__).resolve().parent
FW_TRADE_ROOT = HERE.parent
from _modes import MODE
try:
 _SETUP_CODE_DIR = FW_TRADE_ROOT / "fosun-env-setup" / "code"
 if str(_SETUP_CODE_DIR) not in sys.path:
  sys.path.insert(0, str(_SETUP_CODE_DIR))
 from api_key_check import classify_api_key_error_code
except Exception:
 _FALLBACK_APIKEY_STATUS = {
  40001: "invalid", 40015: "invalid",
  40005: "disabled", 40008: "disabled",
  40010: "expired",
 }
 def classify_api_key_error_code(code):
  try:
   return _FALLBACK_APIKEY_STATUS.get(int(code))
  except (TypeError, ValueError):
   return None
class APIError(Exception):
 pass
SDKClient = Any
JsonFormatter = None
get_sdk_logger = None
_FSOPENAPI_READY = False
SERVICE_HOME_DIR = Path.home() / ".workbuddy" / "star-wealth-openapi"
DEFAULT_SHARED_ENV_PATH = SERVICE_HOME_DIR / "fosun.env"
TRADE_MARKETS = {"hk", "us"}
TRADE_PRODUCT_TYPES = {5, 6}
_PEM_WRAPPERS = {
 "FSOPENAPI_CLIENT_PRIVATE_KEY": ("-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----"),
 "FSOPENAPI_SERVER_PUBLIC_KEY": ("-----BEGIN PUBLIC KEY-----", "-----END PUBLIC KEY-----"),
}
ACCOUNT_INDEX_KEY = "FSOPENAPI_ACCOUNT_INDEX"
ACCOUNT_TYPE_LABELS = {
 0: "real_stock",
 1: "real_option",
 2: "mock",
}
SUPPORTED_ACCOUNT_TYPES = ("mock", "real_stock", "real_option")
SKILL_ALLOWED_ACCOUNT_TYPE = MODE.account_type
_ACCOUNT_REFRESH_HINTS = (
 "subaccount",
 "sub_account",
 "account not found",
 "no permission",
 "无权限",
 "账户",
 "子账户",
)
_ACCOUNT_REFRESH_CODES = {60901, 90001, 90004, 90005}
_HK_MARKET_TZ = ZoneInfo("Asia/Shanghai")
CONFIRMATION_WINDOW_SECONDS = MODE.confirmation_window_seconds
CONFIRMATION_TOKEN_LENGTH = MODE.confirmation_token_length
CONFIRMATION_STATE_PATH = FW_TRADE_ROOT / ".pending_confirmation.json"
class NoAccountError(RuntimeError):
 pass
NoMockAccountError = NoAccountError
NoRealStockAccountError = NoAccountError
class StructuredScriptError(RuntimeError):
 def __init__(
  self,
  message,
  *,
  error_code,
  hint = "",
  next_action = "",
  exit_code = 2,
 ):
  super().__init__(message)
  self.error_code = error_code
  self.hint = hint
  self.next_action = next_action
  self.exit_code = exit_code
def shared_env_path():
 a = (os.environ.get("FOSUN_ENV_PATH") or "").strip()
 if not a:
  return DEFAULT_SHARED_ENV_PATH.resolve()
 b = Path(os.path.expandvars(os.path.expanduser(a)))
 if not b.is_absolute():
  b = (DEFAULT_SHARED_ENV_PATH.parent / b).resolve()
 return b
def _candidate_env_files():
 return [shared_env_path()]
def load_env_file():
 for a in _candidate_env_files():
  if a.exists():
   for b, c in _read_shared_entries(a).items():
    os.environ[b] = c
   return a
 raise FileNotFoundError(
  "Shared credential file not found. Generate it first through the sibling fosun-env-setup, and make sure the file FOSUN_ENV_PATH points at exists and is valid; when that variable "
  "is not set, the path defaults to fosun.env in the root of the whole skill."
 )
def _read_shared_entries(path = None):
 a = path or shared_env_path()
 if not a.exists():
  return {}
 b: dict[str, str] = {}
 c = a.read_text(encoding="utf-8").splitlines()
 d = 0
 while d < len(c):
  e = c[d]
  if not e.strip() or e.strip().startswith("#"):
   d += 1
   continue
  f, g, h = e.partition("=")
  f = f.strip()
  h = h.strip()
  if h.startswith('"') and not h.endswith('"'):
   i = [h[1:]]
   d += 1
   while d < len(c):
    j = c[d]
    if j.endswith('"'):
     i.append(j[:-1])
     break
    i.append(j)
    d += 1
   h = "\n".join(i)
  elif h.startswith('"') and h.endswith('"'):
   h = h[1:-1]
  if f:
   b[f] = _ensure_pem(f, h)
  d += 1
 return b
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
def upsert_shared_env(updates):
 a = shared_env_path()
 a.parent.mkdir(parents=True, exist_ok=True)
 b = _read_shared_entries()
 for c, d in updates.items():
  b[c] = "" if d is None else str(d)
 e = {g: _encode_env_value(g, h) for g, h in b.items() if h is not None}
 with a.open("w", encoding="utf-8") as f:
  for c in sorted(e.keys()):
   f.write(f"{c}={e[c]}\n")
 for c, d in updates.items():
  if d is None:
   os.environ.pop(c, None)
  else:
   os.environ[c] = str(d)
def _truthy(value):
 return (value or "").strip().lower() in {"1", "true", "yes", "on", "debug"}
def _configure_sdk_debug_logger():
 _ensure_fsopenapi_ready()
 a = get_sdk_logger()
 a.setLevel(logging.DEBUG)
 if any(getattr(h, "_fw_trade_debug", False) for h in a.handlers):
  return
 b = logging.StreamHandler(sys.stderr)
 b.setFormatter(JsonFormatter())
 b._fw_trade_debug = True
 a.addHandler(b)
PROD_BASE_URL_HOST = "openapi.fosunxcz.com"
def require_activated_credential():
 load_env_file()
 if os.environ.get("FSOPENAPI_API_KEY_STATUS", "").strip().lower() != "valid":
  raise EnvironmentError("Star Wealth OpenAPI credential is not activated. Run python3 fosun-env-setup/code/ensure_fosun_env.py and wait until status is valid")
def build_client():
 require_activated_credential()
 _ensure_fsopenapi_ready()
 a = os.environ.get("FSOPENAPI_BASE_URL")
 b = os.environ.get("FSOPENAPI_API_KEY")
 if not a or not b:
  raise EnvironmentError("FSOPENAPI_BASE_URL and FSOPENAPI_API_KEY must be configured in the env file")
 if (urlparse(a).hostname or "") != PROD_BASE_URL_HOST:
  raise EnvironmentError(
   f"This skill only allows the PROD gateway; FSOPENAPI_BASE_URL is currently {a}; change it "
   f"to https://{PROD_BASE_URL_HOST}"
  )
 c = _truthy(os.environ.get("FSOPENAPI_DEBUG"))
 d = _truthy(os.environ.get("FSOPENAPI_LOG_BODY"))
 if c or d:
  _configure_sdk_debug_logger()
 return SDKClient(
  a,
  b,
  logging_enable=c or d,
  log_body=d,
 )
def _ensure_fsopenapi_ready():
 global APIError, SDKClient, JsonFormatter, get_sdk_logger, _FSOPENAPI_READY
 if _FSOPENAPI_READY:
  return
 try:
  from fsopenapi import JsonFormatter as _JsonFormatter, SDKClient as _SDKClient, get_sdk_logger as _get_sdk_logger
  from fsopenapi.exceptions import APIError as _APIError
 except ModuleNotFoundError as a:
  b = getattr(a, "name", None) or "unknown"
  raise StructuredScriptError(
   f"Missing runtime dependency: `{b}` is not installed.",
   error_code="DEPENDENCY_MISSING",
   hint=(
    "The current Python environment is missing `fsopenapi` and its dependencies, so the script cannot initialize the SDK client."
   ),
   next_action=(
    f"Install the missing package in the current environment first: `{sys.executable} -m pip install {b}`; if missing "
    "`fsopenapi` related packages are still reported afterwards, run install.sh in the root of the whole skill to install the shared SDK dependencies once, then retry."
   ),
   exit_code=2,
  ) from a
 APIError = _APIError
 SDKClient = _SDKClient
 JsonFormatter = _JsonFormatter
 get_sdk_logger = _get_sdk_logger
 _FSOPENAPI_READY = True
def _coerce_sub_account_id(value):
 if value is None:
  return ""
 return str(value).strip()
def _normalize_account_index(payload):
 a = (((payload or {}).get("data") or {}).get("subAccounts")) or []
 b: dict[str, list[dict]] = {e: [] for e in ACCOUNT_TYPE_LABELS.values()}
 for c in a:
  d = c.get("subAccountType")
  e = ACCOUNT_TYPE_LABELS.get(d)
  if not e:
   continue
  b[e].append({
   "subAccountId": _coerce_sub_account_id(c.get("subAccountId")),
   "subAccountType": d,
   "chineseName": c.get("chineseName"),
   "englishName": c.get("englishName"),
   "status": c.get("status"),
  })
 return {"refreshedAt": int(time.time()), **b}
def load_account_index():
 a = os.environ.get(ACCOUNT_INDEX_KEY)
 if not a:
  return None
 try:
  b = json.loads(a)
 except (TypeError, ValueError):
  return None
 if not isinstance(b, dict):
  return None
 return b
def refresh_account_index(client):
 a = client.account.list_accounts()
 b = _normalize_account_index(a)
 upsert_shared_env({ACCOUNT_INDEX_KEY: json.dumps(b, ensure_ascii=False)})
 return b
def sim_account_create(client):
 a = getattr(client.account, "sim_account_create", None)
 if callable(a):
  return a()
 return client.post("/v1/account/SimAccountCreate", data={})
def sim_account_reset(client, sub_account_id):
 a = getattr(client.account, "sim_account_reset", None)
 if callable(a):
  return a(sub_account_id)
 return client.post(
  "/v1/account/SimAccountReset",
  data={"subAccountId": _coerce_sub_account_id(sub_account_id)},
 )
def _pick_from_index(index, account_type):
 if not index:
  return None
 a = index.get(account_type) or []
 for b in a:
  c = _coerce_sub_account_id(b.get("subAccountId"))
  if c:
   return c
 return None
def _find_account_type_by_sub_account_id(index, sub_account_id):
 if not index:
  return None
 a = _coerce_sub_account_id(sub_account_id)
 if not a:
  return None
 for b in SUPPORTED_ACCOUNT_TYPES:
  for c in index.get(b) or []:
   d = _coerce_sub_account_id(c.get("subAccountId"))
   if d == a:
    return b
 return None
def _index_is_empty(index):
 if not index:
  return True
 return not any(index.get(label) for label in SUPPORTED_ACCOUNT_TYPES)
def _raise_no_account(index):
 a = []
 for b in SUPPORTED_ACCOUNT_TYPES:
  for c in index.get(b) or []:
   d = _coerce_sub_account_id(c.get("subAccountId"))
   if d:
    e = c.get("chineseName") or c.get("englishName") or ""
    a.append(f"{b}: {d} {e}".strip())
 f = [
  f"You selected the [{MODE.label}] market for trading, but no {MODE.label} sub-account (subAccountType={MODE.sub_account_type}).",
  f"). This operation has been stopped and is waiting on the user. The model must not switch to the {MODE.other_label} skill on its own, nor automatically continue with a different account.",
 ]
 if a:
  f.append("Sub-accounts visible under the shared credential (for reference only, must not be picked automatically):")
  f.extend(f"  - {c}" for c in a)
 f.append(
  "Tell the user the following in English and wait for a clear instruction before you continue:\n  1) whether to open "
  f"a {MODE.label} account at the broker and retry "
  "afterwards;\n  2) whether to pass `--sub-account-id <ID>` explicitly and use one of the visible accounts for debugging (the user must name the exact ID)."
 )
 raise NoAccountError("\n".join(f))
def _ensure_skill_account_type(account_type):
 if account_type == SKILL_ALLOWED_ACCOUNT_TYPE:
  return
 raise StructuredScriptError(
  f"{MODE.entry}The script refuses to resolve account_type={account_type}.",
  error_code="CROSS_TRADING_GUARD",
  hint=(
   f"This script runs in the {MODE.skill_dir} isolation domain, which only allows {MODE.account_type} sub-accounts; any path other "
   f"than {MODE.account_type} is hard-blocked locally."
  ),
  next_action=(
   f"Stop immediately and confirm the market type with the user; if the user clearly wants{MODE.other_label}, switch to {MODE.other_skill_dir}, and do not retry "
   f"inside the {MODE.label} script."
  ),
  exit_code=2,
 )
def _validate_explicit_sub_account_id(
 client,
 sub_account_id,
 *,
 source,
 expected_account_type,
):
 a = _coerce_sub_account_id(sub_account_id)
 if not a:
  return a
 b = load_account_index()
 c = _find_account_type_by_sub_account_id(b, a)
 if c is None:
  d = refresh_account_index(client)
  c = _find_account_type_by_sub_account_id(d, a)
 if c is None:
  raise StructuredScriptError(
   f"{source} specified subAccountId={a} is not in the current shared account index.",
   error_code="CROSS_TRADING_GUARD",
   hint=(
    f"The market type of that account ID cannot be confirmed. To prevent cross-market mistakes, {MODE.label}the script does not blindly trust an account ID passed in from outside."
   ),
   next_action=(
    f"Run account_list.py first to confirm the visible {MODE.account_type} sub-accounts, then have the user name the "
    "account ID explicitly and retry; Do not switch to the live skill or pick another account."
   ),
   exit_code=2,
  )
 if c != expected_account_type:
  raise StructuredScriptError(
   f"{source} specified subAccountId={a} belongs to {c}, which is inconsistent with the {MODE.label} requirement of {expected_account_type}.",
   error_code="CROSS_TRADING_GUARD",
   hint=(
    f"Cross-market account injection detected: {MODE.label}the script received a sub-account that is not {MODE.account_type}. To avoid mixing "
    "markets, this operation has been hard-blocked."
   ),
   next_action=(
    "Stop and confirm which side they want, then retry with that side's sub-account id."
   ),
   exit_code=2,
  )
 return a
def resolve_sub_account_id(
 client,
 override = None,
 account_type = MODE.account_type,
):
 _ensure_skill_account_type(account_type)
 if account_type not in SUPPORTED_ACCOUNT_TYPES:
  raise ValueError(
   f"Unsupported account type: {account_type}; available values: {SUPPORTED_ACCOUNT_TYPES}"
  )
 a = _coerce_sub_account_id(override)
 if a:
  return _validate_explicit_sub_account_id(
   client,
   a,
   source="CLI --sub-account-id",
   expected_account_type=account_type,
  )
 b = _coerce_sub_account_id(os.environ.get(MODE.sub_account_env))
 if b:
  return _validate_explicit_sub_account_id(
   client,
   b,
   source=f"Environment variable {MODE.sub_account_env}",
   expected_account_type=account_type,
  )
 c = load_account_index()
 if not _index_is_empty(c):
  d = _pick_from_index(c, account_type)
  if d:
   return d
 e = refresh_account_index(client)
 d = _pick_from_index(e, account_type)
 if d:
  return d
 if account_type == MODE.account_type:
  _raise_no_account(e)
 raise RuntimeError(
  f"No sub-account was found under account_type={account_type}; check that the shared "
  "credential has a sub-account of that type enabled"
 )
def _looks_like_account_error(exc):
 if getattr(exc, "code", None) in _ACCOUNT_REFRESH_CODES:
  return True
 a = str(getattr(exc, "message", "") or "").lower()
 return any(hint in a for hint in _ACCOUNT_REFRESH_HINTS)
def call_with_account_retry(
 client,
 factory,
 override = None,
 account_type = MODE.account_type,
):
 _ensure_skill_account_type(account_type)
 a = _coerce_sub_account_id(
  resolve_sub_account_id(client, override, account_type)
 )
 try:
  return factory(a)
 except APIError as b:
  if not _looks_like_account_error(b):
   raise
  refresh_account_index(client)
  c = _coerce_sub_account_id(
   resolve_sub_account_id(client, override, account_type)
  )
  if c == a:
   raise
  print(
   f"[notice] the cached subAccountId={a} is no longer valid and was "
   f"refreshed automatically to {c} and retried.",
   file=sys.stderr,
  )
  return factory(c)
def ensure_trade_market(market_code):
 if market_code and market_code not in TRADE_MARKETS:
  raise ValueError(f"{MODE.entry}Only Hong Kong and US stock trading is supported; market-code only allows hk or us")
def ensure_trade_markets(market_codes):
 for a in market_codes or []:
  ensure_trade_market(a)
def ensure_trade_product_type(product_type):
 if product_type is not None and product_type not in TRADE_PRODUCT_TYPES:
  raise ValueError(f"{MODE.entry}Only Hong Kong and US stock trading is supported; product-type only allows 5 for Hong Kong stocks or 6 for US stocks")
def ensure_trade_product_types(product_types):
 for a in product_types or []:
  ensure_trade_product_type(a)
def ensure_supported_order_type(order_type):
 if order_type is not None and order_type not in MODE.allowed_order_types:
  raise StructuredScriptError(
   f"{MODE.entry}Unsupported orderType={order_type}.",
   error_code="INVALID_PARAM",
   hint=MODE.order_type_hint,
   next_action=(
    "Retry with orderType=3 (limit) or orderType=9 (market). Conditional orders, trailing stops, take-profit and stop-loss "
    "orders, auction, enhanced and special limit orders, and dark-pool orders are never supported."
   ),
   exit_code=2,
  )
def ensure_us_night_session_order_supported(
 market_code,
 order_type,
 time_in_force,
):
 if not MODE.us_night_guard:
  return
 if (market_code or "").strip().lower() != "us":
  return
 if time_in_force != 4:
  return
 if order_type == 9:
  raise StructuredScriptError(
   f"{MODE.entry}US night-session trading does not support market orders (orderType=9).",
   error_code="INVALID_PARAM",
   hint=(
    "The current parameter combination is US stocks plus the night session (timeInForce=4) plus a market order (orderType=9). The night session only supports "
    "limit orders, so the market order is blocked locally."
   ),
   next_action="Retry as a limit order (orderType 3 with --price), or drop the overnight flag and use the regular session.",
   exit_code=2,
  )
def ensure_hk_order_time_window(market_code):
 a = MODE.hk_order_block
 if a is None:
  return
 if (market_code or "").strip().lower() != "hk":
  return
 b = datetime.now(_HK_MARKET_TZ)
 c = b.hour * 60 + b.minute
 if a[0] <= c < a[1]:
  raise StructuredScriptError(
   MODE.hk_order_block_hint,
   error_code="INVALID_PARAM",
   hint=(
    f"The current market time {b.strftime('%H:%M')} (Asia/Shanghai) falls in a restricted window; to avoid fake night-session "
    "fills and ambiguous status, the script hard-blocks locally and sends no order to the gateway."
   ),
   next_action="Retry the Hong Kong order after the restricted window. To trade now, confirm another market or a later time with the user first.",
   exit_code=2,
  )
def ensure_supported_modify_type(modify_type):
 if modify_type is not None and modify_type not in MODE.allowed_modify_types:
  raise StructuredScriptError(
   f"{MODE.entry}Unsupported modifyType={modify_type}.",
   error_code="INVALID_PARAM",
   hint=MODE.modify_type_hint,
   next_action="An order change uses modifyType 1 and may change quantity or price only.",
   exit_code=2,
  )
_SIM_TRADE_MARKET_TUPLES = {
 "hk": {"currency": "HKD", "product_type": 5, "label": "Hong Kong stocks"},
 "us": {"currency": "USD", "product_type": 6, "label": "US stocks"},
}
def ensure_trade_tuple_aligned(
 market_code,
 currency,
 product_type,
):
 a = _SIM_TRADE_MARKET_TUPLES.get(market_code)
 if not a:
  raise ValueError(f"{MODE.entry} market-code only allows hk or us")
 b = []
 if currency != a["currency"]:
  b.append(f"currency={currency} should be {a['currency']}")
 if product_type != a["product_type"]:
  b.append(f"product-type={product_type} should be {a['product_type']}")
 if b:
  raise ValueError(
   f"Market parameter mismatch ({a['label']} {market_code}):"
   + ";".join(b)
   + ". Align the market-code, currency, and product-type trio explicitly; do not rely on defaults."
  )
def expand_market_to_tuple(market):
 a = _SIM_TRADE_MARKET_TUPLES.get(market)
 if not a:
  raise ValueError("--market only supports hk (Hong Kong stocks) or us (US stocks); any other value is rejected")
 return {
  "market_code": market,
  "currency": a["currency"],
  "product_type": a["product_type"],
 }
def resolve_market_args(
 market,
 market_code,
 currency,
 product_type,
 *,
 require_currency = True,
):
 if market:
  if market_code or currency or (product_type is not None):
   raise ValueError(
    "--market is mutually exclusive with --market-code / --currency / --product-type; pick one form, either `--market "
    "hk|us` (recommended) or the full trio (for advanced users)"
   )
  a = expand_market_to_tuple(market)
  return (
   a["market_code"],
   a["currency"] if require_currency else None,
   a["product_type"],
  )
 if require_currency:
  if not (market_code and currency and product_type is not None):
   raise ValueError(
    "Use `--market hk|us` (recommended), or pass the full trio "
    "`--market-code / --currency / --product-type` explicitly; do not rely on defaults"
   )
  ensure_trade_tuple_aligned(market_code, currency, product_type)
  return (market_code, currency, product_type)
 if product_type is None:
  raise ValueError("Use `--market hk|us` (recommended), or pass `--product-type 5|6` explicitly")
 ensure_trade_product_type(product_type)
 return (market_code, None, product_type)
def ensure_trade_show_type(show_type):
 if show_type is not None and show_type != 0:
  raise ValueError(f"{MODE.entry}Option orders are not supported; show-type only allows 0, meaning stock orders only")
def ensure_sub_account_class(sub_account_class):
 if sub_account_class == 9:
  raise ValueError(f"{MODE.entry}Option accounts are not supported; sub-account-class must not be 9")
def _sanitize_confirmation_argv(argv):
 a: list[str] = []
 b = False
 for c in argv:
  if b:
   b = False
   continue
  if c == "--confirm":
   continue
  if c == "--confirm-token":
   b = True
   continue
  if c.startswith("--confirm-token="):
   continue
  a.append(c)
 return a
def _build_confirmation_fingerprint(*, action, intent_summary):
 a = {
  "action": str(action or "").strip(),
  "intent": str(intent_summary or "").strip(),
  "argv": _sanitize_confirmation_argv(sys.argv[1:]),
 }
 b = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
 return hashlib.sha256(b.encode("utf-8")).hexdigest()
def _issue_confirmation_challenge(
 *,
 action,
 intent_summary,
 confirmation_fingerprint,
):
 a = int(time.time())
 b = a + CONFIRMATION_WINDOW_SECONDS
 c = (
  f"{confirmation_fingerprint}|{a}|{time.time_ns()}|"
  f"{os.getpid()}|{os.urandom(8).hex()}"
 )
 d = hashlib.sha256(c.encode("utf-8")).hexdigest()[:CONFIRMATION_TOKEN_LENGTH].upper()
 e = {
  "action": action,
  "intent": intent_summary,
  "fingerprint": confirmation_fingerprint,
  "token": d,
  "issuedAt": a,
  "expiresAt": b,
 }
 CONFIRMATION_STATE_PATH.write_text(
  json.dumps(e, ensure_ascii=False, indent=2),
  encoding="utf-8",
 )
 try:
  os.chmod(CONFIRMATION_STATE_PATH, 0o600)
 except OSError:
  pass
 return e
def _confirmation_window_minutes():
 return max(1, CONFIRMATION_WINDOW_SECONDS // 60)
def _load_confirmation_challenge():
 if not CONFIRMATION_STATE_PATH.exists():
  return None
 try:
  a = json.loads(CONFIRMATION_STATE_PATH.read_text(encoding="utf-8"))
 except (OSError, ValueError, TypeError):
  return None
 return a if isinstance(a, dict) else None
def _clear_confirmation_challenge():
 try:
  CONFIRMATION_STATE_PATH.unlink(missing_ok=True)
 except OSError:
  pass
def ensure_user_confirmed(
 confirmed,
 *,
 action,
 intent_summary,
 confirm_token = None,
):
 a = str(intent_summary or "").strip()
 if not a:
  raise StructuredScriptError(
   f"{action}The operation is missing its intent summary.",
   error_code="INVALID_PARAM",
   hint=(
    "A state-changing operation requires the model to restate the full intent first and only then go through the two-step "
    "confirmation flow; an empty intent robs the confirmation chain of its semantic binding."
   ),
   next_action=(
    f"First fill in the full intent summary of this {action} (including the key objects and arguments), then start the "
    "confirmation flow."
   ),
   exit_code=2,
  )
 b = _build_confirmation_fingerprint(
  action=action,
  intent_summary=a,
 )
 if not confirmed:
  c = _issue_confirmation_challenge(
   action=action,
   intent_summary=a,
   confirmation_fingerprint=b,
  )
  raise StructuredScriptError(
   f"{action}Operation not confirmed: the user must agree explicitly first, and only then may it run with a confirmation token.",
   error_code="NEED_CONFIRMATION",
   hint=(
    f"A state-changing operation ({action}) changes account or order state, so it must never "
    "run from a single command. The system has issued a single-use confirmation token bound to the current intent and the full command arguments."
   ),
   next_action=(
    f"First restate the full {action} intent ({a}) to the user in natural language and "
    f"get explicit agreement; then append `--confirm --confirm-token {c['token']}` to the original command and retry. The token is "
    f"valid for {_confirmation_window_minutes()} minutes and applies only to the current intent."
   ),
   exit_code=2,
  )
 d = str(confirm_token or "").strip().upper()
 c = _load_confirmation_challenge()
 e = int(time.time())
 f = bool(
  c
  and d
  and c.get("token") == d
  and c.get("action") == action
  and str(c.get("intent") or "").strip() == a
  and str(c.get("fingerprint") or "") == b
  and int(c.get("expiresAt") or 0) >= e
 )
 if not f:
  g = _issue_confirmation_challenge(
   action=action,
   intent_summary=a,
   confirmation_fingerprint=b,
  )
  raise StructuredScriptError(
   f"{action}The confirmation token is invalid, missing, or expired, so execution was blocked.",
   error_code="NEED_CONFIRMATION",
   hint=(
    "The second confirmation uses a single-use token that is tightly bound to the operation type, the intent summary, and a fingerprint of the command "
    "arguments; an order operation can never be run by reusing an old token, quietly changing arguments, or skipping the token."
   ),
   next_action=(
    f"Confirm this {action} intent with the user again, then retry with a "
    f"new confirmation token: `--confirm --confirm-token {g['token']}`."
   ),
   exit_code=2,
  )
 _clear_confirmation_challenge()
def dump(data):
 print(json.dumps(data, ensure_ascii=False, indent=2))
_HK_BOARD_LOTS = re.compile(r"^\d{1,5}$")
_US_TICKER = re.compile(r"^[A-Z]{1,5}([.\-][A-Z0-9]{1,3})?$", re.IGNORECASE)
_KNOWN_PREFIXES_LOWER = ("hk", "us", "sh", "sz")
def normalize_security_code(raw):
 if not isinstance(raw, str):
  return str(raw), "The security code was not a string; it was converted with str() and returned as is"
 a = raw.strip()
 if not a:
  return a, "The security code is an empty string"
 b = a.upper()
 for c in ("HK.", "US.", "SH.", "SZ."):
  if b.startswith(c):
   d = b[len(c):]
   if not d:
    return a, f"`{a}` looks like `{c}<code>` but the code part is empty"
   e = c[:2].lower()
   if e in ("hk", "sh", "sz") and d.isdigit():
    d = d.zfill(5)
   return e + d, None
 f = a.lower()
 for g in _KNOWN_PREFIXES_LOWER:
  if f.startswith(g) and len(a) > len(g):
   d = a[len(g):]
   if d.startswith("."):
    d = d[1:]
   return g + d, None
 if _HK_BOARD_LOTS.match(a):
  return "hk" + a.zfill(5), None
 if _US_TICKER.match(a):
  return "us" + b, None
 return a, (
  f"`{a}` does not look like a standard Hong Kong board number (5 digits), a US ticker (1-5 letters), or a value already carrying a valid prefix (hk/us/sh/sz); it was passed to "
  "the SDK as is. If the API errors out or returns empty data, confirm the full market plus code with the user."
 )
def normalize_trade_stock_code(raw, market_code):
 a = (market_code or "").strip().lower()
 if not a:
  raise StructuredScriptError(
   "marketCode is missing, so the security code cannot be normalized into the trading API stockCode.",
   error_code="INVALID_PARAM",
   hint="The stockCode of the trading API relies on marketCode to decide whether an hk/us/sh/sz prefix has to be stripped.",
   next_action="Retry with `--market hk|us`, or pass `--market-code`, `--currency`, and `--product-type` together.",
   exit_code=2,
  )
 b = str(raw).strip()
 if not b:
  raise StructuredScriptError(
   "The security code is empty.",
   error_code="INVALID_PARAM",
   hint="stockCode is required for order placement and must not be empty.",
   next_action="Ask the user for the symbol, then retry.",
   exit_code=2,
  )
 c: Optional[str] = None
 d = b
 e = b.upper()
 for f in ("HK.", "US.", "SH.", "SZ."):
  if e.startswith(f):
   c = f[:2].lower()
   d = b[len(f):]
   break
 if c is None:
  g = b.lower()
  for h in _KNOWN_PREFIXES_LOWER:
   if g.startswith(h) and len(b) > len(h):
    c = h
    d = b[len(h):]
    if d.startswith("."):
     d = d[1:]
    break
 if c and c != a:
  raise StructuredScriptError(
   f"The security-code prefix `{c}` does not match the market `{a}`.",
   error_code="INVALID_PARAM",
   hint=(
    "The trading API carries both marketCode and stockCode, and the two must point at the same market; never pair a "
    "prefixed code such as hk00700 with the us market, or the other way round."
   ),
   next_action="Stop and confirm the market and the symbol. Then retry with `--market` and a matching `--stock-code`.",
   exit_code=2,
  )
 d = d.strip()
 if not d:
  raise StructuredScriptError(
   f"`{b}` looks like a market prefix, but the code part is empty.",
   error_code="INVALID_PARAM",
   hint="For example `hk00700` splits into marketCode=hk plus stockCode=00700, but `hk` on its own carries no actual stock code.",
   next_action="Ask the user for the full symbol, then retry.",
   exit_code=2,
  )
 if a == "hk":
  if not d.isdigit():
   raise StructuredScriptError(
    f"A Hong Kong stockCode must be a plain numeric code, but the value received is `{d}`.",
    error_code="INVALID_PARAM",
    hint="The OrderCreate documentation example is marketCode=hk plus stockCode=00700; do not pass hk00700, and do not pass a non-numeric ticker.",
    next_action="Ask the user for the 5-digit Hong Kong code, then retry.",
    exit_code=2,
   )
  return d.zfill(5)
 if a == "us":
  return d.upper()
 return d
def ensure_order_create_effective(result):
 if not isinstance(result, dict):
  raise StructuredScriptError(
   "The order-placement endpoint returned a malformed structure; it cannot be confirmed that an order was really created.",
   error_code="ORDER_CREATE_UNVERIFIABLE",
   hint=(
    "The SDK response is not a JSON object (dict), which means code, message, and data cannot be extracted from it; on that basis you must not tell the user "
    "the order was placed successfully."
   ),
   next_action=(
    "Do not report success. Show the raw payload and requestId, if any, and ask for the SDK or gateway format to be fixed before a retry."
   ),
   exit_code=2,
  )
 a = result.get("code")
 b = str(result.get("message") or "").strip().lower()
 c = result.get("data")
 if a == 0 and c is None and b in ("success", "ok", ""):
  raise StructuredScriptError(
   "The order-placement response is a silent fail: code=0 but data=null, so it cannot be confirmed that the order was persisted.",
   error_code="ORDER_CREATE_SILENT_FAIL",
   hint=(
    "This is a classic \"success shell\" response: the endpoint looks successful but contains no order entity at all. Until a "
    "real order identifier is in hand, you must not claim the order was placed."
   ),
   next_action=(
    "Stop all follow-up actions immediately and tell the user about the failure exactly as it is; check inputs such as stockCode, marketCode, price, and quantity, then retry."
   ),
   exit_code=2,
  )
 d = c if isinstance(c, dict) else {}
 e = (
  d.get("orderId")
  or d.get("orderID")
  or d.get("order_id")
  or result.get("orderId")
  or result.get("orderID")
  or result.get("order_id")
 )
 e = str(e or "").strip()
 if a == 0 and not e:
  raise StructuredScriptError(
   "The order-placement response has no orderId, so it cannot be proven that the order was persisted.",
   error_code="ORDER_CREATE_NO_ORDER_ID",
   hint=(
    "Order queries and any later modification or cancellation all depend on orderId. Without an orderId this response "
    "cannot be verified and must not be treated as real success."
   ),
   next_action=(
    "Treat this order placement as failed and report it back to the user; retry with the same arguments, and if it still fails, submit the gateway logs for investigation."
   ),
   exit_code=2,
  )
 return e
def _extract_order_mutation_evidence(result):
 a = result.get("data")
 b = a if isinstance(a, dict) else {}
 c = (
  b.get("orderId")
  or b.get("orderID")
  or b.get("order_id")
  or result.get("orderId")
  or result.get("orderID")
  or result.get("order_id")
 )
 d = (
  b.get("orderStatus")
  or b.get("status")
  or result.get("orderStatus")
  or result.get("status")
 )
 return {
  "orderId": str(c).strip() if c not in (None, "") else "",
  "orderStatus": d,
  "data": a,
 }
def _ensure_order_mutation_effective(result, *, action_zh):
 if not isinstance(result, dict):
  raise StructuredScriptError(
   f"{action_zh}The endpoint returned a malformed structure, so it cannot be confirmed that the change took effect.",
   error_code="ORDER_MUTATION_UNVERIFIABLE",
   hint="The SDK response is not a JSON object (dict), so no verifiable fields can be extracted.",
   next_action=(
    f"Do not report the {action_zh} as a success. Show the raw payload and requestId, if any, and have the gateway response format checked."
   ),
   exit_code=2,
  )
 a = result.get("code")
 b = str(result.get("message") or "").strip().lower()
 c = _extract_order_mutation_evidence(result)
 if a == 0 and c["data"] is None and b in ("success", "ok", ""):
  raise StructuredScriptError(
   f"{action_zh}The response is a silent fail: code=0 but data=null, so the order status change cannot be confirmed.",
   error_code="ORDER_MUTATION_SILENT_FAIL",
   hint=(
    "This is a \"success shell\" response: the endpoint looks successful but contains no order entity and no status field; on that basis "
    "you must not tell the user the operation took effect."
   ),
   next_action="Stop and tell the user the call failed. Check the order fields, then retry.",
   exit_code=2,
  )
 if a == 0 and not c["orderId"] and c["orderStatus"] in (None, ""):
  raise StructuredScriptError(
   f"{action_zh}The response lacks verifiable evidence (orderId or orderStatus).",
   error_code="ORDER_MUTATION_NO_EVIDENCE",
   hint=(
    "Without an orderId or orderStatus in the response, there is no proof that the modification or cancellation was accepted and attached to an order entity."
   ),
   next_action=(
    f"Treat this {action_zh} as failed and report it back to the user; retry with the same arguments, and if it still fails, submit the gateway logs for investigation."
   ),
   exit_code=2,
  )
 return {"orderId": c["orderId"], "orderStatus": c["orderStatus"]}
def ensure_order_modify_effective(result):
 return _ensure_order_mutation_effective(result, action_zh="Modify order")
def ensure_order_cancel_effective(result):
 return _ensure_order_mutation_effective(result, action_zh="Cancel order")
def normalize_codes_inplace(args, *fields):
 a: list[str] = []
 for b in fields:
  c = b.replace("-", "_")
  if not hasattr(args, c):
   continue
  d = getattr(args, c)
  if d is None:
   continue
  if isinstance(d, list):
   e: list[Optional[str]] = []
   for f in d:
    if f is None:
     e.append(f)
     continue
    g, h = normalize_security_code(str(f))
    e.append(g)
    if h:
     a.append(h)
   setattr(args, c, e)
  else:
   g, h = normalize_security_code(str(d))
   setattr(args, c, g)
   if h:
    a.append(h)
 return a
def dump_with_directive(
 data,
 *,
 next_action,
 **directives,
):
 a = {"ok": True, "user_language": "en", "next_action": "Reply to the user in English. " + next_action, **directives}
 if isinstance(data, dict):
  a.update(data)
 else:
  a["data"] = data
 b = a.get("data")
 c = a.get("code")
 d = (a.get("message") or "").lower()
 if (
  c == 0
  and b is None
  and d in ("success", "ok", "")
 ):
  e = {
   "ok": False,
   "error_code": "SILENT_FAIL_EMPTY_DATA",
   "message": (
    "The SDK returned code=0 / message=success but data=null, which is a silent failure. The most common cause is a wrong security-code format (for example a missing market "
    "prefix, or a code that does not exist); the SDK swallows the error silently and there is no real data."
   ),
   "hint": (
    'The script adds the market prefix itself. If the gateway still returns no data, ask the user to confirm the full market and code. Do not invent a price.'
   ),
   "next_action": (
    "Stop immediately and truthfully tell the user that the SDK returned no data; ask the user to **confirm the full security code** (including the market, for example hk00700 or usAAPL), then retry. Do "
    "not guess the code yourself, and do not misread ok=true as success; this run produced no real data worth reporting."
   ),
   "_silent_fail_payload_preview": a,
  }
  print(json.dumps(e, ensure_ascii=False, indent=2, default=str), file=sys.stderr)
  sys.exit(2)
 print(json.dumps(a, ensure_ascii=False, indent=2, default=str))
_APIKEY_ERROR_GUIDANCE: dict[str, dict[str, str]] = {
 "invalid": {
  "account_action": "reset",
  "hint": "The apikey in the shared credential is invalid or the client key does not match; the paper-trading skill cannot repair this by itself.",
  "next_action": (
   'Stop. Guide the user to the live trading flow to finish the reset by scanning the QR code. Do not paste a key into the chat.'
  ),
 },
 "expired": {
  "account_action": "renew",
  "hint": "The apikey in the shared credential has expired; the paper-trading skill cannot renew it by itself.",
  "next_action": (
   "Stop, and guide the user back to the sibling real-trade-skill to run the renewal flow (scan the QR code). Renewal only extends the "
   "validity of the existing apikey; it does not overwrite the API Key in fosun.env and needs nothing written back by the user. Once the scan is done, have the "
   "user retry the current paper-trading command directly."
  ),
 },
 "disabled": {
  "account_action": "contact_support",
  "hint": "The apikey in the shared credential has been disabled or revoked and cannot be recovered by the skill itself.",
  "next_action": (
   "Stop, and tell the user in plain language that the OpenAPI account has been disabled or revoked and that they should contact Star Wealth "
   "customer support; do not try TicketCreate and do not generate a QR code."
  ),
 },
}
APIERROR_PLAYBOOK: dict[Any, dict[str, str]] = {
 50001: {
  "hint": "Server-side list endpoints strictly validate the paging Count field; both omitting it and passing 0 are rejected.",
  "next_action": "Retry once with `--count 50` or another sensible page size. Do not retry the same arguments.",
 },
 60006: {
  "hint": "The server rejected the order. Typical causes: price, size, a halt, or the wrong currency.",
  "next_action": "Relay the error to the user in English. Wait for them to change the order. Do not guess a fix.",
 },
 60009: {
  "hint": "The single order amount is over the server limit.",
  "next_action": "Suggest a smaller quantity or a lower-priced name. Do not retry the same size.",
 },
 60014: {
  "hint": "The order was blocked by a risk or compliance check.",
  "next_action": "Relay the error code and message to the user in English. Wait for them to change the name or the fields.",
 },
}
def _apierror_message_playbook(message):
 a = (message or "").strip().lower()
 if "session" in a and ("expir" in a or "invalid" in a or "timeout" in a or "time out" in a or "timed out" in a):
  return {
   "error_code": "SESSION_EXPIRED",
   "hint": "The broker session inside the shared credential has expired. This failure does not mean \"the order or holding does not exist\"; it means the query and operation channel has stopped working.",
   "next_action": "Run check_shared_env.py. If the session is still expired, use the sibling fosun-env-setup, then retry. This is not an order-not-found result.",
  }
 if "signature" in a and ("invalid" in a or "verify" in a or "verification" in a or "mismatch" in a):
  return {
   "error_code": "INVALID_SIGNATURE",
   "hint": "The API key or the signature chain in the shared credential is no longer valid. This is not an order-not-found result.",
   "next_action": "Use the sibling fosun-env-setup to repair the shared credential, then retry. This is not an order-not-found result.",
  }
 return None
def _maybe_inject_from_args_json():
 if "--args-json" not in sys.argv:
  return
 a = sys.argv.index("--args-json")
 if a + 1 >= len(sys.argv):
  raise StructuredScriptError(
   "A JSON object string must immediately follow `--args-json`",
   error_code="INVALID_PARAM",
   hint="`--args-json` expects a JSON object (for example `'{\"code\":[\"hk01810\"]}'`) but nothing follows it.",
   next_action="Put a full JSON object after `--args-json`. Wrap it in single quotes, then retry.",
   exit_code=2,
  )
 b = sys.argv[a + 1]
 try:
  c = json.loads(b)
 except json.JSONDecodeError as d:
  raise StructuredScriptError(
   f"`--args-json` failed to parse: {d}",
   error_code="INVALID_PARAM",
   hint="The string passed to `--args-json` is not valid JSON (common causes: the shell swallowed the double quotes, a comma is missing, or single and double quotes are mixed).",
   next_action=(
    "Suggested form: wrap the whole JSON in single quotes and use "
    "double quotes inside. For example `--args-json '{\"code\":[\"hk01810\"],\"field\":[\"price\"]}'`. Fix it and retry."
   ),
   exit_code=2,
  )
 if not isinstance(c, dict):
  raise StructuredScriptError(
   "`--args-json` must be a JSON object ({...}), not an array, a string, or a number",
   error_code="INVALID_PARAM",
   hint="The JSON template must be a top-level object, and each key corresponds to one argparse flag.",
   next_action="Wrap it as a JSON object, for example `{\"code\":[\"hk01810\"]}`, then retry.",
   exit_code=2,
  )
 e = list(sys.argv[:a])
 for f, g in c.items():
  if f == "_script":
   continue
  h = "--" + str(f).lstrip("-").replace("_", "-")
  if isinstance(g, bool):
   if g:
    e.append(h)
   continue
  if g is None:
   continue
  if isinstance(g, list):
   for i in g:
    e.append(h)
    e.append(str(i))
  else:
   e.append(h)
   e.append(str(g))
 e.extend(sys.argv[a + 2:])
 sys.argv = e
_SYMBOL_BRAINSTORM_NAMES = (
 "--ticker", "--tickers",
 "--instrument", "--instruments",
 "--security", "--securities",
 "--asset", "--assets",
 "--inst-code", "--inst_code",
 "--stockcode", "--stock_code",
 "--symbolcode", "--symbol_code",
 "--codes",
 "--stock", "--stocks",
)
def _detect_symbol_brainstorm(detail):
 a = (detail + " " + " ".join(sys.argv)).lower()
 for b in _SYMBOL_BRAINSTORM_NAMES:
  if b in a:
   return b
 return None
def _raise_argparse_error(message):
 a = (message or "Command-line argument parsing failed").strip()
 b = "Command-line argument parsing failed (unknown argument name / missing required argument / choices mismatch / this script does not support that filter)."
 c = "Fix the flags from the error, then retry. If the flag name is unclear, run `--help`. Do not invent another name."
 d = _detect_symbol_brainstorm(a)
 if d is not None:
  b = (
   f"The argument name `{d}` was invented by the model. The \"security code\" input of every "
   "script in this skill **accepts exactly 4 official aliases**: `--code` / `--stock-code` / `--symbol` / `--symbols` (aligned across scripts since "
   "v1.7.4). Any name outside these 4 (including `--ticker` / `--instrument` / `--security` / `--stocks` and so on) is invented."
  )
  c = (
   f"Rename `{d}` to `--code` (the main name for market-data scripts) or `--stock-code` (the main name for trading scripts) and retry; the "
   "other names (`--symbol` / `--symbols`) are accepted too. **Do not guess any other spelling**: anything beyond these 4 aliases is invented."
  )
 elif "unrecognized arguments" in a and "--order-id" in a:
  b = "`order_list.py` does not support filtering directly by `--order-id`; this failure is a local command-line usage mistake, not a broker-side \"order does not exist\"."
  c = "Narrow order_list.py with `--stock-code` plus a date, market, or status, then find the order id in the list. This is not an order-not-found result."
 raise StructuredScriptError(
  a,
  error_code="INVALID_PARAM",
  hint=b,
  next_action=c,
  exit_code=2,
 )
_GENERIC_PLAYBOOK = {
 "NoAccountError": {
  "error_code": MODE.no_account_error_code,
  "exit_code": 3,
  "hint": MODE.no_account_hint,
  "next_action": f"Stop and tell the user there is no {MODE.label} sub-account. Wait for them to open one, or to pass `--sub-account-id` for a debug call. Do not switch to the {MODE.other_label} skill or pick another account.",
 },
 "FileNotFoundError": {
  "error_code": "ENV_FILE_MISSING",
  "exit_code": 2,
  "hint": "The shared credential file at FOSUN_ENV_PATH does not exist.",
  "next_action": "Create the shared credential with the sibling fosun-env-setup, then come back.",
 },
 "EnvironmentError": {
  "error_code": "ENV_INCOMPLETE",
  "exit_code": 2,
  "hint": "The shared credential exists but FSOPENAPI_BASE_URL or FSOPENAPI_API_KEY is missing.",
  "next_action": "Repair the shared credential with the sibling fosun-env-setup.",
 },
 "ValueError": {
  "error_code": "INVALID_PARAM",
  "exit_code": 2,
  "hint": "A local check failed: the market trio does not match, or a field is outside this entry's scope.",
  "next_action": "Fix the flags from the error and retry. If it changes what they asked for, confirm with them first.",
 },
}
def _format_error_payload(
 *,
 error_code,
 message,
 hint,
 next_action,
 extras = None,
):
 a = {
  "ok": False,
  "error_code": error_code,
  "message": message,
  "hint": hint,
  "user_language": "en",
  "next_action": "Reply to the user in English. " + next_action,
 }
 if extras:
  a.update(extras)
 return a
def _emit_error(payload, exit_code):
 print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
 sys.exit(exit_code)
def run(action):
 a = argparse.ArgumentParser.error
 def b(self, f):
  _raise_argparse_error(f)
 argparse.ArgumentParser.error = b
 try:
  _maybe_inject_from_args_json()
  action()
 except StructuredScriptError as c:
  _emit_error(
   _format_error_payload(
    error_code=c.error_code,
    message=str(c),
    hint=c.hint,
    next_action=c.next_action,
   ),
   c.exit_code,
  )
 except NoAccountError as c:
  d = _GENERIC_PLAYBOOK["NoAccountError"]
  _emit_error(
   _format_error_payload(
    error_code=d["error_code"],
    message=str(c),
    hint=d["hint"],
    next_action=d["next_action"],
   ),
   d["exit_code"],
  )
 except APIError as c:
  e = getattr(c, "code", None)
  f = getattr(c, "message", str(c))
  if MODE.is_live:
   from account_actions import handle_apikey_error, is_apikey_error
   if is_apikey_error(e):
    _emit_error(*handle_apikey_error(e, api_message=f or ""))
  g = classify_api_key_error_code(e)
  if g in _APIKEY_ERROR_GUIDANCE:
   h = _APIKEY_ERROR_GUIDANCE[g]
   _emit_error(
    _format_error_payload(
     error_code=f"APIERROR_{e}" if e is not None else "APIERROR",
     message=f,
     hint=h["hint"],
     next_action=h["next_action"],
     extras={
      "code": e,
      "account_action": h["account_action"],
      "credential_owner_skill": "real-trade-skill",
      "requestId": getattr(c, "request_id", None),
      "data": getattr(c, "data", None),
     },
    ),
    1,
   )
  i = _apierror_message_playbook(f)
  d = APIERROR_PLAYBOOK.get(e, {})
  _emit_error(
   _format_error_payload(
    error_code=i["error_code"] if i else (
     f"APIERROR_{e}" if e is not None else "APIERROR"
    ),
    message=f,
    hint=(i or d).get(
     "hint",
     "Server-side business error; read the message to decide whether a retry is appropriate.",
    ),
    next_action=(i or d).get(
     "next_action",
     "If the error names a bad flag, fix it and retry. Otherwise relay it to the user in English and wait.",
    ),
    extras={
     "code": e,
     "requestId": getattr(c, "request_id", None),
     "data": getattr(c, "data", None),
    },
   ),
   1,
  )
 except FileNotFoundError as c:
  d = _GENERIC_PLAYBOOK["FileNotFoundError"]
  _emit_error(
   _format_error_payload(
    error_code=d["error_code"],
    message=str(c),
    hint=d["hint"],
    next_action=d["next_action"],
   ),
   d["exit_code"],
  )
 except EnvironmentError as c:
  d = _GENERIC_PLAYBOOK["EnvironmentError"]
  _emit_error(
   _format_error_payload(
    error_code=d["error_code"],
    message=str(c),
    hint=d["hint"],
    next_action=d["next_action"],
   ),
   d["exit_code"],
  )
 except ValueError as c:
  d = _GENERIC_PLAYBOOK["ValueError"]
  _emit_error(
   _format_error_payload(
    error_code=d["error_code"],
    message=str(c),
    hint=d["hint"],
    next_action=d["next_action"],
   ),
   d["exit_code"],
  )
 finally:
  argparse.ArgumentParser.error = a
