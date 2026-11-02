from __future__ import annotations
import base64
import importlib.util
import os
import tempfile
from pathlib import Path
from typing import Any
SETUP_ROOT = Path(__file__).resolve().parent.parent
_QR_DELIVERY_RULE = (
 'Send the QR several ways in the same reply: exact_open_url in the text, and deliver_attachments with qr_png_path. Ask whether they can see the image. If they cannot, ask what they see and try another way. Do not show the image with the Read tool. Do not send only the link.'
)
def _load_gen_access_url_module():
 a = SETUP_ROOT / "scripts" / "gen_access_url.py"
 b = importlib.util.spec_from_file_location("fosun_gen_access_url", a)
 if b is None or b.loader is None:
  raise RuntimeError(f"Cannot load gen_access_url.py: {a}")
 c = importlib.util.module_from_spec(b)
 b.loader.exec_module(c)
 return c
def generate_qr_artifact(url):
 a = _load_gen_access_url_module()
 b = os.path.join(tempfile.gettempdir(), f"fosun_openapi_qr_{os.getpid()}.png")
 c = a.make_qr(url)
 d, e = a.save_qr_png_for_chat(c, b)
 with open(b, "rb") as f:
  g = f.read()
 h = base64.standard_b64encode(g).decode("ascii")
 i = os.path.abspath(b)
 return {
  "qr_png_path": i,
  "qr_media": {
   "method": "media",
   "path": i,
   "mime_type": "image/png",
   "width": d,
   "height": e,
   "filename": "openapi_authority_qr.png",
  },
  "qr_image": {
   "type": "image",
   "mime_type": "image/png",
   "encoding": "base64",
   "data": h,
   "width": d,
   "height": e,
   "alt": "OpenAPI activation QR code",
   "filename": "openapi_authority_qr.png",
  },
 }
def apply_qr_delivery(payload, open_url):
 try:
  a = generate_qr_artifact(open_url)
  payload["qr_png_path"] = a["qr_png_path"]
  payload["qr_media"] = a["qr_media"]
  payload["qr_image"] = a["qr_image"]
  payload["show_qr_rule"] = _QR_DELIVERY_RULE
 except Exception as b:
  payload["qr_generation_error"] = str(b)
  payload["show_qr_rule"] = (
   "QR code generation failed; only exact_open_url is provided. Tell the user to click the link to complete activation."
  )
 return payload
