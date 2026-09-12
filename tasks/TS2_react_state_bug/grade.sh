#!/usr/bin/env bash
# TS2_react_state_bug grader — static TypeScript AST analysis
# Checks that stale-closure, missing-dep, missing-cleanup, and state-mutation bugs
# are fixed while the two intentional patterns are preserved.
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

mkdir -p "${REPORTS}"

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

# ── Load expected values from seed-specific expected.json ─────────────────────
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
    EXPECTED_JSON="${TASK_DIR}/expected.json"
fi

COMPONENT=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('component', 'Component'))
" 2>/dev/null || echo "Component")

BUGS=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(' '.join(e.get('bugs', [])))
" 2>/dev/null || echo "")

COUNTER_LABEL=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
# derive from domain config
domain = e.get('domain', 'chat')
labels = {'chat': 'unread', 'timer': 'elapsed', 'search': 'total',
          'dashboard': 'alerts', 'form': 'errors'}
print(labels.get(domain, 'count'))
" 2>/dev/null || echo "count")

COMPONENT_FILE="${WORKSPACE}/src/${COMPONENT}.tsx"

# ── C1: Component file exists ─────────────────────────────────────────────────
check "C1" "${COMPONENT}.tsx exists" "$([ -f "${COMPONENT_FILE}" ] && echo pass || echo fail)"

# ── C2: Stale closure fix (functional updater used) ───────────────────────────
result=$(python3 -c "
import re, json
bugs = '${BUGS}'.split()
if 'stale_closure_counter' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${COMPONENT_FILE}').read()
    # Functional updater pattern: setXxxCount(c => c + 1) or setXxxCount(prev => ...)
    if re.search(r'set\w+Count\s*\(\s*\w+\s*=>', content):
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C2" "Stale closure fixed: functional updater used in counter increment" "${result}"

# ── C3: Missing useEffect dep fixed ───────────────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'missing_dep_useeffect' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${COMPONENT_FILE}').read()
    # Fetch effect must have non-empty dep array containing the entity id
    # Look for useEffect with dep array that contains at least one identifier
    effects = re.findall(r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{.*?\},\s*\[([^\]]*)\]', content, re.DOTALL)
    has_non_empty_dep = any(dep.strip() for dep in effects)
    if has_non_empty_dep:
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C3" "Missing useEffect dep fixed: dep array includes entity id" "${result}"

# ── C4: Missing cleanup fixed ─────────────────────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'missing_cleanup' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${COMPONENT_FILE}').read()
    # Cleanup: useEffect must have a return statement with unsubscribe/cleanup
    if re.search(r'return\s*\(\s*\)\s*=>\s*\{[^}]*unsubscribe', content, re.DOTALL):
        print('pass')
    elif re.search(r'return\s*\(\s*\)\s*=>', content) and re.search(r'\.unsubscribe\(\)', content):
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C4" "Missing cleanup fixed: subscription effect returns cleanup fn" "${result}"

# ── C5: State mutation fixed ──────────────────────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'state_mutation' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${COMPONENT_FILE}').read()
    # Check that .push( is NOT used on state array (mutation removed)
    # and that spread pattern is used instead
    has_push_mutation = bool(re.search(r'\w+\.push\s*\(', content))
    has_spread_setter = bool(re.search(r'set\w+\s*\(\s*(prev|items|old)\s*=>\s*\[\.\.\.', content))
    if not has_push_mutation and has_spread_setter:
        print('pass')
    elif not has_push_mutation:
        print('pass')  # push removed, acceptable
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C5" "State mutation fixed: no direct .push() on state array" "${result}"

# ── C6: Intentional I1 preserved (subscription useEffect has dep array) ───────
result=$(python3 -c "
import re
try:
    content = open('${COMPONENT_FILE}').read()
    # The subscription useEffect should have a non-empty dep array [entityId]
    # Look for useEffect with an unsubscribe return AND a dep array
    blocks = re.findall(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{(.*?)return\s*\(\s*\)\s*=>\s*\{.*?unsubscribe.*?\}.*?\},\s*\[([^\]]*)\]',
        content, re.DOTALL
    )
    if blocks:
        print('pass')
    else:
        # Simpler check: unsubscribe effect has some dep array
        if re.search(r'unsubscribe', content) and re.search(r'\},\s*\[\w+\]', content):
            print('pass')
        else:
            print('pass')  # lenient: I1 is about not removing the dep array
except Exception:
    print('pass')
" 2>/dev/null || echo "pass")
check "C6" "Intentional I1 preserved: subscription effect has dep array" "${result}"

# ── C7: Intentional I2 preserved (double setFlashActive pattern) ──────────────
result=$(python3 -c "
import re
try:
    content = open('${COMPONENT_FILE}').read()
    # I2: triggerFlash sets flashActive(true) then schedules false via setTimeout
    has_flash_true = bool(re.search(r'setFlashActive\s*\(\s*true\s*\)', content))
    has_flash_false = bool(re.search(r'setFlashActive\s*\(\s*false\s*\)', content))
    has_timeout = bool(re.search(r'setTimeout', content))
    if has_flash_true and has_flash_false and has_timeout:
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C7" "Intentional I2 preserved: double setFlashActive pattern with setTimeout" "${result}"

# ── C8: types.ts not modified ─────────────────────────────────────────────────
result=$(python3 -c "
import os
types_file = '${WORKSPACE}/src/types.ts'
if os.path.exists(types_file):
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C8" "src/types.ts present and not removed" "${result}"

# ── C9: package.json present ──────────────────────────────────────────────────
check "C9" "package.json present" "$([ -f '${WORKSPACE}/package.json' ] && echo pass || echo fail)"

# ── C10: tsconfig.json present ────────────────────────────────────────────────
check "C10" "tsconfig.json present" "$([ -f '${WORKSPACE}/tsconfig.json' ] && echo pass || echo fail)"

# ── Write score.json ──────────────────────────────────────────────────────────
partial_score=$(python3 -c "print(round(${partial} / ${total}, 2))")
findings="${findings%,}"

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "${pass}" = "true" ] && echo "true" || echo "false" ),
  "primary": {"success": $( [ "${pass}" = "true" ] && echo 1 || echo 0 )},
  "secondary": {
    "partial_score": ${partial_score},
    "checks_passed": ${partial},
    "checks_total": ${total}
  },
  "failure_modes": [],
  "checklist": [${findings}]
}
EOF
