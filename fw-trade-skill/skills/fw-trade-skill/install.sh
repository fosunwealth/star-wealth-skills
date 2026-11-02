#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_FOSUN_ENV_PATH="${HOME}/.workbuddy/star-wealth-openapi/fosun.env"
mkdir -p "$(dirname "${DEFAULT_FOSUN_ENV_PATH}")"
FOSUN_ENV_PATH="${FOSUN_ENV_PATH:-${DEFAULT_FOSUN_ENV_PATH}}"
export FOSUN_ENV_PATH

VENV_DIR="${FW_TRADE_VENV:-${FOSUN_VENV:-${MONI_VENV:-${SKILL_ROOT}/.venv}}}"
PIN_PYTHON_VERSION="${FW_TRADE_PYTHON_VERSION:-${MONI_PYTHON_VERSION:-3.13}}"
SDK_VERSION="${FW_TRADE_SDK_VERSION:-${MONI_SDK_VERSION:-v1.2.0}}"
SDK_ZIP_URL_PRIMARY="${FW_TRADE_SDK_URL:-${MONI_SDK_URL:-https://openapi-docs.fosunxcz.com/download/sdk/openapi-python-sdk-1.2.0.zip}}"
SDK_ZIP_URL_FALLBACK="${FW_TRADE_SDK_FALLBACK_URL:-${MONI_SDK_FALLBACK_URL:-https://github.com/fosunwealth/openapi-python-sdk/archive/refs/tags/v1.2.0.zip}}"
SDK_SHA256="${FW_TRADE_SDK_SHA256:-${MONI_SDK_SHA256:-bfba27b338c7811e5c7ded57c03d901904d92f8339183b5c45714e81c4b52771}}"
SDK_CACHE_ROOT="${FW_TRADE_CACHE_DIR:-${MONI_CACHE_DIR:-${SKILL_ROOT}/.cache}}"
SDK_CACHE_DIR="${SDK_CACHE_ROOT}/openapi-python-sdk-${SDK_VERSION}"

UV_INSTALLER_VERSION="${FW_TRADE_UV_VERSION:-0.12.11}"
UV_INSTALLER_URL="https://astral.sh/uv/${UV_INSTALLER_VERSION}/install.sh"
UV_INSTALLER_SHA256="${FW_TRADE_UV_SHA256:-2c0d7ff0e15a458f46c20bf4d0b1c617f642f578d03f76bc535c9359014cff29}"

log() { printf "\033[1;36m[fw-trade]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[fw-trade ERROR]\033[0m %s\n" "$*" >&2; }

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$1" <<'PY'
import hashlib
import sys

print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PY
    return 0
  fi
  err "Missing shasum, sha256sum, or python3, so the download cannot be verified."
  return 1
}

require_https() {
  case "$1" in
    https://*) return 0 ;;
  esac
  err "Refusing a non-HTTPS download URL: $1"
  exit 1
}

ensure_uv() {
  export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
  if command -v uv >/dev/null 2>&1; then
    log "uv found: $(command -v uv)"
    return 0
  fi
  log "uv not found. Installing pinned uv ${UV_INSTALLER_VERSION} (official URL, SHA256 checked)..."
  UV_INSTALLER_PATH="${TMPDIR:-/tmp}/uv-installer-${UV_INSTALLER_VERSION}.sh"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --connect-timeout 30 --max-time 120 "${UV_INSTALLER_URL}" -o "${UV_INSTALLER_PATH}"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "${UV_INSTALLER_PATH}" "${UV_INSTALLER_URL}"
  else
    err "curl and wget are both missing, so the uv installer cannot be downloaded. Install uv by hand: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
  fi
  local actual
  if ! actual="$(sha256_file "${UV_INSTALLER_PATH}")"; then
    exit 1
  fi
  if [ "${actual}" != "${UV_INSTALLER_SHA256}" ]; then
    err "uv installer SHA256 mismatch (expected ${UV_INSTALLER_SHA256}, got ${actual}). Stopping so a tampered installer is not run."
    exit 1
  fi
  log "uv installer SHA256 ok."
  sh "${UV_INSTALLER_PATH}"
  rm -f "${UV_INSTALLER_PATH}"
  export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"
  if ! command -v uv >/dev/null 2>&1; then
    err "uv install failed. Install uv by hand and rerun."
    exit 1
  fi
  log "uv installed: $(command -v uv)"
}

ensure_uv

VENV_PY="${VENV_DIR}/bin/python"

FIRST_INSTALL=0
if [ ! -x "${VENV_PY}" ]; then
  log "Creating the shared environment (uv downloads Python ${PIN_PYTHON_VERSION} if needed): ${VENV_DIR}"
  mkdir -p "$(dirname "${VENV_DIR}")"
  uv venv --python "${PIN_PYTHON_VERSION}" "${VENV_DIR}"
  FIRST_INSTALL=1
else
  log "Reusing the shared environment: ${VENV_DIR}"
fi

if [ ! -x "${VENV_PY}" ]; then
  err "Shared environment was not created. Interpreter missing: ${VENV_PY}"
  exit 1
fi

SDK_SRC_DIR="${SDK_CACHE_ROOT}/openapi-python-sdk-${SDK_VERSION}"
SDK_ZIP_URL=""
if "${VENV_PY}" -c "import fsopenapi" >/dev/null 2>&1 && [ -d "${SDK_SRC_DIR}" ]; then
  log "SDK is already installed and the cache is present. Skipping download (to reinstall, delete ${SDK_SRC_DIR} and rerun)."
else
  FIRST_INSTALL=1
  TMP_BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/fw-trade-build.XXXXXX")"
trap 'rm -rf "${TMP_BUILD_DIR}"' EXIT
SDK_ZIP_PATH="${TMP_BUILD_DIR}/openapi-python-sdk.zip"
SDK_EXTRACT_DIR="${TMP_BUILD_DIR}/src"

download_sdk_zip() {
  local url="$1"
  require_https "${url}"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --connect-timeout 30 --max-time 600 "${url}" -o "${SDK_ZIP_PATH}"
    return 0
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -O "${SDK_ZIP_PATH}" "${url}"
    return 0
  fi
  err "curl and wget are both missing, so the SDK zip cannot be downloaded: ${url}"
  return 1
}

verify_sdk_zip() {
  local actual
  if ! actual="$(sha256_file "${SDK_ZIP_PATH}")"; then
    err "SHA256 could not be computed. Stopping."
    return 1
  fi
  if [ "${actual}" != "${SDK_SHA256}" ]; then
    err "SDK zip SHA256 mismatch (expected ${SDK_SHA256}, got ${actual}). Stopping so a tampered package is not installed."
    return 1
  fi
  log "SDK zip SHA256 ok: ${actual}"
  return 0
}

if [ -n "${FW_TRADE_SDK_URL:-${MONI_SDK_URL:-}}" ]; then
  log "Custom SDK URL is set. The official primary URL is skipped. SHA256 is still checked (set FW_TRADE_SDK_SHA256 to the hash of that build)."
fi

if download_sdk_zip "${SDK_ZIP_URL_PRIMARY}" && verify_sdk_zip; then
  SDK_ZIP_URL="${SDK_ZIP_URL_PRIMARY}"
elif [ -n "${SDK_ZIP_URL_FALLBACK}" ] && [ "${SDK_ZIP_URL_FALLBACK}" != "${SDK_ZIP_URL_PRIMARY}" ]; then
  log "Primary URL failed or the hash did not match. Trying the official GitHub archive: ${SDK_ZIP_URL_FALLBACK}"
  if download_sdk_zip "${SDK_ZIP_URL_FALLBACK}" && verify_sdk_zip; then
    SDK_ZIP_URL="${SDK_ZIP_URL_FALLBACK}"
  else
    err "Primary and fallback URLs both failed the download or the hash check. Set FW_TRADE_SDK_URL / FW_TRADE_SDK_FALLBACK_URL / FW_TRADE_SDK_SHA256 and rerun."
    exit 1
  fi
else
  err "Primary URL failed and no fallback is configured. Set FW_TRADE_SDK_URL / FW_TRADE_SDK_FALLBACK_URL / FW_TRADE_SDK_SHA256 and rerun."
  exit 1
fi

log "Unpacking the SDK zip"
SDK_EXTRACTED_DIR="$("${VENV_PY}" - "${SDK_ZIP_PATH}" "${SDK_EXTRACT_DIR}" <<'PY'
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
extract_root = Path(sys.argv[2])
extract_root.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(extract_root)

root_dirs = [p for p in extract_root.iterdir() if p.is_dir()]
if len(root_dirs) == 1:
    candidate = root_dirs[0]
else:
    candidates = []
    for marker in ("setup.py", "pyproject.toml"):
        for file in extract_root.rglob(marker):
            candidates.append(file.parent)
    if not candidates:
        raise SystemExit("setup.py / pyproject.toml not found in the unpacked SDK")
    candidate = sorted(candidates, key=lambda p: len(str(p)))[0]

print(candidate.resolve())
PY
)"
mkdir -p "${SDK_CACHE_ROOT}"
rm -rf "${SDK_CACHE_DIR}"
cp -R "${SDK_EXTRACTED_DIR}" "${SDK_CACHE_DIR}"
SDK_SRC_DIR="${SDK_CACHE_DIR}"
log "SDK cache: ${SDK_SRC_DIR}"

if [ ! -f "${SDK_SRC_DIR}/setup.py" ] && [ ! -f "${SDK_SRC_DIR}/pyproject.toml" ]; then
  err "SDK cache is missing setup.py and pyproject.toml: ${SDK_SRC_DIR}"
  exit 1
fi

log "Installing the fsopenapi SDK (editable, official PyPI)"
if ! uv pip install --python "${VENV_PY}" --reinstall --editable "${SDK_SRC_DIR}"; then
  err "Install from https://pypi.org failed. Check that this machine can reach it, then rerun install.sh."
  exit 1
fi

log "Installing QR dependencies (qrcode and Pillow) from official PyPI"
if ! uv pip install --python "${VENV_PY}" "qrcode[pil]>=7.4"; then
  err "Install from https://pypi.org failed. Check that this machine can reach it, then rerun install.sh."
  exit 1
fi
fi

log "Checking import fsopenapi"
"${VENV_PY}" -c "import fsopenapi; print('  fsopenapi @', fsopenapi.__file__)"
log "Checking import qrcode and PIL"
"${VENV_PY}" -c "import qrcode; from PIL import Image; print('  qrcode + Pillow OK')"

if [ "${FIRST_INSTALL}" = "1" ]; then
  log "First install. Checking the shared credential: ${FOSUN_ENV_PATH}"
  "${VENV_PY}" "${SKILL_ROOT}/fosun-env-setup/code/ensure_fosun_env.py" || {
    err "Credential check failed. The environment install itself is done. Run this by hand:"
    err "  ${VENV_PY} ${SKILL_ROOT}/fosun-env-setup/code/ensure_fosun_env.py"
  }
fi

cat <<EOF

Install finished. Paper, live, and env-setup share this environment.

Python: ${VENV_PY} (pinned ${PIN_PYTHON_VERSION})
Skill root: ${SKILL_ROOT}
Virtualenv: ${VENV_DIR}
Shared credential: ${FOSUN_ENV_PATH}
SDK source: ${SDK_ZIP_URL:-reused cache}
SDK cache: ${SDK_SRC_DIR}

Session setup (export once per new session):
  export FOSUN_SKILL_ROOT="${SKILL_ROOT}"
  export FOSUN_PY="${VENV_PY}"
  export FOSUN_ENV_PATH="${FOSUN_ENV_PATH}"

Shared credential (before a business script):
  \$FOSUN_PY \$FOSUN_SKILL_ROOT/fosun-env-setup/code/ensure_fosun_env.py

Paper example, from the skill root:
  FW_TRADE_MODE=paper \$FOSUN_PY \$FOSUN_SKILL_ROOT/code/check_shared_env.py

Live example, from the skill root:
  FW_TRADE_MODE=live \$FOSUN_PY \$FOSUN_SKILL_ROOT/code/check_shared_env.py

See each subskill's subSKILL.md.

EOF
