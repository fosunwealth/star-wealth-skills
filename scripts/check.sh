#!/usr/bin/env bash
# Checks what a marketplace loader checks. Needs bash, python3, uv, and network on first run.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0

echo "== 1/2. plugin manifests (Agent Plugins 1.0.0)"
uvx --with jsonschema python3 - <<'PY' || fail=1
import json, pathlib, sys, urllib.request
from jsonschema import Draft202012Validator
cache, bad = {}, 0

def schema(url):
    last = None
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(url, timeout=25))
        except Exception as e:
            last = e
    print(f"FAIL cannot load {url}: {last}")
    sys.exit(1)

for root in sorted(pathlib.Path('.').glob('*/plugin.json')):
    doc, before = json.loads(root.read_text()), bad
    url = doc.get('$schema')
    if url not in cache:
        cache[url] = schema(url)
    for e in sorted(Draft202012Validator(cache[url]).iter_errors(doc), key=lambda e: str(e.path)):
        print(f"FAIL {root}: {e.message}"); bad += 1
    if bad == before:
        print(f"ok   {root}")
print("manifests: " + ("FAIL" if bad else "all pass"))
sys.exit(1 if bad else 0)
PY

echo
echo "== 2b. Cursor manifests (Cursor's own schemas)"
uvx --with jsonschema python3 - <<'PY' || fail=1
# The schemas are Cursor's, not ours: fetched from cursor/plugins so this gate cannot drift.
# https://github.com/cursor/plugins/tree/HEAD/schemas
import json, pathlib, sys, urllib.request
from jsonschema import Draft7Validator

BASE = "https://raw.githubusercontent.com/cursor/plugins/HEAD/schemas/"
MANIFESTS = ('.cursor-plugin/plugin.json', '.claude-plugin/plugin.json', 'plugin.json')
bad = 0

def fail(msg):
    global bad
    bad += 1
    print(f"FAIL {msg}")

def schema(name):
    last = None
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(BASE + name, timeout=25))
        except Exception as e:
            last = e
    print(f"FAIL cannot load Cursor's {name} from {BASE}: {last}")
    sys.exit(1)

def check(doc, sch, label):
    n = 0
    for e in sorted(Draft7Validator(sch).iter_errors(doc), key=lambda e: list(e.absolute_path)):
        extra = f' ("{e.validator_value}")' if e.validator == 'additionalProperties' else ''
        fail(f"{label}: {list(e.absolute_path) or '/'}: {e.message}{extra}")
        n += 1
    return n

marketplace_schema = schema('marketplace.schema.json')
plugin_schema = schema('plugin.schema.json')

p = pathlib.Path('.cursor-plugin/marketplace.json')
if not p.exists():
    fail(".cursor-plugin/marketplace.json is missing: Cursor reads it to import a multi-plugin repo")
    sys.exit(1)

ms = json.loads(p.read_text())
check(ms, marketplace_schema, '.cursor-plugin/marketplace.json')

entries = ms.get('plugins') or []
if not entries:
    fail("marketplace plugins must be a non-empty array")

seen = set()
for i, entry in enumerate(entries):
    name, src = entry.get('name', ''), entry.get('source', '')
    if name in seen:
        fail(f"plugins[{i}]: duplicate plugin name {name}")
    seen.add(name)

    path = pathlib.PurePosixPath(src)
    if path.is_absolute() or '..' in path.parts:
        fail(f"plugins[{i}]: source is not a safe relative path")
        continue
    d = pathlib.Path(*path.parts)
    if not d.is_dir():
        fail(f"{name}: source directory {src} does not exist")
        continue

    manifest = d / '.cursor-plugin/plugin.json'
    if not manifest.is_file():
        fail(f"{name}: {manifest} is missing")
        continue

    doc = json.loads(manifest.read_text())
    ok = check(doc, plugin_schema, manifest.as_posix()) == 0
    if doc.get('name') != name:
        fail(f"{name}: marketplace name does not match plugin.json name {doc.get('name')}")
        ok = False

    logo = doc.get('logo')
    if logo and not (d / logo).is_file():
        fail(f"{name}: logo {logo} does not exist")
        ok = False

    versions = {m: json.loads((d / m).read_text()).get('version')
                for m in MANIFESTS if (d / m).is_file()}
    versions = {m: v for m, v in versions.items() if v is not None}
    if len(set(versions.values())) > 1:
        fail(f"{name}: manifest versions differ: {versions}")
        ok = False

    if ok:
        print(f"ok   {manifest.as_posix()}")

for manifest in sorted(pathlib.Path('.').glob('*/.cursor-plugin/plugin.json')):
    plugin = manifest.parent.parent.name
    if plugin not in seen:
        fail(f"{plugin} is not listed in marketplace.json, so the marketplace hides it")

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
# 内容扫描只覆盖会进库的东西：已跟踪的文件，加上没被 .gitignore 忽略的新文件。
# 本机自留的目录（config_md/）因此不进任何一条内容扫描，和它进不了提交是同一个道理。
scan() { git ls-files -z -co --exclude-standard | xargs -0 grep -nIE "$@" 2>/dev/null || true; }

h=$(scan 'fsk_[A-Za-z0-9]{12,}|BEGIN ([A-Z]+ )?PRIVATE KEY-----[A-Za-z0-9+/=]{20,}|FSOPENAPI_API_KEY=[^[:space:]#]+|FINTRUST_API_KEY=[^[:space:]#]+' | grep -v '\.env\.example:' | grep -v '^scripts/check\.sh:' || true)
[ -n "$h" ] && { printf 'FAIL credential material\n%s\n' "$h"; fail=1; } || printf 'ok   no credential material\n'
h=$(scan 'present_files|connect_cloud_service|WorkBuddy (desktop|marketplace|sidebar|session)' | grep -E 'SKILL\.md:|README\.md:|subSKILL\.md:' || true)
[ -n "$h" ] && { printf 'FAIL host-only contract in reader-facing files\n%s\n' "$h"; fail=1; } || printf 'ok   no host-only contract\n'
# 这一条故意扫全树，包括被忽略的文件：本地多出一个 .env 就要有人看一眼。
# 只跳过 .git 和明确自留的目录，别的一律不放过。
h=$(find . -path ./.git -prune -o -path ./config_md -prune -o \( -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' -o -name 'node_modules' -o -name '.env' \) -print 2>/dev/null || true)
[ -n "$h" ] && { printf 'FAIL build output or untracked state\n%s\n' "$h"; fail=1; } || printf 'ok   no build output\n'
h=$(scan -i 'workbuddy' | grep -E 'SKILL\.md:|README\.md:|subSKILL\.md:' || true)
[ -n "$h" ] && { printf 'FAIL a host name in reader-facing files\n%s\n' "$h"; fail=1; } || printf 'ok   no host name in reader-facing files\n'

echo
[ "$fail" -eq 0 ] && echo "PASS: ready to import as a team marketplace." || echo "FAIL: fix the lines above."
exit "$fail"
