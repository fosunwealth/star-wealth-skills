from __future__ import annotations
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
SCENARIO_SETUP = "setup"
SCENARIO_RENEW = "renew"
SCENARIO_RESET = "reset"
ACTION_SETUP = SCENARIO_SETUP
ACTION_RENEW = SCENARIO_RENEW
ACTION_RESET = SCENARIO_RESET
ACTION_CONTACT_SUPPORT = "contact_support"
CONTACT_SUPPORT_USER_MESSAGE = (
 "This OpenAPI account cannot continue. "
 "Contact Star Wealth support. A QR code will not restore it."
)
FORGET_API_PARAMS_HINT = (
 "If you have opened OpenAPI before (lost credentials and a new device look the same), "
 "tap Forgot API parameters on the page and reset. "
 "On a first-time setup, follow the signup steps and do not tap that button."
)
SETUP_USER_MESSAGE = (
 "The QR code is in the attachment. Scan it, or open the link below to finish OpenAPI signup. "
 f"{FORGET_API_PARAMS_HINT} "
 "After a first-time setup, reply that it is ready and the credentials will be checked again. "
 "If you tapped Forgot API parameters and finished the reset, send the API key and the server public key "
 "from that page (the PEM blocks) together. They are written locally and then checked. "
 "Can you see the QR image in the attachment? If you only see a link or an error, say so and it will be sent another way."
)
RENEW_USER_MESSAGE = (
 "This OpenAPI account has expired and needs a renewal. "
 "The QR code is in the attachment. Scan it, or open the link below. Then retry the same action. "
 "Renewal only extends the current API key. Do not replace or retype it. "
 "Can you see the QR image in the attachment? If you only see a link or an error, say so and it will be sent another way."
)
RESET_USER_MESSAGE = (
 'The OpenAPI credentials need to be set again. The QR code is attached. Scan it, or open the link, then tap Forgot API parameters. Send the API key and the server public key from that page together. Scanning alone does not update this computer.'
)
UPDATE_API_KEY_COMMAND = (
 "python3 fosun-env-setup/code/ensure_fosun_env.py "
 "--api-key <API key from the page> --server-public-key '<server public key PEM from the page>'"
)
def build_open_url(url, *, is_expired = None):
 url = str(url or "").strip()
 if not url:
  return url
 a = urlsplit(url)
 b = a.fragment
 if "?" in b:
  c, d = b.split("?", 1)
 else:
  c, d = b, ""
 e = dict(parse_qsl(d, keep_blank_values=True))
 if is_expired is True:
  e["isExpired"] = "1"
 elif is_expired is False:
  e.pop("isExpired", None)
 f = urlencode(e)
 if f:
  g = f"{c}?{f}"
 else:
  g = c
 return urlunsplit((a.scheme, a.netloc, a.path, a.query, g))
def operation_guide(scenario):
 a = [
  "Send the QR code once, in more than one way, following show_qr_rule "
  "(deliver_attachments plus the link are required; media or a data URI is optional). "
  "When using deliver_attachments, tell the user to open the attachment, then ask whether they can see the QR image.",
  "Send exact_open_url character for character. Do not change the host.",
 ]
 if scenario == SCENARIO_RENEW:
  return a + [
   "Tell the user the OpenAPI account has expired. Scanning renews it. Do not replace the API key.",
   "After they finish, retry the failed action. Do not ask them to paste an API key.",
  ]
 if scenario == SCENARIO_RESET:
  return a + [
   "Tell the user to tap Forgot API parameters on the page.",
   "They must send both the API key and the server public key (full PEM) from that page.",
   f"Then run: {UPDATE_API_KEY_COMMAND}",
   "Do not write the API key alone. After it is written, verify or retry the original command.",
  ]
 return a + [
  FORGET_API_PARAMS_HINT,
  "First-time setup: after they finish on the page and reply that it is ready, run ensure_fosun_env.py again.",
  "New device or Forgot API parameters: wait for the API key and the server public key (PEM) from the page, "
  f"then run {UPDATE_API_KEY_COMMAND} and verify.",
  "If they send only the API key, ask for the server public key from the same page and run the backfill once with both. "
  "Do not run --api-key alone. Finalize routes a valid, expired, or rejected key. "
  "An expired key on a new device is recognized only after both values are written.",
 ]
def scenario_fields(scenario):
 if scenario == SCENARIO_RENEW:
  return {
   "credential_scenario": SCENARIO_RENEW,
   "account_action": ACTION_RENEW,
   "user_message": RENEW_USER_MESSAGE,
   "hint": (
    "The API key has expired. TicketCreate renewal (URL includes isExpired=1). "
    "Renewal only extends the current API key. It does not overwrite the API key or the server public key in fosun.env."
   ),
   "next_action": (
    'Send the QR code once, in more than one way, and send the link. Tell the user in English to scan it or open the link. Ask whether they can see the image.'
   ),
   "requires_api_key_from_user": False,
   "renew_only": True,
  }
 if scenario == SCENARIO_RESET:
  return {
   "credential_scenario": SCENARIO_RESET,
   "account_action": ACTION_RESET,
   "user_message": RESET_USER_MESSAGE,
   "hint": (
    "The local API key is invalid or the key pair does not match. The client key was rotated and TicketCreate issued a reset. "
    "The user must tap Forgot API parameters. Scanning does not update the API key in fosun.env."
   ),
   "next_action": (
    "1. Send the QR code once, following show_qr_rule, plus the link. Tell them to tap Forgot API parameters. "
    f"2. After they send the page API key and the server public key, run {UPDATE_API_KEY_COMMAND}. "
    "3. Run ensure_fosun_env.py again or retry the original command. Do not write the API key alone."
   ),
   "requires_api_key_from_user": True,
   "requires_server_public_key_from_user": True,
   "update_api_key_command": UPDATE_API_KEY_COMMAND,
  }
 return {
  "credential_scenario": SCENARIO_SETUP,
  "account_action": ACTION_SETUP,
  "user_message": SETUP_USER_MESSAGE,
  "hint": (
   'A first signup, a new device, and a lost file look the same. An expired API key can sit on top of a new device. Follow the scenario in the JSON. Do not mix tickets.'
  ),
  "next_action": (
   "Send the QR code once, following show_qr_rule, and send the link. "
   "First signup: after they say it is ready, run ensure_fosun_env.py again. "
   "New device or Forgot API parameters: wait for the API key and the server public key from the page, "
   f"run {UPDATE_API_KEY_COMMAND}, then verify. Do not write the API key alone. "
   "Both values go in one backfill. A first signup only needs them to say it is ready."
  ),
  "requires_api_key_from_user": False,
  "conditional_api_key_backfill": True,
  "requires_server_public_key_on_backfill": True,
  "update_api_key_command": UPDATE_API_KEY_COMMAND,
 }
