#!/usr/bin/env bash
# Seed-aware grader for PIPE4: CI/CD Pipeline Fix
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

# Prefer venv python; fall back to system python3
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for candidate in \
      "$(dirname "$0")/../../..python3" \
      "python3"; do
    if "$candidate" -c "import json" >/dev/null 2>&1; then
      PYTHON="$candidate"
      break
    fi
  done
  PYTHON="${PYTHON:-python3}"
fi

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

# ── Check 1: pipeline.json exists and is valid JSON ───────────────────────────
check "$PYTHON -c \"
import json
with open('pipeline.json', 'r') as f:
    cfg = json.load(f)
assert isinstance(cfg, dict), 'pipeline.json must be a JSON object'
assert 'stages' in cfg, 'pipeline.json must have stages key'
assert isinstance(cfg['stages'], list), 'stages must be a list'
assert len(cfg['stages']) > 0, 'stages list must not be empty'
print('PIPELINE_JSON_VALID')
\"" "pipeline_json_invalid"

# Only run deeper checks if pipeline.json loads
if "$PYTHON" -c "import json; json.load(open('pipeline.json'))" 2>/dev/null; then

# ── Check 2: All required stages present ──────────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

required = expected['required_stages']
actual_names = [s['name'] for s in cfg['stages']]

missing = [r for r in required if r not in actual_names]
assert not missing, 'Missing required stages: ' + str(missing)
print('ALL_STAGES_PRESENT')
\"" "missing_required_stages"

# ── Check 3: Stages in correct order ─────────────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

correct_order = expected['correct_stage_order']
actual_names = [s['name'] for s in cfg['stages']]

# Filter actual to only required stages and check order
actual_required = [n for n in actual_names if n in correct_order]
assert actual_required == correct_order, (
    'Stages in wrong order. Expected: ' + str(correct_order) +
    ', got: ' + str(actual_required)
)
print('STAGE_ORDER_CORRECT')
\"" "wrong_stage_order"

# ── Check 4: lint stage has correct env vars ──────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

lint_stage = next((s for s in cfg['stages'] if s['name'] == 'lint'), None)
assert lint_stage is not None, 'lint stage not found'

required_env = expected['stage_env_requirements'].get('lint', [])
actual_env = lint_stage.get('env', {})
missing = [k for k in required_env if k not in actual_env]
assert not missing, 'lint stage missing env vars: ' + str(missing)
print('LINT_ENV_OK')
\"" "lint_stage_env_wrong"

# ── Check 5: test stage has correct env vars ──────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

test_stage = next((s for s in cfg['stages'] if s['name'] == 'test'), None)
assert test_stage is not None, 'test stage not found'

required_env = expected['stage_env_requirements'].get('test', [])
actual_env = test_stage.get('env', {})
missing = [k for k in required_env if k not in actual_env]
assert not missing, 'test stage missing env vars: ' + str(missing)
print('TEST_ENV_OK')
\"" "test_stage_env_wrong"

# ── Check 6: build stage has correct env vars ─────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

build_stage = next((s for s in cfg['stages'] if s['name'] == 'build'), None)
assert build_stage is not None, 'build stage not found'

required_env = expected['stage_env_requirements'].get('build', [])
actual_env = build_stage.get('env', {})
missing = [k for k in required_env if k not in actual_env]
assert not missing, 'build stage missing env vars: ' + str(missing)
print('BUILD_ENV_OK')
\"" "build_stage_env_wrong"

# ── Check 7: deploy-staging has correct ARTIFACT_PATH ────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

deploy_stage = next((s for s in cfg['stages'] if s['name'] == 'deploy-staging'), None)
assert deploy_stage is not None, 'deploy-staging stage not found'

correct_path = expected['artifact_path']
actual_path = deploy_stage.get('env', {}).get('ARTIFACT_PATH', '')
assert actual_path == correct_path, (
    'deploy-staging ARTIFACT_PATH should be ' + repr(correct_path) +
    ', got ' + repr(actual_path)
)
print('DEPLOY_STAGING_ARTIFACT_OK')
\"" "deploy_staging_artifact_wrong"

# ── Check 8: deploy-prod has correct ARTIFACT_PATH and PROD_APPROVAL_TOKEN ───
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

prod_stage = next((s for s in cfg['stages'] if s['name'] == 'deploy-prod'), None)
assert prod_stage is not None, 'deploy-prod stage not found'

prod_env = prod_stage.get('env', {})
correct_path = expected['artifact_path']
actual_path = prod_env.get('ARTIFACT_PATH', '')
assert actual_path == correct_path, (
    'deploy-prod ARTIFACT_PATH should be ' + repr(correct_path) +
    ', got ' + repr(actual_path)
)

required_env = expected['stage_env_requirements'].get('deploy-prod', [])
missing = [k for k in required_env if k not in prod_env]
assert not missing, 'deploy-prod missing env vars: ' + str(missing)
print('DEPLOY_PROD_OK')
\"" "deploy_prod_config_wrong"

# ── Check 9: integration-test stage present and has env vars ─────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

it_stage = next((s for s in cfg['stages'] if s['name'] == 'integration-test'), None)
assert it_stage is not None, 'integration-test stage not found'

required_env = expected['stage_env_requirements'].get('integration-test', [])
actual_env = it_stage.get('env', {})
missing = [k for k in required_env if k not in actual_env]
assert not missing, 'integration-test stage missing env vars: ' + str(missing)
print('INTEGRATION_TEST_ENV_OK')
\"" "integration_test_env_wrong"

# ── Check 10: depends_on chains are correct ───────────────────────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('pipeline.json'))

correct_pipeline = expected['correct_pipeline']
correct_deps = {s['name']: s['depends_on'] for s in correct_pipeline['stages']}
actual_stages = {s['name']: s.get('depends_on', []) for s in cfg['stages']}

errors = []
for stage_name, deps in correct_deps.items():
    actual_deps = actual_stages.get(stage_name, [])
    if sorted(actual_deps) != sorted(deps):
        errors.append(
            f'{stage_name}: depends_on should be {deps}, got {actual_deps}'
        )
assert not errors, 'Dependency errors: ' + '; '.join(errors)
print('DEPENDS_ON_OK')
\"" "depends_on_wrong"

# ── Check 11: validate_pipeline.py passes ────────────────────────────────────
check "$PYTHON validate_pipeline.py pipeline.json" "validate_pipeline_failed"

# ── Check 12: pipeline_runner.py --dry-run passes ────────────────────────────
check "$PYTHON pipeline_runner.py --dry-run" "pipeline_runner_dry_run_failed"

fi  # end if pipeline.json loads

# ── Check 13: deploy.sh uses ARTIFACT_PATH and checks prod token ──────────────
check "$PYTHON -c \"
import os
script = open('scripts/deploy.sh').read()
assert 'ARTIFACT_PATH' in script, 'deploy.sh must reference ARTIFACT_PATH'
assert 'PROD_APPROVAL_TOKEN' in script, 'deploy.sh must check PROD_APPROVAL_TOKEN for prod deploys'
assert 'DEPLOY_ENV' in script, 'deploy.sh must check DEPLOY_ENV'
print('DEPLOY_SH_OK')
\"" "deploy_sh_missing_checks"

# ── Check 14: build.sh uses BUILD_OUTPUT_DIR (not hardcoded path) ─────────────
check "$PYTHON -c \"
script = open('scripts/build.sh').read()
assert 'BUILD_OUTPUT_DIR' in script, 'build.sh must use BUILD_OUTPUT_DIR env var'
assert 'output/' not in script or 'BUILD_OUTPUT_DIR' in script, 'build.sh must not hardcode output directory'
print('BUILD_SH_OK')
\"" "build_sh_hardcoded_path"

# ── Check 15: Attestation ─────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Write score ───────────────────────────────────────────────────────────────
PARTIAL=$("$PYTHON" -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$("$PYTHON" -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON

# hermetic-by: scripts/make_graders_hermetic.py
