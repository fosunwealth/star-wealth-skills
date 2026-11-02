#!/usr/bin/env bash
# Checks what a marketplace loader checks. Needs bash, python3, uv, and network on first run.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0

echo "== 1/2. plugin manifests"
uvx --with jsonschema python3 - <<'PY' || fail=1
import json, pathlib, sys, urllib.request
from jsonschema import Draft202012Validator
CURSOR = {"name","description","version","author","homepage","repository","license","keywords",
          "logo","rules","agents","skills","commands","hooks","mcpServers","variables"}
cache, bad = {}, 0
for root in sorted(pathlib.Path('.').glob('*/plugin.json')):
    d, doc, before = root.parent, json.loads(root.read_text()), bad
    url = doc.get('$schema')
    cache.setdefault(url, json.load(urllib.request.urlopen(url, timeout=25)))
    for e in sorted(Draft202012Validator(cache[url]).iter_errors(doc), key=lambda e: str(e.path)):
        print(f"FAIL {root}: {e.message}"); bad += 1
    cur = d / '.cursor-plugin' / 'plugin.json'
    if not cur.exists():
        print(f"FAIL {cur}: missing"); bad += 1; continue
    c = json.loads(cur.read_text())
    for cond, msg in ((set(c) - CURSOR, f"fields Cursor does not document: {sorted(set(c) - CURSOR)}"),
                      (not c.get('name'), "name is required"),
                      (set(c.get('author', {})) - {'name','email'}, "author takes name and email only"),
                      (c.get('logo') and not (d / c['logo']).is_file(), f"logo {c.get('logo')} does not exist"),
                      (c.get('name') != doc.get('name'), "the two manifests disagree on name")):
        if cond:
            print(f"FAIL {cur}: {msg}"); bad += 1
    if bad == before:
        print(f"ok   {root}")
print("manifests: " + ("FAIL" if bad else "all pass"))
sys.exit(1 if bad else 0)
PY

echo
echo "== 2b. team marketplace manifest"
python3 - <<'PY' || fail=1
import json, pathlib, re, sys
NAME = re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')
p = pathlib.Path('.cursor-plugin/marketplace.json')
if not p.exists():
    print('FAIL .cursor-plugin/marketplace.json is missing: Cursor reads it to import a multi-plugin repo'); sys.exit(1)
ms = json.loads(p.read_text()); bad = 0
if not NAME.match(str(ms.get('name', ''))): print('FAIL marketplace name must be kebab-case'); bad += 1
if not (ms.get('owner') or {}).get('name'): print('FAIL marketplace owner.name is required'); bad += 1
entries = ms.get('plugins') or []
if not entries: print('FAIL marketplace plugins must be a non-empty array'); bad += 1
root = (ms.get('metadata') or {}).get('pluginRoot') or ''
seen = []
for i, e in enumerate(entries):
    name, src = e.get('name', ''), e.get('source', '')
    if not NAME.match(str(name)): print(f'FAIL plugins[{i}].name must be kebab-case'); bad += 1
    if name in seen: print(f'FAIL duplicate plugin name {name}'); bad += 1
    seen.append(name)
    path = pathlib.PurePosixPath(root) / src if root else pathlib.PurePosixPath(src)
    if path.is_absolute() or '..' in path.parts:
        print(f'FAIL plugins[{i}].source is not a safe relative path'); bad += 1; continue
    d = pathlib.Path(*path.parts)
    m = d / '.cursor-plugin' / 'plugin.json'
    if not m.is_file(): print(f'FAIL {name}: {m} is missing'); bad += 1; continue
    if json.loads(m.read_text()).get('name') != name:
        print(f'FAIL {name}: marketplace name differs from plugin.json'); bad += 1
for m in sorted(pathlib.Path('.').glob('*/.cursor-plugin/plugin.json')):
    plugin = m.parent.parent.name
    if plugin not in seen:
        print(f'FAIL {plugin} is not listed in marketplace.json, so the marketplace hides it'); bad += 1
print('marketplace: ' + ('FAIL' if bad else 'all pass'))
sys.exit(1 if bad else 0)
PY

echo
echo "== 3. skills (official Agent Skills validator)"
for f in */skills/*/SKILL.md; do
  if out=$(uvx --from skills-ref agentskills validate "$(dirname "$f")" 2>&1); then
    printf 'ok   %s\n' "$(dirname "$f")"
  else
    printf 'FAIL %s\n%s\n' "$(dirname "$f")" "$(printf '%s' "$out" | sed 's/^/       /')"; fail=1
  fi
done

echo
echo "== 4. credentials, build output, host-only contract"
h=$(grep -RInE 'fsk_[A-Za-z0-9]{12,}|BEGIN ([A-Z]+ )?PRIVATE KEY-----[A-Za-z0-9+/=]{20,}|FSOPENAPI_API_KEY=[^[:space:]#]+|FINTRUST_API_KEY=[^[:space:]#]+' --include='*.md' --include='*.py' --include='*.json' --include='*.sh' --include='*.mjs' --include='*.ps1' . 2>/dev/null | grep -v '\.env\.example:' | grep -v '^\./scripts/check\.sh:' || true)
[ -n "$h" ] && { printf 'FAIL credential material\n%s\n' "$h"; fail=1; } || printf 'ok   no credential material\n'
h=$(grep -RInE 'present_files|connect_cloud_service|WorkBuddy (desktop|marketplace|sidebar|session)' --include='SKILL.md' --include='README.md' --include='subSKILL.md' . 2>/dev/null || true)
[ -n "$h" ] && { printf 'FAIL host-only contract in reader-facing files\n%s\n' "$h"; fail=1; } || printf 'ok   no host-only contract\n'
h=$(find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' -o -name 'node_modules' -o -name '.env' 2>/dev/null || true)
[ -n "$h" ] && { printf 'FAIL build output or untracked state\n%s\n' "$h"; fail=1; } || printf 'ok   no build output\n'
h=$(grep -RIni 'workbuddy' --include='SKILL.md' --include='README.md' --include='subSKILL.md' . 2>/dev/null || true)
[ -n "$h" ] && { printf 'FAIL a host name in reader-facing files\n%s\n' "$h"; fail=1; } || printf 'ok   no host name in reader-facing files\n'

echo
[ "$fail" -eq 0 ] && echo "PASS: ready to import as a team marketplace." || echo "FAIL: fix the lines above."
exit "$fail"
