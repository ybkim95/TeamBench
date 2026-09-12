#!/usr/bin/env bash
# INC8 grader: verify timeout cascade fixed and harmful retries removed,
# while preserving correct retries.
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

# ── C1: pytest passes ─────────────────────────────────────────────────────
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# ── Inline Python test harness ────────────────────────────────────────────
(python3 - <<'PYEOF'
import sys, os, json, inspect

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    from config import (
        GATEWAY_TIMEOUT, ORDER_SERVICE_TIMEOUT, INVENTORY_SERVICE_TIMEOUT,
        GATEWAY_RETRY_CONFIG, ORDER_RETRY_CONFIG
    )

    # ── C2: Gateway timeout >= order_service timeout ──────────────────────
    results["C2"] = GATEWAY_TIMEOUT >= ORDER_SERVICE_TIMEOUT

    # ── C3: Order service timeout >= inventory_service timeout ────────────
    results["C3"] = ORDER_SERVICE_TIMEOUT >= INVENTORY_SERVICE_TIMEOUT

    # ── C4: Proper timeout hierarchy (gateway > order > inventory) ────────
    results["C4"] = GATEWAY_TIMEOUT >= ORDER_SERVICE_TIMEOUT >= INVENTORY_SERVICE_TIMEOUT

    # ── C5: GET /inventory/check retry is preserved (idempotent) ──────────
    # The retry config for GET operations should still be enabled
    get_retry = GATEWAY_RETRY_CONFIG.get("GET", {})
    results["C5"] = get_retry.get("enabled", False) is True or get_retry.get("max_retries", 0) > 0

    # ── C6: /health retry is preserved (idempotent) ───────────────────────
    health_retry = GATEWAY_RETRY_CONFIG.get("health", GATEWAY_RETRY_CONFIG.get("HEALTH", {}))
    results["C6"] = health_retry.get("enabled", False) is True or health_retry.get("max_retries", 0) > 0

except Exception as e:
    for k in ["C2","C3","C4","C5","C6"]:
        results[k] = False
    results["_error_config"] = str(e)

# ── Check retry fixes in source code ──────────────────────────────────────
try:
    # ── C7: POST /orders/create retry is disabled or has idempotency key ──
    from config import ORDER_RETRY_CONFIG
    post_retry = ORDER_RETRY_CONFIG.get("POST", ORDER_RETRY_CONFIG.get("create", {}))
    post_disabled = (post_retry.get("enabled", True) is False or
                     post_retry.get("max_retries", 1) == 0)
    # Or idempotency key is required
    has_idempotency = False
    try:
        src = open("order_service.py").read()
        has_idempotency = "idempotency" in src.lower() or "idempotent" in src.lower()
    except Exception:
        pass
    results["C7"] = post_disabled or has_idempotency

    # ── C8: Retry storm prevention (circuit breaker or retry budget) ──────
    try:
        order_src = open("order_service.py").read()
        gateway_src = open("gateway.py").read()
        combined = order_src + gateway_src
        has_protection = ("circuit" in combined.lower() or
                         "breaker" in combined.lower() or
                         "budget" in combined.lower() or
                         "max_total" in combined.lower() or
                         "retry_budget" in combined.lower() or
                         "no_retry_on_timeout" in combined.lower() or
                         "propagate" in combined.lower())
        results["C8"] = has_protection
    except Exception:
        results["C8"] = False

    # ── C9: Gateway source doesn't have the old broken timeout value ──────
    try:
        gateway_src = open("gateway.py").read()
        config_src = open("config.py").read()
        # Old broken pattern: gateway timeout < downstream timeout
        # The old gateway timeout was 5 (less than order_service 10)
        results["C9"] = "timeout=5" not in gateway_src.replace(" ", "") or GATEWAY_TIMEOUT >= ORDER_SERVICE_TIMEOUT
    except Exception:
        results["C9"] = False

except Exception as e:
    for k in ["C7","C8","C9"]:
        if k not in results:
            results[k] = False

# ── C10: Incident response documentation or comments ─────────────────────
try:
    all_src = ""
    for f in ["gateway.py", "order_service.py", "config.py"]:
        try:
            all_src += open(f).read()
        except Exception:
            pass
    # Check the code has no TODO/FIXME left
    results["C10"] = "TODO" not in all_src and "FIXME" not in all_src
except Exception:
    results["C10"] = False

print(json.dumps(results))
PYEOF
) > /tmp/inc8_results.json 2>/tmp/inc8_err.txt || true

# Parse inline test results
if [ -f /tmp/inc8_results.json ]; then
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/inc8_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C2) check "C2" "Gateway timeout >= order_service timeout" "$val" ;;
            C3) check "C3" "Order_service timeout >= inventory_service timeout" "$val" ;;
            C4) check "C4" "Proper timeout hierarchy across all 3 services" "$val" ;;
            C5) check "C5" "Idempotent GET retry preserved" "$val" ;;
            C6) check "C6" "Health check retry preserved" "$val" ;;
            C7) check "C7" "Non-idempotent POST retry disabled or has idempotency key" "$val" ;;
            C8) check "C8" "Retry storm prevention (circuit breaker or budget)" "$val" ;;
            C9) check "C9" "Broken gateway timeout value removed" "$val" ;;
            C10) check "C10" "No TODO/FIXME markers left in code" "$val" ;;
        esac
    done
else
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        check "$cid" "Services failed to load (check /tmp/inc8_err.txt)" "fail"
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
    "correct_retries": ["GET_inventory_check","health_check"],
    "harmful_retries": ["POST_orders_create","retry_storm_amplification"]
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
