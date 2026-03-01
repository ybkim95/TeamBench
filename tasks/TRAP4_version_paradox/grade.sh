#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=12
findings=""

check() {
    local id="$1" desc="$2" result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

cd "${WORKSPACE}"
pip install pytest --quiet 2>/dev/null || true

# C1: pytest passes
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "All tests pass" "pass"
else
    check "C1" "Tests failing" "fail"
fi

# C2: test_v3_api.py passes
if python -m pytest tests/test_v3_api.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C2" "test_v3_api.py passes" "pass"
else
    check "C2" "test_v3_api.py failing" "fail"
fi

# C3: test_adapter.py passes
if python -m pytest tests/test_adapter.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C3" "test_adapter.py passes (legacy_adapter compat)" "pass"
else
    check "C3" "test_adapter.py failing (legacy_adapter broken)" "fail"
fi

# C4: test_deprecation.py passes
if python -m pytest tests/test_deprecation.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C4" "test_deprecation.py passes (DeprecationWarnings emitted)" "pass"
else
    check "C4" "test_deprecation.py failing" "fail"
fi

python3 <<'PYEOF' > /tmp/trap4_results.json 2>/dev/null || echo '{}' > /tmp/trap4_results.json
import sys, json, importlib.util, warnings, os
sys.path.insert(0, '.')
results = {}

# C5: v3 API exists: run(), results(), configure(), Query
try:
    import mylib
    results['C5'] = all(hasattr(mylib, x) for x in ['run', 'results', 'configure', 'Query'])
except:
    results['C5'] = False

# C6: v2 shims connect_v2 and QueryBuilder still importable from mylib
try:
    import mylib
    results['C6'] = hasattr(mylib, 'connect_v2') and hasattr(mylib, 'QueryBuilder')
except:
    results['C6'] = False

# C7: connect_v2 emits DeprecationWarning
try:
    import mylib
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mylib.connect_v2("localhost")
        results['C7'] = any(issubclass(x.category, DeprecationWarning) for x in w)
except:
    results['C7'] = False

# C8: QueryBuilder emits DeprecationWarning
try:
    import mylib
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mylib.QueryBuilder()
        results['C8'] = any(issubclass(x.category, DeprecationWarning) for x in w)
except:
    results['C8'] = False

# C9: legacy_adapter imports successfully
try:
    sys.path.insert(0, 'vendor')
    import legacy_adapter
    results['C9'] = True
except:
    results['C9'] = False

# C10: v2 shims are in compat.py not core.py
try:
    core_src = open('mylib/core.py').read()
    compat_src = open('mylib/compat.py').read() if os.path.exists('mylib/compat.py') else ''
    results['C10'] = 'connect_v2' not in core_src and 'connect_v2' in compat_src
except:
    results['C10'] = False

# C11: execute() v2 pattern removed from public API
try:
    import mylib
    results['C11'] = not hasattr(mylib, 'execute') or hasattr(mylib, 'run')
except:
    results['C11'] = True

# C12: Syntax validity
try:
    import py_compile
    for f in ['mylib/__init__.py', 'mylib/core.py', 'mylib/compat.py']:
        if os.path.exists(f):
            py_compile.compile(f, doraise=True)
    results['C12'] = True
except:
    results['C12'] = False

print(json.dumps(results))
PYEOF

for cid in C5 C6 C7 C8 C9 C10 C11 C12; do
    val=$(python3 -c "import json; d=json.load(open('/tmp/trap4_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
    case "$cid" in
        C5) check "C5" "v3 API (run/results/configure/Query) exists" "$val" ;;
        C6) check "C6" "v2 shims (connect_v2/QueryBuilder) still importable" "$val" ;;
        C7) check "C7" "connect_v2 emits DeprecationWarning" "$val" ;;
        C8) check "C8" "QueryBuilder emits DeprecationWarning" "$val" ;;
        C9) check "C9" "vendor/legacy_adapter imports cleanly" "$val" ;;
        C10) check "C10" "v2 shims in compat.py not core.py" "$val" ;;
        C11) check "C11" "Old v2 execute() removed from public API" "$val" ;;
        C12) check "C12" "Syntax valid" "$val" ;;
    esac
done

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"
mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {"partial_score": $partial_score, "checks_passed": $partial, "checks_total": $total},
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
