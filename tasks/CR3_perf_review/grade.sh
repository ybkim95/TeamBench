#!/usr/bin/env bash
# Grade script for CR3: Performance Optimization from Profiler Report
# Arguments:
#   $1 = WORKSPACE  (directory containing the module and tests/)
#   $2 = REPORTS    (grader-only directory; contains expected.json)
#   $3 = SUBMISSION (directory where the agent writes attestation.json)
#   $4 = TASK_DIR   (task definition directory)
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

cd "$WORKSPACE"

EXPECTED="$REPORTS/expected.json"

# Read expected values once for reuse
MODULE_FILE=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['module_file'])" 2>/dev/null)
H1_FN=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['hotspot1_fn'])" 2>/dev/null)
H2_FN=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['hotspot2_fn'])" 2>/dev/null)
H3_FN=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['hotspot3_fn'])" 2>/dev/null)
BUDGET_MS=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['budget_ms'])" 2>/dev/null)

# ── Check 1: Module is syntactically valid Python ────────────────────────────
check "python3 -c \"
import py_compile, json
exp = json.load(open('$EXPECTED'))
py_compile.compile(exp['module_file'], doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── Check 2: Module runs without import errors ───────────────────────────────
check "python3 -c \"
import json, importlib.util, sys, os
exp = json.load(open('$EXPECTED'))
mod_file = exp['module_file']
spec = importlib.util.spec_from_file_location('mod', mod_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('IMPORT_OK')
\"" "import_error"

# ── Check 3: All tests pass (functional correctness preserved) ───────────────
check "python3 -m pytest tests/test_module.py -q --tb=short 2>&1 | tail -5 | grep -E '^[0-9]+ passed'" "tests_failing"

# ── Check 4: Hotspot 1 optimized — no O(n^2) nested loop over reference ─────
check "python3 -c \"
import json, ast, sys

exp = json.load(open('$EXPECTED'))
h1_fn = exp['hotspot1_fn']
mod_file = exp['module_file']

with open(mod_file) as f:
    src = f.read()
tree = ast.parse(src)

# Find the function definition
fn_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == h1_fn:
        fn_node = node
        break
assert fn_node is not None, f'{h1_fn} not found'

# Count nested For loops inside the function body
for_loops = [n for n in ast.walk(fn_node) if isinstance(n, ast.For)]
# An optimised version should have at most 1 for-loop (or zero with comprehension)
assert len(for_loops) <= 1, f'O(n^2) nested loops still present in {h1_fn}: {len(for_loops)} For nodes'
print('HOTSPOT1_OPTIMIZED')
\"" "hotspot1_not_optimized"

# ── Check 5: Hotspot 1 uses set/dict for O(1) lookup ────────────────────────
check "python3 -c \"
import json, ast

exp = json.load(open('$EXPECTED'))
h1_fn = exp['hotspot1_fn']
mod_file = exp['module_file']

with open(mod_file) as f:
    src = f.read()
tree = ast.parse(src)

fn_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == h1_fn:
        fn_node = node
        break
assert fn_node is not None

# Must contain a Set or Dict literal/comprehension, or call set()
has_set_or_dict = False
for node in ast.walk(fn_node):
    if isinstance(node, (ast.Set, ast.SetComp, ast.DictComp, ast.Dict)):
        has_set_or_dict = True
        break
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ('set', 'dict', 'frozenset'):
            has_set_or_dict = True
            break
        if isinstance(node.func, ast.Attribute) and node.func.attr in ('keys', 'values', 'items'):
            has_set_or_dict = True
            break
assert has_set_or_dict, f'{h1_fn} does not use a set/dict for O(1) lookup'
print('HOTSPOT1_USES_LOOKUP')
\"" "hotspot1_no_set_dict"

# ── Check 6: Hotspot 2 optimized — result is cached (cache dict or lru_cache) ─
check "python3 -c \"
import json, ast, re

exp = json.load(open('$EXPECTED'))
h2_fn = exp['hotspot2_fn']
mod_file = exp['module_file']

with open(mod_file) as f:
    src = f.read()

# Accept either functools.lru_cache decorator or a manual cache dict pattern
uses_lru = bool(re.search(r'lru_cache', src))

tree = ast.parse(src)
fn_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == h2_fn:
        fn_node = node
        break
assert fn_node is not None

# Check for lru_cache decorator
decorated = False
for dec in fn_node.decorator_list:
    dec_src = ast.unparse(dec) if hasattr(ast, 'unparse') else ''
    if 'cache' in dec_src.lower():
        decorated = True
        break

# Check for manual cache: subscript assignment (cache[key] = ...) anywhere in module
has_cache_assign = False
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Subscript):
                has_cache_assign = True
                break

# Check module-level dict that looks like a cache
has_module_dict = False
for node in tree.body:
    if isinstance(node, ast.Assign):
        if isinstance(node.value, ast.Dict) and len(node.value.keys) == 0:
            has_module_dict = True

assert uses_lru or decorated or has_cache_assign, \
    f'{h2_fn} does not appear to cache results (no lru_cache and no cache dict)'
print('HOTSPOT2_CACHED')
\"" "hotspot2_not_cached"

# ── Check 7: Hotspot 3 optimized — uses generator (yield or genexpr) ─────────
check "python3 -c \"
import json, ast

exp = json.load(open('$EXPECTED'))
h3_fn = exp['hotspot3_fn']
mod_file = exp['module_file']

with open(mod_file) as f:
    src = f.read()
tree = ast.parse(src)

fn_node = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == h3_fn:
        fn_node = node
        break
assert fn_node is not None, f'{h3_fn} not found'

# Must contain a Yield, YieldFrom, or GeneratorExp
has_generator = any(
    isinstance(n, (ast.Yield, ast.YieldFrom, ast.GeneratorExp))
    for n in ast.walk(fn_node)
)
# Must NOT build a list via list.append loop
has_append = any(
    isinstance(n, ast.Attribute) and n.attr == 'append'
    for n in ast.walk(fn_node)
)
assert has_generator, f'{h3_fn} does not yield or use a generator expression'
assert not has_append, f'{h3_fn} still uses list.append — generator pattern not applied'
print('HOTSPOT3_GENERATOR')
\"" "hotspot3_not_generator"

# ── Check 8: No O(n^2) patterns remain anywhere in the module ────────────────
check "python3 -c \"
import json, ast

exp = json.load(open('$EXPECTED'))
mod_file = exp['module_file']
h1_fn = exp['hotspot1_fn']

with open(mod_file) as f:
    src = f.read()
tree = ast.parse(src)

# Only check top-level functions (not helpers load_* or run_benchmark)
for node in tree.body:
    if not isinstance(node, ast.FunctionDef):
        continue
    if node.name.startswith('load_') or node.name == 'run_benchmark':
        continue
    # Count nested for-loops: a For inside another For = O(n^2) risk
    for child in ast.walk(node):
        if isinstance(child, ast.For):
            inner_fors = [n for n in ast.walk(child) if isinstance(n, ast.For) and n is not child]
            assert len(inner_fors) == 0, \
                f'Nested For loops remain in {node.name} — O(n^2) pattern not removed'
print('NO_N2_PATTERNS')
\"" "n2_patterns_remain"

# ── Check 9: Performance within budget (run_benchmark must complete in time) ──
check "python3 -c \"
import json, importlib.util, sys, os, time

exp = json.load(open('$EXPECTED'))
mod_file = exp['module_file']
budget_ms = exp['budget_ms']

spec = importlib.util.spec_from_file_location('mod', mod_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Run benchmark 3 times, take median
import statistics
times = []
for _ in range(3):
    times.append(mod.run_benchmark())
median_ms = statistics.median(times)

assert median_ms <= budget_ms, \
    f'Median benchmark {median_ms:.1f} ms exceeds budget {budget_ms} ms'
print(f'PERF_OK ({median_ms:.1f} ms <= {budget_ms} ms)')
\"" "perf_over_budget"

# ── Check 10: Attestation ─────────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
