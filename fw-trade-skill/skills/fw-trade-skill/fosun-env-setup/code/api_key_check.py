from __future__ import annotations
from typing import Any
ERR_APIKEY_INVALID = 40001
ERR_APIKEY_DISABLED = 40005
ERR_APIKEY_REVOKED = 40008
ERR_APIKEY_EXPIRED = 40010
ERR_CLIENT_KEY_MISMATCH = 40015
API_KEY_ERROR_STATUS_BY_CODE = {
 ERR_APIKEY_INVALID: "invalid",
 ERR_CLIENT_KEY_MISMATCH: "invalid",
 ERR_APIKEY_DISABLED: "disabled",
 ERR_APIKEY_REVOKED: "disabled",
 ERR_APIKEY_EXPIRED: "expired",
}
API_KEY_CHECK_STATUS_BY_CODE = {
 0: "invalid",
 1: "valid",
 2: "disabled",
 3: "expired",
}
def _as_bool_flag(value):
 if isinstance(value, bool):
  return value
 if value is None:
  return None
 if isinstance(value, (int, float)):
  return bool(value)
 a = str(value).strip().lower()
 if not a:
  return None
 if a in {"1", "true", "active", "valid", "ok", "success"}:
  return True
 if a in {"0", "false", "inactive", "invalid", "expired", "error"}:
  return False
 return None
def coerce_api_key_check_status(value):
 if value is None:
  return None
 if isinstance(value, bool):
  return "valid" if value else "invalid"
 if isinstance(value, (int, float)):
  return API_KEY_CHECK_STATUS_BY_CODE.get(int(value))
 a = str(value).strip().lower()
 if a in {"valid", "ok", "active", "1"}:
  return "valid"
 if a in {"invalid", "0"}:
  return "invalid"
 if a in {"disabled", "2"}:
  return "disabled"
 if a in {"expired", "3"}:
  return "expired"
 return None
def classify_api_key_error_code(code):
 try:
  return API_KEY_ERROR_STATUS_BY_CODE.get(int(code))
 except (TypeError, ValueError):
  return None
def parse_api_key_check_status(payload):
 if not isinstance(payload, dict):
  a = coerce_api_key_check_status(payload)
  return a or "unknown"
 if "status" in payload:
  a = coerce_api_key_check_status(payload.get("status"))
  if a:
   return a
 for b in ("valid", "isValid", "active", "isActive"):
  if b not in payload:
   continue
  a = _as_bool_flag(payload.get(b))
  if a is True:
   return "valid"
  if a is False:
   return "invalid"
 for b in ("data", "content", "result"):
  if b not in payload:
   continue
  c = payload.get(b)
  if isinstance(c, dict):
   a = parse_api_key_check_status(c)
  else:
   a = coerce_api_key_check_status(c)
   if not a:
    d = _as_bool_flag(c)
    if d is True:
     a = "valid"
    elif d is False:
     a = "invalid"
  if a and a != "unknown":
   return a
 return "unknown"
