from __future__ import annotations
import sys
from pathlib import Path
_SETUP_CODE = Path(__file__).resolve().parent.parent / "fosun-env-setup" / "code"
if str(_SETUP_CODE) not in sys.path:
 sys.path.insert(0, str(_SETUP_CODE))
from credential_scenarios import (
 ACTION_CONTACT_SUPPORT,
 ACTION_RENEW,
 ACTION_RESET,
 CONTACT_SUPPORT_USER_MESSAGE,
 RESET_USER_MESSAGE,
 RENEW_USER_MESSAGE,
)
from api_key_check import (
 ERR_APIKEY_DISABLED,
 ERR_APIKEY_EXPIRED,
 ERR_APIKEY_INVALID,
 ERR_APIKEY_REVOKED,
 ERR_CLIENT_KEY_MISMATCH,
 classify_api_key_error_code,
)
from ensure_fosun_env import issue_apikey_error_payload
ACTION_BY_STATUS = {
 "invalid": ACTION_RESET,
 "expired": ACTION_RENEW,
 "disabled": ACTION_CONTACT_SUPPORT,
}
_CODE_LABELS = {
 ERR_APIKEY_INVALID: "apikey invalid (does not exist)",
 ERR_APIKEY_DISABLED: "apikey disabled",
 ERR_APIKEY_REVOKED: "apikey revoked",
 ERR_APIKEY_EXPIRED: "apikey expired",
 ERR_CLIENT_KEY_MISMATCH: "client key pair mismatch",
}
_CONTACT_SUPPORT_HINT = (
 "The apikey has been disabled or revoked and the skill cannot recover by itself. Tell the user in "
 "plain language to contact Star Wealth customer support; do not generate a QR code and do not try TicketCreate."
)
_CONTACT_SUPPORT_NEXT = "Tell the user in English to contact Star Wealth support. Do not generate a QR code."
def is_apikey_error(code):
 return classify_api_key_error_code(code) is not None
def handle_apikey_error(code, *, api_message = ""):
 a = int(code)
 b = classify_api_key_error_code(a)
 c = ACTION_BY_STATUS.get(b)
 if not c:
  raise ValueError(f"not an apikey error code: {code}")
 d = _CODE_LABELS.get(a, f"Error code {a}")
 if c == ACTION_CONTACT_SUPPORT:
  e = {
   "ok": False,
   "error_code": "OPENAPI_ACCOUNT_CONTACT_SUPPORT",
   "code": a,
   "message": api_message or d,
   "account_action": c,
   "user_message": CONTACT_SUPPORT_USER_MESSAGE,
   "hint": _CONTACT_SUPPORT_HINT,
   "next_action": _CONTACT_SUPPORT_NEXT,
  }
  return e, 4
 e = issue_apikey_error_payload(
  scenario=c,
  code=a,
  message=api_message or d,
  label=d,
 )
 if c == ACTION_RENEW:
  e["user_message"] = RENEW_USER_MESSAGE
 else:
  e["user_message"] = RESET_USER_MESSAGE
 return e, 4
