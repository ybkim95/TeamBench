#!/usr/bin/env bash
# Grader for MULTI4: Monorepo Dependency Fix
# Fixes required:
#   B1: circular import (models -> api -> core -> models)
#   B2: stale version pin in utils/setup.cfg (core==X.Y -> core>=X.Y)
#   B3: moved function (worker imports from core.processing, should be utils.processing)
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

# ── Discover seed-parameterized package names from expected.json ─────────────
EXPECTED="$REPORTS/expected.json"

CORE_PKG=$(python3 -c "
import json, os
d = json.load(open('$EXPECTED'))
domain = d.get('domain', 'webapp')
m = {'webapp': 'core', 'dataplatform': 'engine', 'mlpipe': 'framework'}
print(m.get(domain, 'core'))
" 2>/dev/null || echo "core")

MODELS_PKG=$(python3 -c "
import json
d = json.load(open('$EXPECTED'))
domain = d.get('domain', 'webapp')
m = {'webapp': 'models', 'dataplatform': 'schemas', 'mlpipe': 'definitions'}
print(m.get(domain, 'models'))
" 2>/dev/null || echo "models")

API_PKG=$(python3 -c "
import json
d = json.load(open('$EXPECTED'))
domain = d.get('domain', 'webapp')
m = {'webapp': 'api', 'dataplatform': 'gateway', 'mlpipe': 'serving'}
print(m.get(domain, 'api'))
" 2>/dev/null || echo "api")

WORKER_PKG=$(python3 -c "
import json
d = json.load(open('$EXPECTED'))
domain = d.get('domain', 'webapp')
m = {'webapp': 'worker', 'dataplatform': 'scheduler', 'mlpipe': 'trainer'}
print(m.get(domain, 'worker'))
" 2>/dev/null || echo "worker")

UTILS_PKG=$(python3 -c "
import json
d = json.load(open('$EXPECTED'))
domain = d.get('domain', 'webapp')
m = {'webapp': 'utils', 'dataplatform': 'toolkit', 'mlpipe': 'helpers'}
print(m.get(domain, 'utils'))
" 2>/dev/null || echo "utils")

# ── Check 1 (B1): models/helpers.py does NOT import from api package ─────────
check "python3 -c \"
import ast
with open('${MODELS_PKG}/helpers.py') as f:
    source = f.read()
tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        assert not node.module.startswith('${API_PKG}.'), (
            f'Circular import still present: {node.module} in ${MODELS_PKG}/helpers.py'
        )
print('B1_NO_CIRCULAR_IMPORT_OK')
\"" "B1_circular_import_not_fixed"

# ── Check 2 (B1): models package imports successfully (no circular dep) ───────
check "python3 -c \"
import sys, importlib
to_remove = [k for k in list(sys.modules.keys())
             if k.startswith(('${MODELS_PKG}', '${API_PKG}', '${CORE_PKG}', '${UTILS_PKG}'))]
for k in to_remove:
    del sys.modules[k]
mod = importlib.import_module('${MODELS_PKG}.helpers')
assert hasattr(mod, 'serialize_entity'), 'serialize_entity missing from ${MODELS_PKG}.helpers'
print('B1_MODELS_IMPORT_OK')
\"" "B1_models_import_fails"

# ── Check 3 (B1): dependency graph has no cycles ──────────────────────────────
check "python3 -c \"
import ast, os
packages = ['${CORE_PKG}', '${MODELS_PKG}', '${API_PKG}', '${WORKER_PKG}', '${UTILS_PKG}']
graph = {pkg: set() for pkg in packages}
for pkg in packages:
    for suffix in ['__init__', 'helpers', 'entities', 'endpoints', 'formatters',
                   'tasks', 'processing', 'base']:
        path = f'{pkg}/{suffix}.py'
        try:
            with open(path) as f:
                source = f.read()
        except FileNotFoundError:
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                dep_pkg = node.module.split('.')[0]
                if dep_pkg in packages and dep_pkg != pkg:
                    graph[pkg].add(dep_pkg)
visited = set()
in_stack = set()
def has_cycle(node):
    visited.add(node)
    in_stack.add(node)
    for neighbor in graph.get(node, []):
        if neighbor in in_stack:
            return True
        if neighbor not in visited and has_cycle(neighbor):
            return True
    in_stack.discard(node)
    return False
for pkg in packages:
    if pkg not in visited:
        assert not has_cycle(pkg), f'Circular dependency still exists involving {pkg}'
print('B1_DEPENDENCY_GRAPH_ACYCLIC_OK')
\"" "B1_dependency_graph_cyclic"

# ── Check 4 (B2): utils/setup.cfg does NOT have stale exact version pin ───────
check "python3 -c \"
import configparser
config = configparser.ConfigParser()
config.read('${UTILS_PKG}/setup.cfg')
raw = config.get('options', 'install_requires', fallback='')
deps = [l.strip() for l in raw.strip().splitlines() if l.strip()]
core_deps = [d for d in deps if d.startswith('${CORE_PKG}')]
assert len(core_deps) >= 1, 'No ${CORE_PKG} dependency found in ${UTILS_PKG}/setup.cfg'
dep = core_deps[0]
assert '==' not in dep, f'Stale exact pin still present: {dep}'
assert '>=' in dep, f'Must use >= constraint, got: {dep}'
print(f'B2_VERSION_PIN_OK: {dep}')
\"" "B2_stale_version_pin_not_fixed"

# ── Check 5 (B2): version constraint tests pass ───────────────────────────────
check "python3 -m pytest tests/test_versions.py -q --tb=short 2>&1 | tail -3 | grep -qE 'passed|no tests'" \
  "B2_version_tests_fail"

# ── Check 6 (B3): worker/tasks.py imports moved function from utils, not core ─
check "python3 -c \"
import ast
with open('${WORKER_PKG}/tasks.py') as f:
    source = f.read()
tree = ast.parse(source)
still_from_core = False
from_utils = False
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom) and node.module:
        names = [a.name for a in node.names]
        if node.module == '${CORE_PKG}.processing' and len(names) > 0:
            # Only validate_input/normalize_output are allowed to stay in core
            bad = [n for n in names if n not in ('validate_input', 'normalize_output')]
            if bad:
                still_from_core = True
        if node.module == '${UTILS_PKG}.processing':
            from_utils = True
assert not still_from_core, 'Worker still imports moved function from ${CORE_PKG}.processing'
assert from_utils, 'Worker does not import moved function from ${UTILS_PKG}.processing'
print('B3_WORKER_IMPORT_OK')
\"" "B3_moved_function_not_fixed"

# ── Check 7 (B3): worker task runs correctly after import fix ─────────────────
check "python3 -c \"
import sys, importlib, inspect
to_remove = [k for k in list(sys.modules.keys())
             if k.startswith(('${WORKER_PKG}', '${CORE_PKG}', '${UTILS_PKG}'))]
for k in to_remove:
    del sys.modules[k]
mod = importlib.import_module('${WORKER_PKG}.tasks')
# Look for the batch/convenience function (returns list), not the moved function itself
# Batch helpers: run_batch, schedule_job, train_model — they take a list and return list
batch_helpers = [name for name, obj in inspect.getmembers(mod, inspect.isfunction)
                 if not name.startswith('_') and not name[0].isupper()
                 and name not in ('process_item', 'transform_record', 'execute_step')]
assert len(batch_helpers) >= 1, f'No batch helper functions in ${WORKER_PKG}.tasks'
fn = getattr(mod, batch_helpers[0])
result = fn([{'id': 1, 'type': 'test'}])
assert isinstance(result, list) and len(result) == 1, f'Expected list of 1, got: {result}'
assert result[0].get('processed') is True, f'Item not marked processed: {result[0]}'
print(f'B3_WORKER_TASK_RUNS_OK: {batch_helpers[0]}')
\"" "B3_worker_task_fails"

# ── Check 8: test_imports.py passes (all import/circular-dep tests) ──────────
check "python3 -m pytest tests/test_imports.py -q --tb=short 2>&1 | tail -3 | grep -qE 'passed|no tests'" \
  "import_tests_fail"

# ── Check 9: test_versions.py passes (all version constraint tests) ───────────
check "python3 -m pytest tests/ -q --tb=short 2>&1 | tail -3 | grep -qE 'passed|no tests'" \
  "all_tests_fail"

# ── Check 10: attestation ──────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

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
