#!/usr/bin/env bash
# INT2 grader: verify v1->v2 API migration with 5 breaking changes + 2 shims
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=12
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

# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require flask pytest || true

# Run inline tests via Python
(python3 - <<'PYEOF'
import sys, os, json

sys.path.insert(0, ".")
results = {}

try:
    from api.app import app
    client = app.test_client()
    app.config["TESTING"] = True

    # ── V2 BREAKING CHANGES ─────────────────────────────────────────────────

    # C1: V2 uses display_name field (rename from user_name)
    r = client.get("/v2/users/1", headers={"Authorization": "Bearer test-token"})
    if r.status_code == 200:
        data = r.get_json()
        # Handle wrapped response
        inner = data.get("data", data)
        results["C1"] = "display_name" in inner
    else:
        results["C1"] = False

    # C2: V2 wraps response in {"data": ..., "meta": ...}
    r = client.get("/v2/users/1", headers={"Authorization": "Bearer test-token"})
    if r.status_code == 200:
        data = r.get_json()
        results["C2"] = "data" in data and "meta" in data
    else:
        results["C2"] = False

    # C3: V2 uses cursor-based pagination
    r = client.get("/v2/users?cursor=abc&limit=10", headers={"Authorization": "Bearer test-token"})
    if r.status_code == 200:
        data = r.get_json()
        inner = data.get("data", data)
        # Should have cursor-based pagination fields
        meta = data.get("meta", data)
        results["C3"] = "cursor" in str(meta) or "next_cursor" in str(meta) or "cursor" in str(data)
    else:
        results["C3"] = False

    # C4: V2 uses new error format {"errors": [{"code": ..., "message": ...}]}
    r = client.get("/v2/users/99999", headers={"Authorization": "Bearer test-token"})
    if r.status_code in (404, 400):
        data = r.get_json()
        results["C4"] = "errors" in data and isinstance(data.get("errors"), list)
    else:
        results["C4"] = False

    # ── SHIM CHECKS (backward compat) ───────────────────────────────────────

    # C5: V2 response includes BOTH user_name AND display_name (shim for mobile)
    r = client.get("/v2/users/1", headers={"Authorization": "Bearer test-token"})
    if r.status_code == 200:
        data = r.get_json()
        inner = data.get("data", data)
        results["C5"] = "user_name" in inner and "display_name" in inner
    else:
        results["C5"] = False

    # C6: V2 auth accepts BOTH X-API-Key AND Authorization Bearer (shim for mobile)
    r1 = client.get("/v2/users/1", headers={"Authorization": "Bearer test-token"})
    r2 = client.get("/v2/users/1", headers={"X-API-Key": "test-api-key"})
    results["C6"] = r1.status_code == 200 and r2.status_code == 200

    # ── CLEAN BREAKS (no backward compat) ───────────────────────────────────

    # C7: V2 does NOT accept old page/per_page pagination (clean break)
    r = client.get("/v2/users?page=1&per_page=10", headers={"Authorization": "Bearer test-token"})
    if r.status_code == 200:
        data = r.get_json()
        # Should use cursor pagination, not page-based
        meta = data.get("meta", data)
        results["C7"] = "page" not in str(meta) or "cursor" in str(meta)
    else:
        results["C7"] = True  # Rejecting old pagination is also acceptable

    # C8: V2 error format is new style (clean break, no old {"error": "msg"})
    r = client.get("/v2/users/99999", headers={"Authorization": "Bearer test-token"})
    if r.status_code in (404, 400):
        data = r.get_json()
        results["C8"] = "errors" in data and "error" not in data
    else:
        results["C8"] = False

    # ── V1 ENDPOINTS STILL WORK ─────────────────────────────────────────────

    # C9: V1 endpoints still respond (not removed)
    r = client.get("/v1/users/1", headers={"X-API-Key": "test-api-key"})
    results["C9"] = r.status_code == 200

    # C10: V1 uses old field name user_name
    r = client.get("/v1/users/1", headers={"X-API-Key": "test-api-key"})
    if r.status_code == 200:
        data = r.get_json()
        results["C10"] = "user_name" in data
    else:
        results["C10"] = False

    # ── SYNTAX/IMPORT CHECKS ────────────────────────────────────────────────

    # C11: All Python files have valid syntax
    import ast
    valid = True
    for f in ["api/app.py", "api/models.py"]:
        try:
            ast.parse(open(f).read())
        except (SyntaxError, FileNotFoundError):
            valid = False
    results["C11"] = valid

    # C12: pytest passes
    import subprocess
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
        capture_output=True, text=True, timeout=30
    )
    results["C12"] = "passed" in r.stdout and "failed" not in r.stdout

except Exception as e:
    for k in [f"C{i}" for i in range(1, 13)]:
        if k not in results:
            results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/int2_results.json 2>/tmp/int2_err.txt || true

# Parse results
if [ -f /tmp/int2_results.json ]; then
    for cid in C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/int2_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C1) check "C1" "V2 uses display_name field" "$val" ;;
            C2) check "C2" "V2 wraps response in data/meta envelope" "$val" ;;
            C3) check "C3" "V2 uses cursor-based pagination" "$val" ;;
            C4) check "C4" "V2 uses new error format with errors array" "$val" ;;
            C5) check "C5" "V2 includes both user_name and display_name (shim)" "$val" ;;
            C6) check "C6" "V2 accepts both X-API-Key and Bearer token (shim)" "$val" ;;
            C7) check "C7" "V2 pagination is cursor-based (clean break)" "$val" ;;
            C8) check "C8" "V2 error format is new only (clean break)" "$val" ;;
            C9) check "C9" "V1 endpoints still respond" "$val" ;;
            C10) check "C10" "V1 uses old user_name field" "$val" ;;
            C11) check "C11" "All Python files have valid syntax" "$val" ;;
            C12) check "C12" "pytest tests pass" "$val" ;;
        esac
    done
else
    for cid in C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12; do
        check "$cid" "App failed to load" "fail"
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
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
