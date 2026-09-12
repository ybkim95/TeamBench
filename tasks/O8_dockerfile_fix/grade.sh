#!/usr/bin/env bash
# Grader for O8: Dockerfile Fix
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

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

# 1. Dockerfile exists
check "test -f Dockerfile" "missing_dockerfile"

if [ -f Dockerfile ] && [ -f "$EXPECTED" ]; then

# 2. Correct base image tag
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('Dockerfile') as f:
    content = f.read()
assert expected['base_image'] in content, f'Base image {expected[\"base_image\"]} not found'
\"" "wrong_base_image"

# 3. WORKDIR present
check "grep -q 'WORKDIR /app' Dockerfile" "missing_workdir"

# 4. Correct layer ordering: requirements.txt copied before pip install, app code after
check "python3 -c \"
with open('Dockerfile') as f:
    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
copy_req_idx = None
pip_idx = None
copy_all_idx = None
for i, l in enumerate(lines):
    if 'requirements.txt' in l and l.startswith('COPY'):
        copy_req_idx = i
    if 'pip install' in l and 'requirements' in l:
        pip_idx = i
    if l.startswith('COPY') and '. .' in l and 'requirements' not in l:
        copy_all_idx = i
assert copy_req_idx is not None, 'No COPY requirements.txt found'
assert pip_idx is not None, 'No pip install found'
assert copy_all_idx is not None, 'No COPY . . found'
assert copy_req_idx < pip_idx < copy_all_idx, f'Wrong order: COPY req={copy_req_idx}, pip={pip_idx}, COPY .={copy_all_idx}'
\"" "wrong_layer_order"

# 5. Correct EXPOSE port
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('Dockerfile') as f:
    content = f.read()
assert f'EXPOSE {expected[\"correct_port\"]}' in content, 'Wrong EXPOSE port'
\"" "wrong_port"

# 6. CMD in exec form
check "python3 -c \"
with open('Dockerfile') as f:
    lines = f.readlines()
cmd_lines = [l.strip() for l in lines if l.strip().startswith('CMD')]
assert len(cmd_lines) >= 1, 'No CMD found'
cmd = cmd_lines[-1]
assert cmd.startswith('CMD ['), f'CMD not in exec form: {cmd}'
assert 'python' in cmd and 'app.py' in cmd, f'CMD does not run python app.py: {cmd}'
\"" "cmd_not_exec_form"

fi

# Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    PASS=true
else
    PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $([ "$PASS" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
