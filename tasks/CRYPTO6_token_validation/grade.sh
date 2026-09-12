#!/usr/bin/env bash
# CRYPTO6 grader: verify JWT validation bugs fixed and refresh race conditions resolved.
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
tb_require pyjwt pytest || true
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# ── Inline Python test harness ────────────────────────────────────────────
(python3 - <<'PYEOF'
import sys, os, json, time, hmac, hashlib, base64

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    from auth import decode_token, validate_token, create_token, is_expired
    from config import SECRET_KEY, ALLOWED_ISSUERS

    # ── C2: Algorithm "none" must be rejected ─────────────────────────────
    # Craft a token with alg=none
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b'=').decode()
    payload_data = {
        "sub": "attacker",
        "iss": ALLOWED_ISSUERS[0] if ALLOWED_ISSUERS else "test-issuer",
        "exp": int(time.time()) + 3600
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).rstrip(b'=').decode()
    none_token = f"{header}.{payload}."
    try:
        result = validate_token(none_token)
        results["C2"] = result is None or result is False or (isinstance(result, dict) and result.get("error"))
    except Exception:
        results["C2"] = True  # Exception means rejection — correct

    # ── C3: Token at exact expiration must be rejected ────────────────────
    now = int(time.time())
    token_at_exp = create_token({"sub": "user1", "iss": ALLOWED_ISSUERS[0] if ALLOWED_ISSUERS else "test-issuer"}, expires_in=0)
    time.sleep(0.1)
    try:
        result = validate_token(token_at_exp)
        results["C3"] = result is None or result is False or (isinstance(result, dict) and result.get("error"))
    except Exception:
        results["C3"] = True

    # ── C4: Grace window must be zero — expired token rejected immediately ─
    expired_token = create_token({"sub": "user2", "iss": ALLOWED_ISSUERS[0] if ALLOWED_ISSUERS else "test-issuer"}, expires_in=-10)
    try:
        result = validate_token(expired_token)
        results["C4"] = result is None or result is False or (isinstance(result, dict) and result.get("error"))
    except Exception:
        results["C4"] = True

    # ── C5: Invalid issuer must be rejected ───────────────────────────────
    bad_issuer_token = create_token({"sub": "user3", "iss": "evil-issuer.example.com"}, expires_in=3600)
    try:
        result = validate_token(bad_issuer_token)
        results["C5"] = result is None or result is False or (isinstance(result, dict) and result.get("error"))
    except Exception:
        results["C5"] = True

    # ── C6: Valid token with correct issuer must be accepted ──────────────
    valid_token = create_token({"sub": "user4", "iss": ALLOWED_ISSUERS[0] if ALLOWED_ISSUERS else "test-issuer"}, expires_in=3600)
    try:
        result = validate_token(valid_token)
        results["C6"] = result is not None and result is not False
        if isinstance(result, dict):
            results["C6"] = not result.get("error")
    except Exception:
        results["C6"] = False

except Exception as e:
    for k in ["C2","C3","C4","C5","C6"]:
        results[k] = False
    results["_error"] = str(e)

# ── Refresh race condition checks ─────────────────────────────────────────
try:
    from refresh import refresh_token, _blacklist, _refresh_lock
    from auth import create_token, validate_token
    from config import ALLOWED_ISSUERS

    # ── C7: Old token blacklisted after refresh ───────────────────────────
    old_token = create_token({"sub": "user5", "iss": ALLOWED_ISSUERS[0] if ALLOWED_ISSUERS else "test-issuer"}, expires_in=3600)
    new_token = refresh_token(old_token)
    # Check that old token is now invalid (blacklisted)
    try:
        result = validate_token(old_token)
        results["C7"] = result is None or result is False or (isinstance(result, dict) and result.get("error"))
    except Exception:
        results["C7"] = True  # Rejection is correct

    # ── C8: Refreshed token is valid ──────────────────────────────────────
    if new_token:
        try:
            result = validate_token(new_token)
            results["C8"] = result is not None and result is not False
            if isinstance(result, dict):
                results["C8"] = not result.get("error")
        except Exception:
            results["C8"] = False
    else:
        results["C8"] = False

    # ── C9: Blacklist mechanism exists ────────────────────────────────────
    # Check that a blacklist data structure exists and is used
    import inspect
    refresh_src = inspect.getsource(refresh_token)
    results["C9"] = "blacklist" in refresh_src.lower() or "revoke" in refresh_src.lower() or "invalid" in refresh_src.lower()

except Exception as e:
    for k in ["C7","C8","C9"]:
        if k not in results:
            results[k] = False

# ── C10: Concurrent refresh protection ────────────────────────────────────
try:
    import inspect
    from refresh import refresh_token
    refresh_src = inspect.getsource(refresh_token)
    results["C10"] = "lock" in refresh_src.lower() or "atomic" in refresh_src.lower() or "mutex" in refresh_src.lower() or "synchronized" in refresh_src.lower()
except Exception:
    results["C10"] = False

print(json.dumps(results))
PYEOF
) > /tmp/crypto6_results.json 2>/tmp/crypto6_err.txt || true

# Parse inline test results
if [ -f /tmp/crypto6_results.json ]; then
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/crypto6_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C2) check "C2" "Algorithm none rejected" "$val" ;;
            C3) check "C3" "Token at exact expiration rejected" "$val" ;;
            C4) check "C4" "Grace window is zero (expired token rejected)" "$val" ;;
            C5) check "C5" "Invalid issuer rejected" "$val" ;;
            C6) check "C6" "Valid token with correct issuer accepted" "$val" ;;
            C7) check "C7" "Old token blacklisted after refresh" "$val" ;;
            C8) check "C8" "Refreshed token is valid" "$val" ;;
            C9) check "C9" "Blacklist mechanism exists in refresh" "$val" ;;
            C10) check "C10" "Concurrent refresh protection (lock/atomic)" "$val" ;;
        esac
    done
else
    for cid in C2 C3 C4 C5 C6 C7 C8 C9 C10; do
        check "$cid" "Auth module failed to load (check /tmp/crypto6_err.txt)" "fail"
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
    "validation_bugs": ["alg_none","exp_off_by_one","grace_window","missing_iss"],
    "race_conditions": ["no_blacklist","concurrent_refresh"]
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
