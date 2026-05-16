#!/usr/bin/env bash
# GH14_celery_chain_fail grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=6
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

pip install pytest --quiet 2>/dev/null || true

# C1: pipeline.py valid Python
result=$(python3 -c "import ast; ast.parse(open('pipeline.py').read()); print('pass')" 2>/dev/null || echo "fail")
check "C1" "pipeline.py valid Python syntax" "$result"

# C2: tasks.py valid Python
result=$(python3 -c "import ast; ast.parse(open('tasks.py').read()); print('pass')" 2>/dev/null || echo "fail")
check "C2" "tasks.py valid Python syntax" "$result"

# C3: error item raises exception (core fix)
result=$(python3 -c "
import sys; sys.path.insert(0, '.')
from tasks import StageError
import pipeline as pm
import inspect

# detect pipeline class and error item
src = inspect.getsource(pm)
# find error sentinel from domain config
error_items = ['POISON_PILL', 'CORRUPT_IMAGE', 'INVALID_DATA']
error_item = None
for e in error_items:
    if e in src:
        error_item = e; break
if error_item is None:
    print('fail'); exit(0)

# find pipeline class
pipeline_class = None
for name, obj in inspect.getmembers(pm):
    if inspect.isclass(obj) and hasattr(obj, 'run'):
        pipeline_class = obj; break
if pipeline_class is None:
    print('fail'); exit(0)

p = pipeline_class()
try:
    result = p.run([error_item])
    # If no exception raised, check all results are error dicts (partial credit fail)
    print('fail')
except Exception:
    print('pass')
" 2>/dev/null || echo "fail")
check "C3" "stage-1 failure raises exception (not swallowed)" "$result"

# C4: single bad item raises
result=$(python3 -c "
import sys; sys.path.insert(0, '.')
from tasks import StageError
import pipeline as pm, inspect
src = inspect.getsource(pm)
error_items = ['POISON_PILL', 'CORRUPT_IMAGE', 'INVALID_DATA']
error_item = next((e for e in error_items if e in src), 'POISON_PILL')
pipeline_class = next(
    (obj for name, obj in inspect.getmembers(pm) if inspect.isclass(obj) and hasattr(obj, 'run')),
    None
)
if pipeline_class is None:
    print('fail'); exit(0)
p = pipeline_class()
try:
    p.run([error_item])
    print('fail')
except Exception:
    print('pass')
" 2>/dev/null || echo "fail")
check "C4" "single bad item raises exception" "$result"

# C5: success path returns all-ok results
result=$(python3 -c "
import sys; sys.path.insert(0, '.')
import pipeline as pm, inspect
pipeline_class = next(
    (obj for name, obj in inspect.getmembers(pm) if inspect.isclass(obj) and hasattr(obj, 'run')),
    None
)
if pipeline_class is None:
    print('fail'); exit(0)
p = pipeline_class()
items = ['item_0', 'item_1', 'item_2', 'item_3']
try:
    results = p.run(items)
    if len(results) != 4:
        print('fail'); exit(0)
    for r in results:
        if r.get('status') != 'ok':
            print('fail'); exit(0)
    print('pass')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C5" "success path returns all-ok results" "$result"

# C6: pytest test_pipeline.py passes
result=$(python3 -m pytest test_pipeline.py -q --tb=no 2>/dev/null && echo "pass" || echo "fail")
check "C6" "pytest test_pipeline.py passes" "$result"

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
