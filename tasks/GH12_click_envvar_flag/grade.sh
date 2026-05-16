#!/usr/bin/env bash
# GH12_click_envvar_flag grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=8
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

# C1: cli.py is valid Python
result=$(python3 -c "import ast; ast.parse(open('cli.py').read()); print('pass')" 2>/dev/null || echo "fail")
check "C1" "cli.py valid Python syntax" "$result"

# Helper: detect which envvar and command this seed uses
ENVVAR=$(python3 -c "
import sys; sys.path.insert(0,'.')
import inspect, cli as m
src = inspect.getsource(m)
for e in ['DEPLOY_DRY_RUN','BACKUP_DRY_RUN','MIGRATE_DRY_RUN']:
    if e in src:
        print(e); break
" 2>/dev/null || echo "DEPLOY_DRY_RUN")

CMD=$(python3 -c "
import sys; sys.path.insert(0,'.')
import inspect, cli as m
src = inspect.getsource(m)
for fn in ['deploy','backup','migrate']:
    if 'def '+fn+'(' in src:
        print(fn); break
" 2>/dev/null || echo "deploy")

# C2: envvar=false -> dry_run=False
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='false'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=None)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is False else 'fail')
" 2>/dev/null || echo "fail")
check "C2" "envvar=false produces dry_run=False" "$result"

# C3: envvar=0 -> dry_run=False
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='0'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=None)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is False else 'fail')
" 2>/dev/null || echo "fail")
check "C3" "envvar=0 produces dry_run=False" "$result"

# C4: envvar=no -> dry_run=False
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='no'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=None)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is False else 'fail')
" 2>/dev/null || echo "fail")
check "C4" "envvar=no produces dry_run=False" "$result"

# C5: envvar=true -> dry_run=True
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='true'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=None)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is True else 'fail')
" 2>/dev/null || echo "fail")
check "C5" "envvar=true produces dry_run=True" "$result"

# C6: envvar=1 -> dry_run=True
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='1'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=None)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is True else 'fail')
" 2>/dev/null || echo "fail")
check "C6" "envvar=1 produces dry_run=True" "$result"

# C7: explicit True overrides envvar=false
result=$(python3 -c "
import os,importlib,sys; sys.path.insert(0,'.')
e='${ENVVAR}'; os.environ[e]='false'
import cli as m; importlib.reload(m)
fn=getattr(m,'${CMD}')
r=fn(dry_run_flag=True)
os.environ.pop(e,None)
print('pass' if r['dry_run'] is True else 'fail')
" 2>/dev/null || echo "fail")
check "C7" "explicit True overrides envvar=false" "$result"

# C8: pytest test_cli.py passes
result=$(python3 -m pytest test_cli.py -q --tb=no 2>/dev/null && echo "pass" || echo "fail")
check "C8" "pytest test_cli.py passes" "$result"

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
