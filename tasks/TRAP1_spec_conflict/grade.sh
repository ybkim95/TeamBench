#!/usr/bin/env bash
# TRAP1 grader: verify that strict validation applies to 4 endpoints
# and that 3 intentionally relaxed endpoints still accept relaxed input.
set -euo pipefail

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

# ── Install dependencies ──────────────────────────────────────────────────────
pip install flask pytest --quiet 2>/dev/null || true

# ── C1: pytest passes ─────────────────────────────────────────────────────────
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# ── Inline Python test harness ────────────────────────────────────────────────
# We import the Flask app directly and test endpoints via the test client.
(python3 - <<'PYEOF'
import sys, os, json

os.chdir(sys.argv[0] if False else os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    from app import create_app
    app = create_app()
    client = app.test_client()
    app.config["TESTING"] = True

    # ── STRICT endpoint checks ───────────────────────────────────────────────

    # C2: POST /users — bad email rejected with 422
    r = client.post("/users", json={"name": "Alice", "email": "not-an-email"})
    results["C2"] = r.status_code == 422

    # C3: POST /users — valid request accepted (200 or 201)
    r = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    results["C3"] = r.status_code in (200, 201)

    # C4: POST /items — missing price rejected with 422
    r = client.post("/items", json={"name": "Widget"})
    results["C4"] = r.status_code == 422

    # C5: POST /items — negative price rejected with 422
    r = client.post("/items", json={"name": "Widget", "price": -5.0})
    results["C5"] = r.status_code == 422

    # C6: POST /orders — missing quantity rejected with 422
    r = client.post("/orders", json={"user_id": 1, "item_id": 2})
    results["C6"] = r.status_code == 422

    # C7: POST /reports — invalid report_type rejected with 422
    r = client.post("/reports", json={"report_type": "INVALID_XYZ_999"})
    results["C7"] = r.status_code == 422

    # ── RELAXED endpoint checks ──────────────────────────────────────────────

    # C8: POST /batch-import — CSV with missing optional fields accepted (not 422)
    r = client.post("/batch-import",
                    data="id,name\n1,foo\n2,bar",
                    content_type="text/csv")
    results["C8"] = r.status_code != 422

    # C9: GET /search — wildcard * in query accepted (not 422)
    r = client.get("/search?q=*")
    results["C9"] = r.status_code != 422

    # C10: POST /webhooks — arbitrary JSON accepted (not 422)
    r = client.post("/webhooks", json={"any_key": "any_value", "nested": {"x": 1}})
    results["C10"] = r.status_code != 422

except Exception as e:
    # If app fails to import or create, all checks fail
    for k in ["C2","C3","C4","C5","C6","C7","C8","C9","C10"]:
        results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/trap1_results.json 2>/tmp/trap1_err.txt || true

# Parse inline test results
if [ -f /tmp/trap1_results.json ]; then
    _res=$(cat /tmp/trap1_results.json)
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        val=$(python3 -c "import json,sys; d=json.load(open('/tmp/trap1_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C2) check "C2" "POST /users rejects invalid email (422)" "$val" ;;
            C3) check "C3" "POST /users accepts valid user (2xx)" "$val" ;;
            C4) check "C4" "POST /items rejects missing price (422)" "$val" ;;
            C5) check "C5" "POST /items rejects negative price (422)" "$val" ;;
            C6) check "C6" "POST /orders rejects missing quantity (422)" "$val" ;;
            C7) check "C7" "POST /reports rejects unknown report_type (422)" "$val" ;;
            C8) check "C8" "POST /batch-import accepts partial CSV (not 422)" "$val" ;;
            C9) check "C9" "GET /search accepts wildcard * query (not 422)" "$val" ;;
            C10) check "C10" "POST /webhooks accepts arbitrary JSON (not 422)" "$val" ;;
        esac
    done
else
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        check "$cid" "App failed to load (check /tmp/trap1_err.txt)" "fail"
    done
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
    "checks_total": $total,
    "strict_endpoints": ["users","items","orders","reports"],
    "relaxed_endpoints": ["batch-import","search","webhooks"]
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
