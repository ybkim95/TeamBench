#!/usr/bin/env bash
# TRAP6 grader: verify 5 callsites migrated + 3 vendored callsites preserved
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=10
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

cd "${WORKSPACE}"

# Install dependencies if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# C1: All Python files parse without SyntaxError
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, glob
for f in glob.glob('**/*.py', recursive=True):
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SyntaxError in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C1" "All Python files have valid syntax" "pass"
else
    check "C1" "Syntax error in one or more Python files" "fail"
fi

# -------------------------------------------------------------------
# C2: pytest tests/ passes overall
# -------------------------------------------------------------------
if python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C2" "pytest tests/ passes" "pass"
else
    check "C2" "pytest tests/ has failures" "fail"
fi

# -------------------------------------------------------------------
# C3-C10: Inline Python checks for migration correctness
# -------------------------------------------------------------------
(python3 - <<'PYEOF'
import json, sys, os, re, glob

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    # Load expected.json from reports dir to know which modules are vendored
    reports_dir = os.environ.get("REPORTS_DIR", "/reports")
    expected_path = os.path.join(reports_dir, "expected.json")
    if os.path.exists(expected_path):
        with open(expected_path) as f:
            expected = json.load(f)
        vendored_modules = expected.get("vendored_modules", [])
        migrate_modules = expected.get("migrate_modules", [])
    else:
        # Fallback: read VENDORED_DEPS.md to find vendored modules
        vendored_modules = []
        migrate_modules = []
        if os.path.exists("VENDORED_DEPS.md"):
            content = open("VENDORED_DEPS.md").read()
            # Find module names mentioned as vendored
            for line in content.splitlines():
                m = re.search(r'`(\w+\.py)`\s+.*vendored', line, re.I)
                if m:
                    vendored_modules.append(m.group(1).replace('.py', ''))

    # Scan all .py files in app/ for old_api and new_api usage
    old_api_files = []
    new_api_files = []
    for pyfile in sorted(glob.glob('app/*.py')):
        content = open(pyfile).read()
        modname = os.path.basename(pyfile).replace('.py', '')
        if modname == '__init__':
            continue
        has_old = bool(re.search(r'old_api\.', content))
        has_new = bool(re.search(r'new_api\.', content))
        if has_old:
            old_api_files.append(modname)
        if has_new:
            new_api_files.append(modname)

    # C3: Vendored modules still use old_api
    vendored_preserved = 0
    for vm in vendored_modules:
        pypath = f'app/{vm}.py'
        if os.path.exists(pypath):
            content = open(pypath).read()
            if re.search(r'old_api\.', content):
                vendored_preserved += 1
    results["C3"] = vendored_preserved == len(vendored_modules)

    # C4: Vendored modules do NOT use new_api
    vendored_no_new = 0
    for vm in vendored_modules:
        pypath = f'app/{vm}.py'
        if os.path.exists(pypath):
            content = open(pypath).read()
            if not re.search(r'new_api\.', content):
                vendored_no_new += 1
    results["C4"] = vendored_no_new == len(vendored_modules)

    # C5: Migrate modules use new_api
    migrated_count = 0
    for mm in migrate_modules:
        pypath = f'app/{mm}.py'
        if os.path.exists(pypath):
            content = open(pypath).read()
            if re.search(r'new_api\.', content):
                migrated_count += 1
    results["C5"] = migrated_count == len(migrate_modules)

    # C6: Migrate modules do NOT use old_api
    migrate_no_old = 0
    for mm in migrate_modules:
        pypath = f'app/{mm}.py'
        if os.path.exists(pypath):
            content = open(pypath).read()
            if not re.search(r'old_api\.', content):
                migrate_no_old += 1
    results["C6"] = migrate_no_old == len(migrate_modules)

    # C7: old_api module still exists and is importable
    results["C7"] = os.path.exists("app/old_api.py") or os.path.exists("lib/old_api.py")

    # C8: new_api module exists and is importable
    results["C8"] = os.path.exists("app/new_api.py") or os.path.exists("lib/new_api.py")

except Exception as e:
    for k in ["C3","C4","C5","C6","C7","C8"]:
        results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/trap6_results.json 2>/tmp/trap6_err.txt || true

# Parse inline test results
if [ -f /tmp/trap6_results.json ]; then
    for cid in C3 C4 C5 C6 C7 C8; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/trap6_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C3) check "C3" "Vendored modules still use old_api (preserved)" "$val" ;;
            C4) check "C4" "Vendored modules do not use new_api (no false migration)" "$val" ;;
            C5) check "C5" "Non-vendored modules migrated to new_api" "$val" ;;
            C6) check "C6" "Non-vendored modules no longer use old_api" "$val" ;;
            C7) check "C7" "old_api module still exists (not deleted)" "$val" ;;
            C8) check "C8" "new_api module exists and is available" "$val" ;;
        esac
    done
else
    for cid in C3 C4 C5 C6 C7 C8; do
        check "$cid" "Inline test harness failed to run" "fail"
    done
fi

# -------------------------------------------------------------------
# C9: Vendored integration tests pass
# -------------------------------------------------------------------
if python3 -m pytest tests/test_vendored_compat.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C9" "Vendored integration tests pass" "pass"
else
    check "C9" "Vendored integration tests failed" "fail"
fi

# -------------------------------------------------------------------
# C10: Migration tests pass
# -------------------------------------------------------------------
if python3 -m pytest tests/test_migration.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C10" "Migration tests pass" "pass"
else
    check "C10" "Migration tests failed" "fail"
fi

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
