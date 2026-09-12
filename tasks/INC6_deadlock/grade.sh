#!/usr/bin/env bash
# Seed-aware grader for INC6: Distributed Deadlock Diagnosis & Fix
# Reads expected values from expected.json for seed-specific grading.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

cd "$WORKSPACE"

# ── Check 1: buggy service file is syntactically valid Python ─────────────────
check "python3 -c '
import ast, json, sys
expected = json.load(open(\"$EXPECTED\"))
buggy = expected[\"buggy_service\"] + \".py\"
with open(buggy, \"r\", encoding=\"utf-8\") as f:
    src = f.read()
ast.parse(src)
print(f\"SYNTAX_OK: {buggy}\")
'" "buggy_service_syntax_error"

# ── Check 2: good service file is syntactically valid Python ──────────────────
check "python3 -c '
import ast, json, sys
expected = json.load(open(\"$EXPECTED\"))
good = expected[\"good_service\"] + \".py\"
with open(good, \"r\", encoding=\"utf-8\") as f:
    src = f.read()
ast.parse(src)
print(f\"SYNTAX_OK: {good}\")
'" "good_service_syntax_error"

# ── Check 3: buggy service smoke test passes ──────────────────────────────────
check "python3 -c '
import json, subprocess, sys
expected = json.load(open(\"$EXPECTED\"))
fname = expected[\"buggy_service\"] + \".py\"
result = subprocess.run([sys.executable, fname], capture_output=True, text=True, timeout=15)
assert result.returncode == 0, f\"exit {result.returncode}: {result.stderr[:200]}\"
print(f\"SMOKE_OK: {fname}\")
'" "buggy_service_smoke_fails"

# ── Check 4: good service smoke test passes ───────────────────────────────────
check "python3 -c '
import json, subprocess, sys
expected = json.load(open(\"$EXPECTED\"))
fname = expected[\"good_service\"] + \".py\"
result = subprocess.run([sys.executable, fname], capture_output=True, text=True, timeout=15)
assert result.returncode == 0, f\"exit {result.returncode}: {result.stderr[:200]}\"
print(f\"SMOKE_OK: {fname}\")
'" "good_service_smoke_fails"

# ── Check 5: Lock ordering fixed — buggy service acquires lock_a before lock_b ─
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
buggy_file = expected[\"buggy_service\"] + \".py\"
lock_a = expected[\"lock_a\"]
lock_b = expected[\"lock_b\"]

with open(buggy_file, \"r\") as f:
    lines = f.readlines()

# Find process_request() body and check lock acquisition order
first_a = None
first_b = None
in_fn = False
for i, line in enumerate(lines):
    if \"def process_request\" in line:
        in_fn = True
    if in_fn:
        if first_a is None and f\"with {lock_a}\" in line:
            first_a = i
        if first_b is None and f\"with {lock_b}\" in line:
            first_b = i
    # Stop at next method definition
    if in_fn and i > 0 and line.startswith(\"    def \") and \"process_request\" not in line:
        break

assert first_a is not None, f\"{lock_a} not found in process_request()\"
assert first_b is not None, f\"{lock_b} not found in process_request()\"
assert first_a < first_b, (
    f\"Lock ordering still wrong in {buggy_file}: \"
    f\"{lock_b} at line {first_b+1} before {lock_a} at line {first_a+1}\"
)
print(f\"LOCK_ORDER_FIXED: {lock_a} (line {first_a+1}) before {lock_b} (line {first_b+1})\")
'" "lock_ordering_not_fixed"

# ── Check 6: Red herring code NOT removed from buggy service ──────────────────
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
buggy_file = expected[\"buggy_service\"] + \".py\"
marker = expected[\"red_herring_marker\"]

with open(buggy_file, \"r\") as f:
    src = f.read()

assert marker in src, f\"Red herring code removed: marker {marker!r} missing from {buggy_file}\"
print(f\"RED_HERRING_INTACT: marker {marker!r} found\")
'" "red_herring_removed"

# ── Check 7: deadlock_sim.py --fixed exits 0 (no deadlock after fix) ─────────
check "python3 -c '
import subprocess, sys
result = subprocess.run(
    [sys.executable, \"deadlock_sim.py\", \"--fixed\"],
    capture_output=True, text=True, timeout=10,
)
assert result.returncode == 0, (
    f\"deadlock_sim.py --fixed exited {result.returncode}: {result.stdout[:300]}\"
)
print(\"DEADLOCK_SIM_FIXED: exits 0\")
'" "deadlock_sim_still_deadlocks"

# ── Check 8: check_fix.py passes ─────────────────────────────────────────────
check "python3 check_fix.py" "check_fix_fails"

# ── Check 9: Good service lock order unchanged (still lock_a then lock_b) ─────
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
good_file = expected[\"good_service\"] + \".py\"
lock_a = expected[\"lock_a\"]
lock_b = expected[\"lock_b\"]

with open(good_file, \"r\") as f:
    lines = f.readlines()

first_a = None
first_b = None
in_fn = False
for i, line in enumerate(lines):
    if \"def process_request\" in line:
        in_fn = True
    if in_fn:
        if first_a is None and f\"with {lock_a}\" in line:
            first_a = i
        if first_b is None and f\"with {lock_b}\" in line:
            first_b = i
    if in_fn and i > 0 and line.startswith(\"    def \") and \"process_request\" not in line:
        break

assert first_a is not None, f\"{lock_a} not found in {good_file} process_request()\"
assert first_b is not None, f\"{lock_b} not found in {good_file} process_request()\"
assert first_a < first_b, (
    f\"Good service lock order was changed! {lock_b} now before {lock_a} in {good_file}\"
)
print(f\"GOOD_SERVICE_UNCHANGED: {lock_a} before {lock_b}\")
'" "good_service_order_changed"

# ── Check 10: No lock-timeout-only workaround (must fix ordering, not mask) ───
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
buggy_file = expected[\"buggy_service\"] + \".py\"
lock_a = expected[\"lock_a\"]
lock_b = expected[\"lock_b\"]

with open(buggy_file, \"r\") as f:
    src = f.read()

# Detect if the fix is ONLY a timeout addition without fixing order
# True fix: lock_a is acquired before lock_b in process_request()
# We already verified this in check 5, but also check no restart workarounds
workaround_signals = [\"os.execv\", \"os.kill(os.getpid\", \"sys.exit(\" ]
# sys.exit in __main__ block is fine; flag only if inside process_request or _do_work
lines = src.splitlines()
in_bad_fn = False
for i, line in enumerate(lines):
    if \"def process_request\" in line or \"def _do_work\" in line:
        in_bad_fn = True
    if in_bad_fn and line.strip().startswith(\"def \") and \"process_request\" not in line and \"_do_work\" not in line:
        in_bad_fn = False
    if in_bad_fn:
        for sig in workaround_signals:
            assert sig not in line, f\"Workaround detected in {buggy_file} line {i+1}: {sig!r}\"
print(\"NO_WORKAROUNDS_IN_HANDLERS\")
'" "workaround_detected"

# ── Check 11: Lock hierarchy consistent — both services use same lock order ────
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
lock_a = expected[\"lock_a\"]
lock_b = expected[\"lock_b\"]

def get_order(fname):
    with open(fname, \"r\") as f:
        lines = f.readlines()
    first_a = first_b = None
    in_fn = False
    for i, line in enumerate(lines):
        if \"def process_request\" in line:
            in_fn = True
        if in_fn:
            if first_a is None and f\"with {lock_a}\" in line:
                first_a = i
            if first_b is None and f\"with {lock_b}\" in line:
                first_b = i
        if in_fn and i > 0 and line.startswith(\"    def \") and \"process_request\" not in line:
            break
    return first_a, first_b

f_buggy = expected[\"buggy_service\"] + \".py\"
f_good  = expected[\"good_service\"] + \".py\"

a_bug, b_bug = get_order(f_buggy)
a_good, b_good = get_order(f_good)

assert a_bug is not None and b_bug is not None, f\"Locks not found in {f_buggy}\"
assert a_good is not None and b_good is not None, f\"Locks not found in {f_good}\"

# Both must now have lock_a < lock_b
assert a_bug < b_bug, f\"{f_buggy}: still wrong order\"
assert a_good < b_good, f\"{f_good}: order broken\"
print(f\"LOCK_HIERARCHY_CONSISTENT: both services acquire {lock_a} before {lock_b}\")
'" "lock_hierarchy_inconsistent"

# ── Check 12: Attestation verdict=pass ────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Write score ────────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
