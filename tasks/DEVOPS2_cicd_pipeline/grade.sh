#!/usr/bin/env bash
# DEVOPS2_cicd_pipeline grader — static YAML analysis of the fixed workflow
# Checks that all real bugs are fixed and flaky-test patterns are preserved.
# No GitHub Actions runner required; all checks parse file content.
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

BUGS=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(' '.join(e.get('bugs', [])))
" 2>/dev/null || echo "")

WRONG_RUNNER=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('wrong_runner', 'ubuntu-18.04'))
" 2>/dev/null || echo "ubuntu-18.04")

CORRECT_ARTIFACT=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('correct_artifact_dir', 'dist/'))
" 2>/dev/null || echo "dist/")

WRONG_ARTIFACT=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('wrong_artifact_dir', 'build/'))
" 2>/dev/null || echo "build/")

WORKFLOW="${WORKSPACE}/.github/workflows/ci.yml"

# ── C1: Workflow file exists ───────────────────────────────────────────────────
check "C1" ".github/workflows/ci.yml exists" "$([ -f "${WORKFLOW}" ] && echo pass || echo fail)"

# ── C2: B1 — runner image fixed (no longer EOL) ───────────────────────────────
result=$(python3 -c "
bugs = '${BUGS}'.split()
if 'wrong_runner_image' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${WORKFLOW}').read()
    wrong = '${WRONG_RUNNER}'
    if wrong in content:
        print('fail')
    elif 'ubuntu-latest' in content:
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C2" "B1 fixed: runner changed from ${WRONG_RUNNER} to ubuntu-latest" "${result}"

# ── C3: B2 — env block present for secret step ────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'missing_env_var' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${WORKFLOW}').read()
    if re.search(r'env:\s*\n\s+\w+:', content) and 'secrets.' in content:
        print('pass')
    else:
        print('fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C3" "B2 fixed: env block with secret injection present" "${result}"

# ── C4: B3 — artifact path fixed ──────────────────────────────────────────────
result=$(python3 -c "
bugs = '${BUGS}'.split()
if 'wrong_artifact_path' not in bugs:
    print('pass')
    raise SystemExit
try:
    lines = open('${WORKFLOW}').readlines()
    path_lines = [l for l in lines if 'path:' in l]
    correct = '${CORRECT_ARTIFACT}'
    wrong = '${WRONG_ARTIFACT}'
    has_correct = any(correct in l for l in path_lines)
    has_wrong = any(wrong in l for l in path_lines)
    print('pass' if has_correct and not has_wrong else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C4" "B3 fixed: upload-artifact path is ${CORRECT_ARTIFACT}" "${result}"

# ── C5: B4 — deploy conditional fixed ────────────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'bad_conditional' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${WORKFLOW}').read()
    has_always = bool(re.search(r'if:\s*always\(\)', content))
    has_success = bool(re.search(r'if:.*success\(\)', content))
    print('pass' if not has_always and has_success else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C5" "B4 fixed: deploy conditional uses success() not always()" "${result}"

# ── C6: B5 — fetch-depth fixed ───────────────────────────────────────────────
result=$(python3 -c "
import re
bugs = '${BUGS}'.split()
if 'wrong_checkout_depth' not in bugs:
    print('pass')
    raise SystemExit
try:
    content = open('${WORKFLOW}').read()
    has_depth_1 = bool(re.search(r'fetch-depth:\s*1\b', content))
    has_depth_0 = bool(re.search(r'fetch-depth:\s*0\b', content))
    print('pass' if not has_depth_1 and has_depth_0 else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C6" "B5 fixed: fetch-depth changed from 1 to 0" "${result}"

# ── C7: F1 preserved — continue-on-error on integration tests ─────────────────
result=$(python3 -c "
import re
try:
    content = open('${WORKFLOW}').read()
    print('pass' if re.search(r'continue-on-error:\s*true', content) else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C7" "F1 preserved: continue-on-error: true on integration test step" "${result}"

# ── C8: F2 preserved — timeout-minutes on slow test ──────────────────────────
result=$(python3 -c "
import re
try:
    content = open('${WORKFLOW}').read()
    print('pass' if re.search(r'timeout-minutes:\s*\d+', content) else 'fail')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C8" "F2 preserved: timeout-minutes present on slow test step" "${result}"

# ── C9: YAML is syntactically valid ───────────────────────────────────────────
result=$(python3 -c "
try:
    import yaml
    with open('${WORKFLOW}') as f:
        yaml.safe_load(f)
    print('pass')
except ImportError:
    print('pass')
except Exception:
    print('fail')
" 2>/dev/null || echo "pass")
check "C9" "YAML syntax is valid" "${result}"

# ── C10: postmortem.md present ────────────────────────────────────────────────
check "C10" "postmortem.md present in workspace" "$([ -f '${WORKSPACE}/postmortem.md' ] && echo pass || echo fail)"

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
