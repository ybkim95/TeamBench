#!/usr/bin/env bash
# Generic grader for generator-based tasks.
# Delegates to workspace/check_solution.py which writes reports/score.json.
#
# Called as: grade.sh WORKSPACE REPORTS SUBMISSION TASK_DIR [EXPECTED_JSON]
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

if [ ! -f "${WORKSPACE}/check_solution.py" ]; then
    mkdir -p "${REPORTS}"
    cat > "${REPORTS}/score.json" <<EOF
{
  "pass": false,
  "primary": {"success": 0},
  "secondary": {"partial_score": 0.0, "checks_passed": 0, "checks_total": 0},
  "failure_modes": ["check_solution_missing"]
}
EOF
    exit 0
fi

# ── Resolve a GRADER-ONLY copy of the rubric script ──────────────────────
# repaired-by: scripts/repair_graders.py (R4 grader-only-rubric)
# check_solution.py is written into the agent-writable workspace by the task
# generator and contains the full rubric. Executing the workspace copy let an
# agent overwrite it and grade itself (measured: 4/4 probed tasks flipped to
# pass=true / partial 1.00 by dropping in a stub). We never execute the
# workspace copy. Resolution order:
#   1. "$REPORTS/check_solution.py"            (grader-only staging dir)
#   2. "$TASK_DIR/reference/check_solution.py" (static grader-only copy)
#   3. deterministic regeneration from the task generator at this run's seed
TASK_DIR="${4:-$(cd "$(dirname "$0")" && pwd)}"
TB_GDIR="$(mktemp -d)"
trap 'rm -rf "$TB_GDIR"' EXIT
TB_RUBRIC=""

if [ -f "${REPORTS}/check_solution.py" ]; then
    TB_RUBRIC="${REPORTS}/check_solution.py"
elif [ -f "${TASK_DIR}/reference/check_solution.py" ]; then
    TB_RUBRIC="${TASK_DIR}/reference/check_solution.py"
else
    TB_REPO_ROOT="$(cd "${TASK_DIR}/../.." && pwd)"
    TB_TASK_ID="$(basename "${TASK_DIR}")"
    TB_SEED="$(python3 - "$(dirname "${REPORTS}")/run_meta.json" <<'_TBPY' 2>/dev/null || echo 0
import json, sys
try:
    print(int(json.load(open(sys.argv[1])).get("seed", 0)))
except Exception:
    print(0)
_TBPY
)"
    if TB_REPO_ROOT="$TB_REPO_ROOT" TB_TASK_ID="$TB_TASK_ID" TB_SEED="$TB_SEED" \
       TB_OUT="${TB_GDIR}/check_solution.py" python3 - <<'_TBPY' 2>/dev/null; then
import os, sys
sys.path.insert(0, os.environ["TB_REPO_ROOT"])
from generators.registry import get_generator
gen = get_generator(os.environ["TB_TASK_ID"])
res = gen.generate(seed=int(os.environ["TB_SEED"]))
src = res.workspace_files.get("check_solution.py")
if not src:
    sys.exit(1)
open(os.environ["TB_OUT"], "w", encoding="utf-8").write(src)
_TBPY
        TB_RUBRIC="${TB_GDIR}/check_solution.py"
    fi
fi

if [ -z "$TB_RUBRIC" ] || [ ! -s "$TB_RUBRIC" ]; then
    mkdir -p "${REPORTS}"
    cat > "${REPORTS}/score.json" <<EOF
{
  "pass": false,
  "primary": {"success": 0},
  "secondary": {"partial_score": 0.0, "checks_passed": 0, "checks_total": 0},
  "failure_modes": ["grader_rubric_unavailable"]
}
EOF
    exit 0
fi

# Execute the trusted rubric with __file__ pinned to the workspace so the
# script's own path resolution (workspace_dir = __file__.parent,
# reports_dir = workspace_dir.parent/"reports") is unchanged. The workspace
# copy, whatever the agent left there, is never executed.
TB_RUBRIC="$TB_RUBRIC" TB_WORKSPACE="${WORKSPACE}" python3 - <<'_TBPY' || true
import os, runpy, sys
src = open(os.environ["TB_RUBRIC"], encoding="utf-8").read()
fake = os.path.join(os.environ["TB_WORKSPACE"], "check_solution.py")
g = {"__name__": "__main__", "__file__": fake, "__builtins__": __builtins__}
os.chdir(os.environ["TB_WORKSPACE"])
try:
    exec(compile(src, fake, "exec"), g)
except SystemExit:
    pass
_TBPY
