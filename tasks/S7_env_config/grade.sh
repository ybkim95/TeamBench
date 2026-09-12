#!/usr/bin/env bash
# Grader for S7: Environment Variable Configuration Fix
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
source /usr/local/lib/venv/bin/activate 2>/dev/null || true

# 1. config.py exists
check "test -f config.py" "missing_config"

# 2. app.py exists
check "test -f app.py" "missing_app"

# 3. App runs without env vars (uses defaults, no crash)
check "python3 -c \"
import subprocess, sys
result = subprocess.run([sys.executable, 'app.py'], capture_output=True, text=True, timeout=10, env={'PATH': '/usr/bin:/bin', 'HOME': '/tmp'})
assert result.returncode == 0, f'app.py crashed: {result.stderr}'
\"" "app_crashes_no_env"

# 4. Bug 1: default value for DB_HOST
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('config.py') as f:
    content = f.read()
# Must not have bare os.environ[DB_HOST] — must use .get() with default
assert 'os.environ[' not in content or expected['db_host_var'] not in content.split('os.environ[')[1].split(']')[0] if 'os.environ[' in content else True
assert '.get(' in content, 'No .get() call found'
assert expected['db_host_default'] in content, f'Default value {expected[\"db_host_default\"]} not found'
\"" "bug1_no_default"

# 5. Bug 2: type cast for MAX_RETRIES
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
var_name = expected['retries_var']
with open('config.py') as f:
    content = f.read()
# The variable should be cast to int
assert f'int(' in content, 'No int() cast found'
# Verify it works: set env var and check type
import subprocess, sys, os
env = os.environ.copy()
env[var_name] = '5'
env[expected['db_host_var']] = 'testhost'
env[expected['api_key_var']] = 'testkey'
result = subprocess.run([sys.executable, '-c', f'''
import importlib.util
spec = importlib.util.spec_from_file_location(\"config\", \"config.py\")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
val = getattr(mod, \"{expected['retries_attr']}\")
assert isinstance(val, int), f\"Expected int, got {{type(val)}}\"
'''], capture_output=True, text=True, timeout=10, env=env, cwd='$WORKSPACE')
assert result.returncode == 0, f'Type cast check failed: {result.stderr}'
\"" "bug2_no_typecast"

# 6. Bug 3: correct case for API_KEY
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('config.py') as f:
    content = f.read()
assert expected['api_key_var'] in content, f'{expected[\"api_key_var\"]} not found (wrong case?)'
\"" "bug3_wrong_case"

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
