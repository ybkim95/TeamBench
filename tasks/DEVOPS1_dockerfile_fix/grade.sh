#!/usr/bin/env bash
# DEVOPS1_dockerfile_fix grader — static analysis of the fixed Dockerfile
# No Docker daemon required; all checks parse file content.
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

# ── Load expected values from seed-specific expected.json ─────────────────────
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
    EXPECTED_JSON="${TASK_DIR}/expected.json"
fi

CORRECT_IMAGE=$(python3 -c "
import json, sys
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('correct_base_image', 'python:3.11-slim'))
" 2>/dev/null || echo "python:3.11-slim")

BUILDER_STAGE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('builder_stage', 'builder'))
" 2>/dev/null || echo "builder")

RUNTIME_STAGE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('runtime_stage', 'runtime'))
" 2>/dev/null || echo "runtime")

PORT=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('port', 8080))
" 2>/dev/null || echo "8080")

WORKDIR=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('workdir', '/app'))
" 2>/dev/null || echo "/app")

DOCKERFILE="${WORKSPACE}/Dockerfile"

# ── C1: Dockerfile exists ─────────────────────────────────────────────────────
check "C1" "Dockerfile exists" "$([ -f "${DOCKERFILE}" ] && echo pass || echo fail)"

# ── C2: Builder stage uses correct base image ─────────────────────────────────
result=$(python3 -c "
import re, sys
content = open('${DOCKERFILE}').read()
# Match: FROM <image> AS <builder_stage>  (case-insensitive AS)
pattern = r'(?i)FROM\s+(\S+)\s+AS\s+${BUILDER_STAGE}\b'
m = re.search(pattern, content)
if m and m.group(1) == '${CORRECT_IMAGE}':
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C2" "builder stage (${BUILDER_STAGE}) uses ${CORRECT_IMAGE}" "${result}"

# ── C3: Runtime stage uses correct base image ─────────────────────────────────
result=$(python3 -c "
import re
content = open('${DOCKERFILE}').read()
pattern = r'(?i)FROM\s+(\S+)\s+AS\s+${RUNTIME_STAGE}\b'
m = re.search(pattern, content)
if m and m.group(1) == '${CORRECT_IMAGE}':
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C3" "runtime stage (${RUNTIME_STAGE}) uses ${CORRECT_IMAGE}" "${result}"

# ── C4: pip install appears in builder stage (not only runtime) ───────────────
result=$(python3 -c "
import re
content = open('${DOCKERFILE}').read()

# Split into stage blocks by FROM lines
stages = re.split(r'(?i)(?=FROM\s)', content)
builder_block = ''
for block in stages:
    if re.search(r'(?i)FROM\s+\S+\s+AS\s+${BUILDER_STAGE}\b', block):
        builder_block = block
        break

if re.search(r'(?i)RUN\s+pip\s+install', builder_block):
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C4" "pip install in builder stage (${BUILDER_STAGE})" "${result}"

# ── C5: COPY --from references correct builder stage name ─────────────────────
result=$(python3 -c "
import re
content = open('${DOCKERFILE}').read()
# Look for COPY --from=<builder_stage> (case-insensitive flag, exact stage name)
pattern = r'(?i)COPY\s+--from=${BUILDER_STAGE}\b'
if re.search(pattern, content):
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C5" "COPY --from references correct stage (${BUILDER_STAGE})" "${result}"

# ── C6: EXPOSE uses correct port ──────────────────────────────────────────────
result=$(python3 -c "
import re
content = open('${DOCKERFILE}').read()
# EXPOSE must include the correct port
if re.search(r'(?i)EXPOSE\s+${PORT}\b', content):
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C6" "EXPOSE ${PORT} present" "${result}"

# ── C7: WORKDIR consistent between builder and runtime stages ─────────────────
result=$(python3 -c "
import re
content = open('${DOCKERFILE}').read()
stages = re.split(r'(?i)(?=FROM\s)', content)
workdirs = {}
for block in stages:
    stage_m = re.search(r'(?i)FROM\s+\S+\s+AS\s+(\S+)', block)
    if not stage_m:
        continue
    stage = stage_m.group(1)
    wd_m = re.search(r'(?i)WORKDIR\s+(\S+)', block)
    if wd_m:
        workdirs[stage] = wd_m.group(1)

builder_wd = workdirs.get('${BUILDER_STAGE}', '')
runtime_wd = workdirs.get('${RUNTIME_STAGE}', '')
if builder_wd and runtime_wd and builder_wd == runtime_wd:
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C7" "WORKDIR consistent across stages (${WORKDIR})" "${result}"

# ── C8: app.py present in workspace ───────────────────────────────────────────
check "C8" "app.py present" "$([ -f "${WORKSPACE}/app.py" ] && echo pass || echo fail)"

# ── C9: requirements.txt present in workspace ─────────────────────────────────
check "C9" "requirements.txt present" "$([ -f "${WORKSPACE}/requirements.txt" ] && echo pass || echo fail)"

# ── C10: docker-compose.yml maps correct host port ───────────────────────────
result=$(python3 -c "
import re, os
dc = '${WORKSPACE}/docker-compose.yml'
if not os.path.exists(dc):
    print('fail')
    raise SystemExit
content = open(dc).read()
# Accept both '\"PORT:PORT\"' and 'PORT:PORT' yaml styles
if re.search(r'[\"\']*${PORT}:${PORT}[\"\']*', content):
    print('pass')
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C10" "docker-compose.yml maps port ${PORT}:${PORT}" "${result}"

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
