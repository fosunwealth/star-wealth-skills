#!/usr/bin/env python3
from __future__ import annotations
import argparse
import base64
import os
import sys
from io import BytesIO
from pathlib import Path
import qrcode
ENV_OPEN_URL = "FSOPENAPI_OPEN_URL"
DEFAULT_QR_FILENAME = "link_qr.png"
CHAT_MAX_EDGE = 320
CHAT_MIN_EDGE = 260
TERM_BORDER = 2
def make_qr(url):
 a = qrcode.QRCode(
  version=None,
  error_correction=qrcode.constants.ERROR_CORRECT_L,
  box_size=1,
  border=TERM_BORDER,
 )
 a.add_data(url)
 a.make(fit=True)
 return a
def _render_qr_png_image(
 qr,
 *,
 max_edge = CHAT_MAX_EDGE,
 min_edge = CHAT_MIN_EDGE,
):
 try:
  from PIL import Image
 except ImportError as a:
  raise ImportError(
   "Generating a QR code image needs Pillow; run: pip install qrcode[pil]"
  ) from a
 b = qr.make_image(fill_color="black", back_color="white")
 c, d = b.size
 e = max(c, d)
 if e <= 0:
  raise ValueError("The QR code image has an abnormal size")
 if e > max_edge:
  f = max_edge / e
 elif e < min_edge:
  f = min_edge / e
 else:
  f = 1.0
 g, h = max(1, int(round(c * f))), max(1, int(round(d * f)))
 try:
  i = Image.Resampling.NEAREST
 except AttributeError:
  i = Image.NEAREST
 if g != c or h != d:
  b = b.resize((g, h), resample=i)
 return b, g, h
def save_qr_png_for_chat(
 qr,
 output,
 *,
 max_edge = CHAT_MAX_EDGE,
 min_edge = CHAT_MIN_EDGE,
):
 a, b, c = _render_qr_png_image(qr, max_edge=max_edge, min_edge=min_edge)
 if isinstance(output, BytesIO):
  a.save(output, format="PNG")
  return b, c
 d = Path(output)
 d.parent.mkdir(parents=True, exist_ok=True)
 a.save(d, format="PNG")
 return b, c
def main():
 a = argparse.ArgumentParser(
  description=(
   f"Generate a QR code PNG for an activation page URL (needs Pillow). You must provide "
   f"--url or the environment variable {ENV_OPEN_URL}."
  )
 )
 a.add_argument(
  "--url",
  default=None,
  metavar="link",
  help=f"the full activation page URL; when omitted, the environment variable is read {ENV_OPEN_URL}",
 )
 a.add_argument(
  "-o",
  "--output",
  default=DEFAULT_QR_FILENAME,
  metavar="PATH",
  help=f"path where the QR code PNG is saved (default ./{DEFAULT_QR_FILENAME})",
 )
 a.add_argument(
  "--max-edge",
  type=int,
  default=CHAT_MAX_EDGE,
  metavar="PX",
  help=f"maximum pixels for the longest edge of the image; default {CHAT_MAX_EDGE}",
 )
 a.add_argument(
  "--min-edge",
  type=int,
  default=CHAT_MIN_EDGE,
  metavar="PX",
  help=f"when the modules are too small, scale up so the shortest edge is about this many pixels; default {CHAT_MIN_EDGE}",
 )
 a.add_argument(
  "--markdown-data-uri",
  action="store_true",
  dest="markdown_data_uri",
  help=(
   "Also print one Markdown line: ![](data:image/png;base64,...). If WebChat renders data URIs, you can "
   "paste that line into the reply; most environments block it, so test it yourself."
  ),
 )
 a.add_argument(
  "--markdown-data-uri-max-bytes",
  type=int,
  default=48_000,
  metavar="N",
  help="when the PNG exceeds this number of bytes the data URI is skipped; default 48000",
 )
 b = a.parse_args()
 c = (b.url or "").strip() or (os.environ.get(ENV_OPEN_URL) or "").strip()
 if not c:
  print(
   f"Missing activation page URL: pass --url, or set the environment variable {ENV_OPEN_URL}.",
   file=sys.stderr,
  )
  print(
   f"Example: export {ENV_OPEN_URL}='https://…' && python3 scripts/gen_access_url.py",
   file=sys.stderr,
  )
  return 1
 d = make_qr(c)
 try:
  e = Path(b.output).resolve()
  f, g = save_qr_png_for_chat(
   d,
   e,
   max_edge=max(64, b.max_edge),
   min_edge=max(0, min(b.min_edge, b.max_edge)),
  )
 except ImportError as h:
  print(str(h), file=sys.stderr)
  return 1
 except OSError as i:
  print(f"Cannot write the QR code image: {i}", file=sys.stderr)
  return 1
 except ValueError as i:
  print(str(i), file=sys.stderr)
  return 1
 print("--- application link (copyable) ---", file=sys.stdout)
 print(c, file=sys.stdout)
 print("--- QR code PNG (must be shown as an image in the conversation, do not just reply with the path text) ---", file=sys.stdout)
 print(f"{e}", file=sys.stdout)
 print(f" (image size {f}×{g} pixels)", file=sys.stdout)
 print(f" (source: {ENV_OPEN_URL} / --url)", file=sys.stdout)
 print("<<<FOSUN_QR_PNG_FOR_CHAT>>>", file=sys.stdout)
 print(str(e), file=sys.stdout)
 print("<<<END_FOSUN_QR_PNG_FOR_CHAT>>>", file=sys.stdout)
 if b.markdown_data_uri:
  j = e.read_bytes()
  k = max(4096, b.markdown_data_uri_max_bytes)
  if len(j) > k:
   print(
    f"Note: the PNG exceeds {k} bytes, so the data URI was skipped. Shorten the "
    "link or lower --max-edge a little, then retry.",
    file=sys.stderr,
   )
  else:
   l = base64.standard_b64encode(j).decode("ascii")
   try:
    m = base64.standard_b64decode(l)
    if len(m) != len(j):
     raise ValueError("The Base64 decoded length does not match")
    if m[:8] != j[:8]:
     raise ValueError("The Base64 decoded content does not match")
   except Exception as i:
    print(
     f"Warning: Base64 encoding verification failed; skipping the data URI output: {i}",
     file=sys.stderr,
    )
   else:
    n = f"![OpenAPI activation QR code](data:image/png;base64,{l})"
    print("<<<FOSUN_QR_MARKDOWN_DATA_URI>>>", file=sys.stdout)
    print(
     " (the Base64 is fully generated and verified; pasting the next line in full into the assistant reply may display the image in the bubble)",
     file=sys.stdout,
    )
    print(n, file=sys.stdout)
    print("<<<END_FOSUN_QR_MARKDOWN_DATA_URI>>>", file=sys.stdout)
 return 0
if __name__ == "__main__":
 sys.exit(main())
