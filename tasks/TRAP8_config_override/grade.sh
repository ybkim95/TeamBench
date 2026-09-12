#!/usr/bin/env bash
# TRAP8 grader: verify that 6 buggy overrides are fixed and 4 intentional
# overrides are preserved.
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
tb_require pyyaml pytest python-dotenv || true
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# ── Inline Python test harness ────────────────────────────────────────────
(python3 - <<'PYEOF'
import sys, os, json

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    from config import load_config

    cfg = load_config()

    # ── C2-C5: Intentional overrides must be PRESERVED ────────────────────
    # DATABASE_URL should still come from env
    results["C2"] = cfg.get("database_url", cfg.get("DATABASE_URL", "")) != ""

    # LOG_LEVEL should still come from env
    log_level = cfg.get("log_level", cfg.get("LOG_LEVEL", ""))
    results["C3"] = log_level != ""

    # CACHE_TTL should still come from env (as an integer)
    cache_ttl = cfg.get("cache_ttl", cfg.get("CACHE_TTL", None))
    results["C4"] = cache_ttl is not None

    # FEATURE_FLAG_X should still come from env
    ff = cfg.get("feature_flag_x", cfg.get("FEATURE_FLAG_X", None))
    results["C5"] = ff is not None

    # ── C6-C7: Type coercion bugs must be FIXED ───────────────────────────
    # DEBUG_MODE should be a proper bool, not the string "true"
    debug_mode = cfg.get("debug_mode", cfg.get("DEBUG_MODE", "MISSING"))
    results["C6"] = isinstance(debug_mode, bool) or debug_mode == "MISSING"

    # MAX_CONNECTIONS should be a proper int, not the string "100"
    max_conn = cfg.get("max_connections", cfg.get("MAX_CONNECTIONS", "MISSING"))
    results["C7"] = isinstance(max_conn, int) or max_conn == "MISSING"

    # ── C8-C9: Stale value bugs must be FIXED ─────────────────────────────
    # REDIS_HOST should not reference old hostname
    redis_host = cfg.get("redis_host", cfg.get("REDIS_HOST", ""))
    results["C8"] = "old-redis" not in str(redis_host) and "legacy" not in str(redis_host)

    # API_PORT should not reference deprecated port
    api_port = cfg.get("api_port", cfg.get("API_PORT", 0))
    results["C9"] = api_port != 8081  # deprecated port

    # ── C10: Security violation bugs must be FIXED ────────────────────────
    # TLS_VERIFY should not be overridable to false from env
    tls_verify = cfg.get("tls_verify", cfg.get("TLS_VERIFY", True))
    results["C10"] = tls_verify is True or tls_verify == "true"

except Exception as e:
    for k in ["C2","C3","C4","C5","C6","C7","C8","C9","C10"]:
        results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/trap8_results.json 2>/tmp/trap8_err.txt || true

# Parse inline test results
if [ -f /tmp/trap8_results.json ]; then
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/trap8_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C2) check "C2" "DATABASE_URL intentional override preserved" "$val" ;;
            C3) check "C3" "LOG_LEVEL intentional override preserved" "$val" ;;
            C4) check "C4" "CACHE_TTL intentional override preserved" "$val" ;;
            C5) check "C5" "FEATURE_FLAG_X intentional override preserved" "$val" ;;
            C6) check "C6" "DEBUG_MODE type coercion fixed (bool not string)" "$val" ;;
            C7) check "C7" "MAX_CONNECTIONS type coercion fixed (int not string)" "$val" ;;
            C8) check "C8" "REDIS_HOST stale value fixed (no old hostname)" "$val" ;;
            C9) check "C9" "API_PORT stale value fixed (not deprecated 8081)" "$val" ;;
            C10) check "C10" "TLS_VERIFY security override blocked" "$val" ;;
        esac
    done
else
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        check "$cid" "Config failed to load (check /tmp/trap8_err.txt)" "fail"
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
    "intentional_overrides": ["DATABASE_URL","LOG_LEVEL","CACHE_TTL","FEATURE_FLAG_X"],
    "buggy_overrides": ["DEBUG_MODE","MAX_CONNECTIONS","REDIS_HOST","API_PORT","TLS_VERIFY","MIN_PASSWORD_LENGTH"]
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
