#!/usr/bin/env bash
# PERF1_optimize_constrained grader
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

# ── Install dependencies ──────────────────────────────────────────────
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# Load expected values
EXPECTED_JSON="${REPORTS}/expected.json"
TIME_LIMIT_MS=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('time_limit_ms', 2500))" 2>/dev/null || echo "2500")
N_ITEMS=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('n_items', 1000))" 2>/dev/null || echo "1000")

# ── C1: Correctness tests pass ────────────────────────────────────────
if python3 -m pytest tests/test_correctness.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C1" "All correctness tests pass" "pass"
else
    check "C1" "Correctness tests failed" "fail"
fi

# ── C2: Benchmark passes under time limit ─────────────────────────────
if python3 benchmark.py --time-limit-ms "${TIME_LIMIT_MS}" 2>/dev/null | grep -q "BENCHMARK: PASS"; then
    check "C2" "Benchmark passes under ${TIME_LIMIT_MS}ms time limit" "pass"
else
    check "C2" "Benchmark failed: did not complete under ${TIME_LIMIT_MS}ms" "fail"
fi

# ── C3: B1 fix — blocked list converted to set ───────────────────────
MODULE=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print({'data_processor':'processor','report_generator':'reporter','search_engine':'search','event_aggregator':'aggregator','log_analyzer':'analyzer'}.get(d.get('domain',''), 'processor'))" 2>/dev/null || echo "processor")
result=$(python3 -c "
import ast, sys
src = open('${MODULE}.py').read()
tree = ast.parse(src)
# Check for set() or set comprehension in __init__
found = False
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '__init__':
        for n in ast.walk(node):
            if isinstance(n, (ast.Call, ast.Set, ast.SetComp)):
                found = True
                break
print('pass' if found else 'fail')
" 2>/dev/null || echo "fail")
check "C3" "B1 fix: blocked collection converted to set" "${result}"

# ── C4: B2 fix — copy.deepcopy removed ───────────────────────────────
result=$(python3 -c "
import ast, sys
src = open('${MODULE}.py').read()
# Check deepcopy is not called
found_deepcopy = 'deepcopy' in src and 'deepcopy(' in src
# Allow it in comments/strings only — check AST for actual Call
import ast
tree = ast.parse(src)
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
deepcopy_calls = [c for c in calls if (hasattr(c.func, 'attr') and c.func.attr == 'deepcopy') or (hasattr(c.func, 'id') and c.func.id == 'deepcopy')]
print('pass' if not deepcopy_calls else 'fail')
" 2>/dev/null || echo "fail")
check "C4" "B2 fix: copy.deepcopy removed from hot path" "${result}"

# ── C5: B3 fix — lru_cache applied ───────────────────────────────────
result=$(python3 -c "
src = open('${MODULE}.py').read()
print('pass' if 'lru_cache' in src else 'fail')
" 2>/dev/null || echo "fail")
check "C5" "B3 fix: lru_cache applied to expensive pure function" "${result}"

# ── C6: B4 fix — config cached in __init__ ───────────────────────────
result=$(python3 -c "
import ast
src = open('${MODULE}.py').read()
tree = ast.parse(src)
# Check __init__ assigns a config-derived attribute (int(_read_config(...)))
found = False
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '__init__':
        for n in ast.walk(node):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Attribute) and t.attr.startswith('_'):
                        found = True
print('pass' if found else 'fail')
" 2>/dev/null || echo "fail")
check "C6" "B4 fix: config value cached in __init__ attribute" "${result}"

# ── C7: S1 preserved — rate_limit_sleep still in export_results ───────
result=$(python3 -c "
import ast, inspect, importlib, sys
sys.path.insert(0, '.')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location('mod', '${MODULE}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = [v for v in vars(mod).values() if isinstance(v, type)][0]
    src = inspect.getsource(cls.export_results)
    print('pass' if 'time.sleep' in src else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C7" "S1 preserved: time.sleep in export_results" "${result}"

# ── C8: S2 preserved — stable sort key unchanged in sorted_results ────
result=$(python3 -c "
import inspect, importlib.util, sys, ast
sys.path.insert(0, '.')
try:
    spec = importlib.util.spec_from_file_location('mod', '${MODULE}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = [v for v in vars(mod).values() if isinstance(v, type)][0]
    src = inspect.getsource(cls.sorted_results)
    print('pass' if 'sorted(' in src and 'key=' in src else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C8" "S2 preserved: sorted_results uses sorted() with key=" "${result}"

# ── C9: filter function correctness — blocked items excluded ──────────
result=$(python3 -c "
import importlib.util, sys
sys.path.insert(0, '.')
try:
    spec = importlib.util.spec_from_file_location('mod', '${MODULE}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = [v for v in vars(mod).values() if isinstance(v, type)][0]
    obj = cls()
    # Determine id_field from first blocked entry
    first = list(obj._blocked)[0] if obj._blocked else 'blocked_x_0'
    id_field = first.rsplit('_', 1)[0].replace('blocked_', '')
    ds = [{id_field: 'blocked_' + id_field + '_0', 'amount': 1.0, 'score': 1.0, 'relevance': 1.0, 'magnitude': 1.0, 'latency_ms': 1.0}]
    methods = [m for m in dir(cls) if m.startswith('filter_')]
    if methods:
        result = getattr(obj, methods[0])(ds)
        print('pass' if len(result) == 0 else 'fail')
    else:
        print('fail')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C9" "Filter function correctly excludes blocked items" "${result}"

# ── C10: Primary function returns non-empty dict ──────────────────────
result=$(python3 -c "
import importlib.util, sys, random
sys.path.insert(0, '.')
try:
    spec = importlib.util.spec_from_file_location('mod', '${MODULE}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = [v for v in vars(mod).values() if isinstance(v, type)][0]
    obj = cls()
    # Build minimal dataset
    rng = random.Random(42)
    cats = ['cat_a', 'cat_b']
    ds = [{'record_id': f'item_{i}', 'entry_id': f'item_{i}', 'doc_id': f'item_{i}',
            'event_id': f'item_{i}', 'line_id': f'item_{i}',
            'amount': rng.uniform(1,10), 'score': rng.uniform(1,10),
            'relevance': rng.uniform(0.1,1), 'magnitude': rng.uniform(1,10),
            'latency_ms': rng.uniform(10,500),
            'category': rng.choice(cats), 'department': rng.choice(cats),
            'source': rng.choice(cats), 'event_type': rng.choice(cats),
            'service': rng.choice(cats)} for i in range(10)]
    primary_methods = [m for m in dir(cls) if m.startswith(('process_', 'generate_', 'search_', 'aggregate_', 'analyze_'))]
    if primary_methods:
        result = getattr(obj, primary_methods[0])(ds)
        print('pass' if isinstance(result, dict) and len(result) > 0 else 'fail')
    else:
        print('fail')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C10" "Primary function returns non-empty dict" "${result}"

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
