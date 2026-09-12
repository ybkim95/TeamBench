#!/usr/bin/env bash
# MULTI2 grader: verify 4 bugs fixed across Python API, Go worker, Node.js proxy, shared config
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

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

cd "${WORKSPACE}"

# Install Python deps
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require flask pytest || true

# ── C1: config.json retry_timeout is an integer, not a string ────────────
if python3 -c "
import json, sys
cfg = json.load(open('config.json'))
val = cfg.get('retry_timeout')
if isinstance(val, int) and val > 0:
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
    check "C1" "config.json retry_timeout is integer (not string)" "pass"
else
    check "C1" "config.json retry_timeout is still a string or missing" "fail"
fi

# ── C2: config.json is valid JSON and retains other fields ───────────────
if python3 -c "
import json, sys
cfg = json.load(open('config.json'))
required = ['service_name', 'port', 'retry_timeout', 'log_level']
for k in required:
    if k not in cfg:
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C2" "config.json is valid and retains all required fields" "pass"
else
    check "C2" "config.json missing required fields or invalid JSON" "fail"
fi

# ── C3: Python API parses dates in the correct format ────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, os, json
sys.path.insert(0, os.path.join(os.getcwd(), "api"))
os.chdir(os.path.join(os.getcwd(), "api") if os.path.isdir("api") else ".")
try:
    from app import app
    client = app.test_client()
    app.config["TESTING"] = True

    # Read expected format from expected.json if available, else test ISO format
    r = client.post("/parse-date", json={"date": "2024-03-15"})
    if r.status_code == 200:
        data = r.get_json()
        if "parsed" in data or "date" in data:
            sys.exit(0)
    # Also try ISO format
    r = client.post("/parse-date", json={"date": "2024-03-15T10:30:00Z"})
    if r.status_code == 200:
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PYEOF
then
    check "C3" "Python API parses dates in correct format" "pass"
else
    check "C3" "Python API still uses wrong date format" "fail"
fi

# ── C4: Python API rejects invalid dates with 400 ───────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "api"))
os.chdir(os.path.join(os.getcwd(), "api") if os.path.isdir("api") else ".")
try:
    from app import app
    client = app.test_client()
    app.config["TESTING"] = True
    r = client.post("/parse-date", json={"date": "not-a-date"})
    if r.status_code == 400:
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PYEOF
then
    check "C4" "Python API rejects invalid dates with 400" "pass"
else
    check "C4" "Python API does not reject invalid dates correctly" "fail"
fi

# ── C5: Go worker source compiles ───────────────────────────────────────
if (cd worker && go build -o /tmp/multi2_worker . 2>/dev/null); then
    check "C5" "Go worker compiles successfully" "pass"
else
    check "C5" "Go worker failed to compile" "fail"
fi

# ── C6: Go worker processes all records (no off-by-one) ─────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, os, re
# Check Go source for correct loop bounds
src = open("worker/main.go").read()
# The off-by-one fix: loop should use <= end or < end+1, not < end
# Look for the batch processing loop and verify it doesn't skip last element
# The buggy pattern is: for i := start; i < end; i++
# The fix should be: for i := start; i <= end; i++ OR i < end+1 OR i < len
# Check that the loop bound includes the last element
if "i <= end" in src or "i < end+1" in src or "i < len(" in src:
    sys.exit(0)
# Also check if they restructured to use slicing correctly
if "items[start:end+1]" in src or "items[start:]" in src:
    sys.exit(0)
# Check for range-based loop which would naturally include all elements
if "for _, item := range" in src or "for i, _ := range" in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C6" "Go worker batch loop includes last record (off-by-one fixed)" "pass"
else
    check "C6" "Go worker still has off-by-one in batch loop" "fail"
fi

# ── C7: Node.js proxy forwards Authorization header correctly ───────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("proxy/server.js").read()
# The bug: proxy hardcodes wrong prefix or doesn't forward original header
# Fix: should read req.headers['authorization'] or req.headers.authorization
# and forward it as-is
if "req.headers['authorization']" in src or 'req.headers["authorization"]' in src or "req.headers.authorization" in src:
    # Make sure it's not hardcoding a wrong value
    if "Bearer hardcoded" not in src and "'Basic '" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "Node.js proxy forwards original Authorization header" "pass"
else
    check "C7" "Node.js proxy still hardcodes or mangles Authorization header" "fail"
fi

# ── C8: Python API app.py has valid syntax ──────────────────────────────
if python3 -c "import ast; ast.parse(open('api/app.py').read())" 2>/dev/null; then
    check "C8" "Python API app.py has valid syntax" "pass"
else
    check "C8" "Python API app.py has syntax errors" "fail"
fi

# ── C9: Go worker main.go has valid syntax (compiles) ───────────────────
if (cd worker && go vet ./... 2>/dev/null); then
    check "C9" "Go worker passes go vet" "pass"
else
    check "C9" "Go worker has issues detected by go vet" "fail"
fi

# ── C10: Node.js proxy server.js has valid syntax ──────────────────────
if node -c proxy/server.js 2>/dev/null; then
    check "C10" "Node.js proxy server.js has valid syntax" "pass"
else
    check "C10" "Node.js proxy server.js has syntax errors" "fail"
fi

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

# hermetic-by: scripts/make_graders_hermetic.py
