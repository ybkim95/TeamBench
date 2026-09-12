#!/usr/bin/env bash
# DIST6 grader: verify distributed lock bugs are fixed.
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
import sys, os, json, time, inspect

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    from distributed_lock import DistributedLock
    from mock_redis import MockRedis

    backend = MockRedis()

    # ── C2: acquire() returns a fencing token (not just bool) ─────────────
    lock = DistributedLock("test-resource-1", backend, node_id="node-A")
    result = lock.acquire()
    # Fencing token should be an int or similar, not just True/False
    results["C2"] = result is not None and result is not True and result is not False
    if result:
        lock.release()

    # ── C3: Fencing tokens are monotonically increasing ───────────────────
    lock_a = DistributedLock("test-resource-2", backend, node_id="node-A")
    lock_b = DistributedLock("test-resource-2", backend, node_id="node-B")
    token_a = lock_a.acquire()
    lock_a.release()
    token_b = lock_b.acquire()
    if token_a is not None and token_b is not None:
        try:
            results["C3"] = int(token_b) > int(token_a)
        except (TypeError, ValueError):
            results["C3"] = False
    else:
        results["C3"] = False
    if token_b:
        lock_b.release()

    # ── C4: TTL is calculated AFTER lock is set ───────────────────────────
    src = inspect.getsource(DistributedLock.acquire)
    # Check that time is captured after the set operation, or elapsed time is subtracted
    # Look for patterns like: time.time() after set, or ttl - elapsed, or end_time
    has_post_set_time = ("elapsed" in src.lower() or
                         "end_time" in src.lower() or
                         "after" in src.lower() or
                         "remaining" in src.lower() or
                         "time.monotonic" in src.lower())
    results["C4"] = has_post_set_time

    # ── C5: Retry uses exponential backoff (not fixed delay) ──────────────
    src_acquire = inspect.getsource(DistributedLock.acquire)
    has_backoff = ("backoff" in src_acquire.lower() or
                   "exponential" in src_acquire.lower() or
                   "2 **" in src_acquire or
                   "2**" in src_acquire or
                   "pow(2" in src_acquire or
                   "attempt" in src_acquire.lower() or
                   "<< " in src_acquire)
    results["C5"] = has_backoff

    # ── C6: Retry uses jitter ─────────────────────────────────────────────
    has_jitter = ("jitter" in src_acquire.lower() or
                  "random" in src_acquire.lower() or
                  "uniform" in src_acquire.lower())
    results["C6"] = has_jitter

    # ── C7: Release checks ownership ──────────────────────────────────────
    backend2 = MockRedis()
    lock_x = DistributedLock("contested-resource", backend2, node_id="node-X")
    lock_y = DistributedLock("contested-resource", backend2, node_id="node-Y")

    token_x = lock_x.acquire()
    # node-Y tries to release node-X's lock — should fail
    try:
        release_result = lock_y.release()
        # Lock should still be held by node-X
        if release_result is False:
            results["C7"] = True
        else:
            # Check if the lock is still held
            token_y = lock_y.acquire()
            results["C7"] = token_y is None or token_y is False  # should fail because X still holds it
    except Exception:
        results["C7"] = True  # Exception on unauthorized release is correct

    # ── C8: release() source checks owner/node identity ───────────────────
    src_release = inspect.getsource(DistributedLock.release)
    has_owner_check = ("owner" in src_release.lower() or
                       "node_id" in src_release.lower() or
                       "holder" in src_release.lower() or
                       "identity" in src_release.lower())
    results["C8"] = has_owner_check

    # ── C9: Lock stores owner identity ────────────────────────────────────
    src_full = inspect.getsource(DistributedLock)
    stores_owner = ("node_id" in src_full or
                    "owner" in src_full.lower() or
                    "holder" in src_full.lower())
    results["C9"] = stores_owner

except Exception as e:
    for k in ["C2","C3","C4","C5","C6","C7","C8","C9"]:
        if k not in results:
            results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/dist6_results.json 2>/tmp/dist6_err.txt || true

# Parse inline test results
if [ -f /tmp/dist6_results.json ]; then
    for cid in C2 C3 C4 C5 C6 C7 C8 C9; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/dist6_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C2) check "C2" "acquire() returns fencing token (not bool)" "$val" ;;
            C3) check "C3" "Fencing tokens are monotonically increasing" "$val" ;;
            C4) check "C4" "TTL calculated after lock set (not stale)" "$val" ;;
            C5) check "C5" "Retry uses exponential backoff" "$val" ;;
            C6) check "C6" "Retry uses jitter" "$val" ;;
            C7) check "C7" "Release by non-owner is rejected" "$val" ;;
            C8) check "C8" "release() checks owner identity" "$val" ;;
            C9) check "C9" "Lock stores owner identity" "$val" ;;
        esac
    done
else
    for cid in C2 C3 C4 C5 C6 C7 C8 C9; do
        check "$cid" "Lock module failed to load (check /tmp/dist6_err.txt)" "fail"
    done
fi

# ── C10: No debug/TODO left in code ──────────────────────────────────────
if grep -rqE "TODO|FIXME|HACK|debugger|breakpoint" distributed_lock.py 2>/dev/null; then
    check "C10" "No debug/TODO markers in distributed_lock.py" "fail"
else
    check "C10" "No debug/TODO markers in distributed_lock.py" "pass"
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
    "bugs": ["no_fencing_token","stale_ttl","fixed_retry","unchecked_release"]
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
