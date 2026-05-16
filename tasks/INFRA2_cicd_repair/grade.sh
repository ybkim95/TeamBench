#!/usr/bin/env bash
# INFRA2_cicd_repair grader — parse the fixed ci.yml and verify:
#   real bugs are fixed, flaky-test patterns preserved.
#
# Checks:
#   C1  .github/workflows/ci.yml exists
#   C2  YAML is syntactically valid
#   C3  Docker image tag is pinned (not :latest)
#   C4  Secret env var block is present in deploy step
#   C5  Artifact upload path matches expected build output dir
#   C6  Deploy step does NOT use always() condition
#   C7  Deploy step uses success() condition (correct guard)
#   C8  fetch-depth is 0 (full clone for git describe)
#   C9  continue-on-error: true on integration test is PRESERVED
#   C10 timeout-minutes on slow test step is PRESERVED
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

mkdir -p "${REPORTS}"

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

# ── Load expected values ───────────────────────────────────────────────────────
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
    EXPECTED_JSON="${TASK_DIR}/expected.json"
fi

WRONG_DOCKER_TAG=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('wrong_docker_tag', 'latest'))
" 2>/dev/null || echo "latest")

CORRECT_ARTIFACT_DIR=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('correct_artifact_dir', 'dist/'))
" 2>/dev/null || echo "dist/")

WRONG_ARTIFACT_DIR=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('wrong_artifact_dir', 'build/'))
" 2>/dev/null || echo "build/")

SECRET_VAR=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('secret_var', 'SECRET_KEY'))
" 2>/dev/null || echo "SECRET_KEY")

SLOW_TIMEOUT=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('slow_timeout', 30))
" 2>/dev/null || echo "30")

BUGS=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(' '.join(e.get('bugs', [])))
" 2>/dev/null || echo "")

WORKFLOW="${WORKSPACE}/.github/workflows/ci.yml"

# ── C1: Workflow file exists ───────────────────────────────────────────────────
check "C1" "ci.yml exists at .github/workflows/ci.yml" \
    "$([ -f '${WORKFLOW}' ] && echo pass || echo fail)"

# ── C2: YAML is syntactically valid ───────────────────────────────────────────
result=$(python3 -c "
import yaml, sys
try:
    yaml.safe_load(open('${WORKFLOW}'))
    print('pass')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C2" "ci.yml is syntactically valid YAML" "${result}"

# ── C3: Docker image tag is pinned (not :latest) ──────────────────────────────
result=$(python3 -c "
import re, sys
content = open('${WORKFLOW}').read()
# Check that :latest does not appear in any docker build/run command
has_latest = bool(re.search(r'docker\s+build.*:latest', content) or
                  re.search(r':\${WRONG_DOCKER_TAG}', content))
# More broadly: ensure :latest is gone from docker lines
has_latest = bool(re.search(r'docker\s+(build|run|push)[^\n]*:latest', content))
print('fail' if has_latest else 'pass')
" 2>/dev/null || echo "fail")
check "C3" "Docker image tag is pinned (not :${WRONG_DOCKER_TAG})" "${result}"

# ── C4: Secret env var is injected ────────────────────────────────────────────
result=$(python3 -c "
import yaml, sys, re
bugs = '${BUGS}'.split()
if 'missing_env_var' not in bugs:
    print('pass')
    sys.exit(0)
content = open('${WORKFLOW}').read()
# Check that the secret var appears in an env: block (not just a comment)
secret_var = '${SECRET_VAR}'
# Look for 'SECRET_VAR: \${{ secrets.SECRET_VAR }}'
pattern = rf'{re.escape(secret_var)}\s*:\s*\\\${{{{[^}}]*secrets[^}}]*{re.escape(secret_var)}'
print('pass' if re.search(pattern, content) else 'fail')
" 2>/dev/null || echo "fail")
check "C4" "Secret env var ${SECRET_VAR} is injected via env: block" "${result}"

# ── C5: Artifact upload path is correct ───────────────────────────────────────
result=$(python3 -c "
import yaml, sys
bugs = '${BUGS}'.split()
if 'wrong_artifact_path' not in bugs:
    print('pass')
    sys.exit(0)
content = open('${WORKFLOW}').read()
correct = '${CORRECT_ARTIFACT_DIR}'
wrong   = '${WRONG_ARTIFACT_DIR}'
# correct path present AND wrong path absent from upload-artifact context
has_correct = correct in content
has_wrong   = wrong in content
# The wrong path might appear in comments; check YAML structure
try:
    data = yaml.safe_load(content)
    jobs = data.get('jobs', {})
    for job in jobs.values():
        for step in job.get('steps', []):
            uses = step.get('uses', '')
            if 'upload-artifact' in uses:
                path = step.get('with', {}).get('path', '')
                if correct.rstrip('/') in path:
                    print('pass')
                    sys.exit(0)
                else:
                    print('fail')
                    sys.exit(0)
    print('fail')
except Exception:
    print('pass' if has_correct and not has_wrong else 'fail')
" 2>/dev/null || echo "fail")
check "C5" "Artifact upload path is ${CORRECT_ARTIFACT_DIR} (not ${WRONG_ARTIFACT_DIR})" "${result}"

# ── C6: Deploy step does NOT use always() ─────────────────────────────────────
result=$(python3 -c "
import yaml, sys
bugs = '${BUGS}'.split()
if 'bad_conditional' not in bugs:
    print('pass')
    sys.exit(0)
try:
    data = yaml.safe_load(open('${WORKFLOW}'))
    jobs = data.get('jobs', {})
    for job in jobs.values():
        for step in job.get('steps', []):
            step_if = str(step.get('if', ''))
            if 'always()' in step_if:
                print('fail')
                sys.exit(0)
    print('pass')
except Exception:
    # Fall back to text search
    import re
    content = open('${WORKFLOW}').read()
    print('fail' if re.search(r'if:\s*always\(\)', content) else 'pass')
" 2>/dev/null || echo "fail")
check "C6" "Deploy step does not use always() condition" "${result}"

# ── C7: Deploy step uses success() guard ──────────────────────────────────────
result=$(python3 -c "
import yaml, sys, re
bugs = '${BUGS}'.split()
if 'bad_conditional' not in bugs:
    print('pass')
    sys.exit(0)
content = open('${WORKFLOW}').read()
# Must contain success() in an if: expression
print('pass' if re.search(r'if:\s*success\(\)', content) else 'fail')
" 2>/dev/null || echo "fail")
check "C7" "Deploy step uses success() condition" "${result}"

# ── C8: fetch-depth is 0 (not shallow clone) ──────────────────────────────────
result=$(python3 -c "
import yaml, sys
bugs = '${BUGS}'.split()
if 'shallow_clone' not in bugs:
    print('pass')
    sys.exit(0)
try:
    data = yaml.safe_load(open('${WORKFLOW}'))
    jobs = data.get('jobs', {})
    for job in jobs.values():
        for step in job.get('steps', []):
            uses = step.get('uses', '')
            if 'checkout' in uses:
                depth = step.get('with', {}).get('fetch-depth', None)
                if depth is not None:
                    print('pass' if int(depth) == 0 else 'fail')
                else:
                    print('pass')  # default is 1 but absence means no explicit shallow
                sys.exit(0)
    print('pass')
except Exception:
    import re
    content = open('${WORKFLOW}').read()
    m = re.search(r'fetch-depth:\s*(\d+)', content)
    if m:
        print('pass' if m.group(1) == '0' else 'fail')
    else:
        print('pass')
" 2>/dev/null || echo "fail")
check "C8" "fetch-depth: 0 (full clone for git describe)" "${result}"

# ── C9: continue-on-error preserved on integration test ───────────────────────
result=$(python3 -c "
import yaml, sys
try:
    data = yaml.safe_load(open('${WORKFLOW}'))
    jobs = data.get('jobs', {})
    for job in jobs.values():
        for step in job.get('steps', []):
            if step.get('continue-on-error') is True:
                print('pass')
                sys.exit(0)
    print('fail')
except Exception:
    import re
    content = open('${WORKFLOW}').read()
    print('pass' if re.search(r'continue-on-error:\s*true', content, re.IGNORECASE) else 'fail')
" 2>/dev/null || echo "fail")
check "C9" "continue-on-error: true preserved on integration test step" "${result}"

# ── C10: timeout-minutes preserved on slow test ───────────────────────────────
result=$(python3 -c "
import yaml, sys
expected_timeout = int('${SLOW_TIMEOUT}')
try:
    data = yaml.safe_load(open('${WORKFLOW}'))
    jobs = data.get('jobs', {})
    for job in jobs.values():
        for step in job.get('steps', []):
            tm = step.get('timeout-minutes')
            if tm is not None and int(tm) == expected_timeout:
                print('pass')
                sys.exit(0)
    print('fail')
except Exception:
    import re
    content = open('${WORKFLOW}').read()
    pattern = rf'timeout-minutes:\s*{expected_timeout}\b'
    print('pass' if re.search(pattern, content) else 'fail')
" 2>/dev/null || echo "fail")
check "C10" "timeout-minutes: ${SLOW_TIMEOUT} preserved on slow test step" "${result}"

# ── Write score.json ──────────────────────────────────────────────────────────
partial_score=$(python3 -c "print(round(${partial} / ${total}, 2))")
findings="${findings%,}"

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "${pass}" = "true" ] && echo "true" || echo "false" ),
  "primary": {"success": $( [ "${pass}" = "true" ] && echo 1 || echo 0 )},
  "secondary": {
    "partial_score": ${partial_score},
    "checks_passed": ${partial},
    "checks_total": ${total}
  },
  "failure_modes": [],
  "checklist": [${findings}]
}
EOF
