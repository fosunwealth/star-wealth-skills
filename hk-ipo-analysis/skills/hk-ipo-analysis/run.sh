#!/usr/bin/env sh
# hk-ipo-analysis entry (macOS / Linux / Git-Bash).
#
# Two jobs only:
#   1) skill root = this file's directory (not cwd, not an environment variable)
#   2) find Python 3 (python3, then python, then py -3) and pass the arguments to scripts/main.py
#
# On Windows cmd or PowerShell: py -3 scripts\main.py. Same arguments. If py is missing, use python.
# To pin an interpreter: HK_PYTHON=/path/to/python run.sh gate
set -u

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MAIN="$HERE/scripts/main.py"

if [ ! -f "$MAIN" ]; then
    echo "[hk-ipo-analysis] Incomplete skill: $MAIN was not found" >&2
    exit 1
fi

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

if [ -n "${HK_PYTHON:-}" ]; then
    exec "$HK_PYTHON" "$MAIN" "$@"
fi

for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        exec "$candidate" "$MAIN" "$@"
    fi
done

if command -v py >/dev/null 2>&1; then
    exec py -3 "$MAIN" "$@"
fi

cat >&2 <<'EOF'
[hk-ipo-analysis] Python 3 was not found (python3, python, and py are not on PATH).

Install:
  macOS        https://www.python.org/downloads/ or brew install python
  Linux        sudo apt install python3    /    sudo dnf install python3
  Windows      https://www.python.org/downloads/ and check "Add python.exe to PATH"

Then rerun the same command, or set HK_PYTHON to the interpreter path.
EOF
exit 127
