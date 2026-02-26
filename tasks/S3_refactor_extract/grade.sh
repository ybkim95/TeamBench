#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

# ── Load seed-specific expected values ─────────────────────────────────────
EXPECTED_JSON="$REPORTS/expected.json"

APP_TYPE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('app_type','web_api'))")
MONOLITH_FILE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('monolith_file','app.py'))")
MODULES_JSON=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('modules',[])))")
MODULES=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(' '.join(d.get('modules',[])))")
MODULE_COUNT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(len(d.get('modules',[])))")
PUBLIC_APIS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('public_apis',{})))")
MODULE_CONTENTS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('module_contents',{})))")
IMPORT_RULES=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('import_rules',''))")

cd "$WORKSPACE"

# ── CHECK 1: Correct number of new module files exist ──────────────────────
check "python3 -c \"
import json, os
modules = json.loads('$MODULES_JSON')
missing = [m for m in modules if not os.path.isfile(m + '.py')]
assert not missing, f'Missing module files: {missing}'
print('MODULE_FILES_OK')
\"" "missing_module_files"

# ── CHECK 2: Each module is independently importable ───────────────────────
check "python3 -c \"
import json, subprocess, sys, os
modules = json.loads('$MODULES_JSON')
for m in modules:
    r = subprocess.run(
        [sys.executable, '-c', f'import {m}; print(\"ok\")'],
        capture_output=True, text=True, cwd='$WORKSPACE'
    )
    assert r.returncode == 0, f'{m} not independently importable: {r.stderr}'
print('INDEPENDENT_IMPORT_OK')
\"" "module_not_independently_importable"

# ── CHECK 3: No circular imports ───────────────────────────────────────────
check "python3 -c \"
import json, subprocess, sys
modules = json.loads('$MODULES_JSON')
import_all = '; '.join(f'import {m}' for m in modules)
r = subprocess.run(
    [sys.executable, '-c', import_all + '; print(\"no_circular\")'],
    capture_output=True, text=True, cwd='$WORKSPACE'
)
assert r.returncode == 0, f'Circular import detected: {r.stderr}'
print('NO_CIRCULAR_OK')
\"" "circular_imports_detected"

# ── CHECK 4: Public APIs present in each module ────────────────────────────
check "python3 -c \"
import json, sys
sys.path.insert(0, '$WORKSPACE')
public_apis = json.loads(r'''$PUBLIC_APIS''')
for mod_name, api_items in public_apis.items():
    mod = __import__(mod_name)
    for item in api_items:
        assert hasattr(mod, item), f'{mod_name}.{item} missing from public API'
print('PUBLIC_API_OK')
\"" "public_api_missing"

# ── CHECK 5: Correct contents in each module (functions/classes) ───────────
check "python3 -c \"
import json, sys, inspect
sys.path.insert(0, '$WORKSPACE')
contents = json.loads(r'''$MODULE_CONTENTS''')
for mod_name, expected_items in contents.items():
    mod = __import__(mod_name)
    for item in expected_items:
        assert hasattr(mod, item), f'Expected {item} in {mod_name} but not found'
print('MODULE_CONTENTS_OK')
\"" "module_contents_wrong"

# ── CHECK 6: Existing tests pass ───────────────────────────────────────────
check "python3 -m pytest tests/ -q --tb=no -p no:cacheprovider 2>&1 | tail -1 | grep -E '^[0-9]+ passed'" "tests_fail"

# ── CHECK 7: All tests pass (zero failures) ────────────────────────────────
check "python3 -m pytest tests/ -q --tb=no -p no:cacheprovider 2>&1 | grep -v 'warning' | grep -qv 'failed'" "tests_have_failures"

# ── CHECK 8: Monolith no longer contains all business logic ────────────────
# (either deleted or reduced to <20 lines)
check "python3 -c \"
import os
mf = '$MONOLITH_FILE'
if not os.path.exists(mf):
    print('MONOLITH_GONE_OK')
else:
    lines = [l for l in open(mf).readlines() if l.strip() and not l.strip().startswith('#')]
    assert len(lines) < 20, f'Monolith {mf} still has {len(lines)} non-blank lines — not split'
    print('MONOLITH_THINNED_OK')
\"" "monolith_not_split"

# ── CHECK 9: Total line count roughly preserved (no mass deletions) ─────────
check "python3 -c \"
import json, os, ast
modules = json.loads('$MODULES_JSON')
total_lines = sum(
    len(open(m + '.py').readlines())
    for m in modules if os.path.isfile(m + '.py')
)
# original monolith was 200-500 lines; we require new modules have at least 80 lines total
assert total_lines >= 80, f'New modules only have {total_lines} lines — functionality likely deleted'
print('LINE_COUNT_OK')
\"" "too_few_lines"

# ── CHECK 10: Import dependency rules respected ─────────────────────────────
check "python3 -c \"
import json, ast, os
modules = json.loads('$MODULES_JSON')
import_rules = '$IMPORT_RULES'

# Build actual import graph: which modules import which other modules
def get_imports(filepath):
    try:
        tree = ast.parse(open(filepath).read())
    except:
        return set()
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports & set(modules)

module_imports = {}
for m in modules:
    fp = m + '.py'
    if os.path.isfile(fp):
        module_imports[m] = get_imports(fp)

# Check no circular imports exist in the graph
def has_cycle(graph):
    visited = set()
    def dfs(node, path):
        if node in path:
            return True
        if node in visited:
            return False
        path.add(node)
        for neighbor in graph.get(node, set()):
            if dfs(neighbor, path):
                return True
        path.discard(node)
        visited.add(node)
        return False
    return any(dfs(n, set()) for n in graph)

assert not has_cycle(module_imports), f'Circular import in module graph: {module_imports}'
print('IMPORT_RULES_OK')
\"" "import_rules_violated"

# ── CHECK 11: Each module file is non-empty (>5 lines) ─────────────────────
check "python3 -c \"
import json, os
modules = json.loads('$MODULES_JSON')
for m in modules:
    fp = m + '.py'
    if os.path.isfile(fp):
        lines = [l for l in open(fp).readlines() if l.strip()]
        assert len(lines) >= 5, f'{m}.py has only {len(lines)} non-blank lines'
print('MODULE_NONEMPTY_OK')
\"" "module_file_too_small"

# ── CHECK 12: Attestation ──────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# ── Score ──────────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
