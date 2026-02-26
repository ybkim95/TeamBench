#!/usr/bin/env bash
# Seed-aware grader for INC3: Memory Leak Investigation & Fix
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

# ── Check 1: service.py exists and is syntactically valid Python ──────────────
check "python3 -c '
import ast
with open(\"service.py\", \"r\", encoding=\"utf-8\") as f:
    src = f.read()
ast.parse(src)
print(\"SERVICE_PY_VALID\")
'" "service_py_syntax_error"

# ── Check 2: service.py smoke test passes (exits 0) ───────────────────────────
check "python3 service.py" "smoke_test_fails"

# ── Check 3: heap_sim.py exists and runs in fixed mode without error ──────────
check "python3 heap_sim.py --fixed" "heap_sim_fails"

# ── Check 4: check_fix.py passes ─────────────────────────────────────────────
check "python3 check_fix.py" "check_fix_fails"

# ── Check 5: Leak is fixed — LEAK: annotation context has been addressed ──────
# We look at the 15 lines surrounding each "# LEAK:" annotation.
# The fix must introduce a bounding/release mechanism in that local context.
# This is intentionally context-local to avoid false-positives from red herring code.
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
leak_type = expected[\"leak_type\"]

with open(\"service.py\", \"r\", encoding=\"utf-8\") as f:
    lines = f.readlines()

# Fix markers that must appear NEAR (within 20 lines before or 30 lines after)
# the original LEAK annotation site. These are chosen to be exclusive to
# the fix, not present in any red herring code.
fix_near_markers = {
    \"unbounded_cache\":      [\"maxsize=\", \"MAX =\", \"MAX=\", \"maxlen\", \"if len(\"],
    \"event_listener_leak\":  [\"remove(\", \"unsubscribe(\", \"_listeners[\", \"once\", \"one_shot\"],
    \"connection_pool_leak\": [\"finally:\", \"finally :\", \".release(conn\", \"with conn\", \"__exit__\"],
    \"circular_reference\":   [\"weakref.ref\", \"weak_ref\", \"del registry\", \"del _request\",
                               \".pop(request_id\", \".pop(ctx\"],
    \"global_list_append\":   [\"maxlen=\", \"deque(maxlen\", \"if len(\", \"[-\", \"= deque(\"],
}
markers = fix_near_markers.get(leak_type, [])

# Find all LEAK annotation lines
leak_line_indices = [i for i, ln in enumerate(lines) if \"# LEAK:\" in ln]

if not leak_line_indices:
    # LEAK annotation removed entirely — check that we have the marker somewhere near
    # where the leak function used to be (within 60 lines of the function definition)
    # Accept: annotation was replaced with fix code
    full_src = \"\".join(lines)
    found_global = [m for m in markers if m in full_src]
    assert found_global, f\"LEAK annotation removed but no fix marker found globally for {leak_type}\"
    print(f\"LEAK_ANNOTATION_REPLACED: fix markers {found_global} present\")
else:
    # Check context around each LEAK line
    fixed = False
    for idx in leak_line_indices:
        start = max(0, idx - 20)
        end = min(len(lines), idx + 30)
        context = \"\".join(lines[start:end])
        found = [m for m in markers if m in context]
        if found:
            fixed = True
            print(f\"LEAK_FIXED at line {idx+1}: markers {found} found nearby\")
            break
    if not fixed:
        # Also accept: the leak line itself has been commented out or changed
        leak_lines_content = [lines[i].rstrip() for i in leak_line_indices]
        all_commented = all(ln.strip().startswith(\"#\") for ln in leak_lines_content)
        assert all_commented, (
            f\"LEAK annotation still present and not fixed. \"
            f\"Expected one of {markers} near LEAK site. \"
            f\"LEAK lines: {leak_lines_content[:2]}\"
        )
        print(f\"LEAK_LINE_COMMENTED_OUT: accepted as fix\")
'" "leak_not_fixed"

# ── Check 6: Red herring code still present (not unnecessarily removed) ────────
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
rh_ids = expected.get(\"red_herring_ids\", [])

with open(\"service.py\", \"r\") as f:
    src = f.read()

# Map red herring id to a characteristic identifier unique to that red herring block
rh_markers = {
    \"lru_cache\":      \"_compute_metrics\",
    \"fixed_deque\":    \"_audit_log\",
    \"ttl_dict\":       \"_session_store\",
    \"large_constant\": \"_LOOKUP_TABLE\",
}

missing = []
for rh_id in rh_ids:
    marker = rh_markers.get(rh_id)
    if marker and marker not in src:
        missing.append(f\"{rh_id} (marker: {marker})\")

assert not missing, f\"Red herring code removed: {missing}\"
print(f\"RED_HERRINGS_INTACT: {rh_ids}\")
'" "red_herrings_removed"

# ── Check 7: No new syntax errors after fix ────────────────────────────────────
check "python3 -c '
import py_compile, sys
try:
    py_compile.compile(\"service.py\", doraise=True)
    print(\"NO_SYNTAX_ERRORS\")
except py_compile.PyCompileError as e:
    print(f\"SYNTAX_ERROR: {e}\", file=sys.stderr)
    sys.exit(1)
'" "new_syntax_errors"

# ── Check 8: Fix is structural (not a restart/kill workaround) ────────────────
check "python3 -c '
with open(\"service.py\", \"r\") as f:
    src = f.read()

workaround_signals = [
    \"os.execv\",
    \"os.kill(os.getpid\",
]
bad = [s for s in workaround_signals if s in src]
assert not bad, f\"Workaround detected: {bad}\"
print(\"NO_WORKAROUNDS\")
'" "workaround_detected"

# ── Check 9: heap_sim shows memory stabilizes (--fixed exits 0) ───────────────
check "python3 -c '
import subprocess, sys
result = subprocess.run(
    [sys.executable, \"heap_sim.py\", \"--fixed\"],
    capture_output=True, text=True, timeout=30,
)
assert result.returncode == 0, f\"heap_sim.py --fixed failed: {result.stderr[:200]}\"
print(\"HEAP_SIM_STABLE\")
'" "heap_not_stable"

# ── Check 10: Main processing function still present and callable ──────────────
check "python3 -c '
import json, sys, subprocess
expected = json.load(open(\"$EXPECTED\"))
smoke_fn = expected.get(\"smoke_test_fn\", \"process_request\")

with open(\"service.py\", \"r\") as f:
    src = f.read()

assert f\"def {smoke_fn}\" in src, f\"Processing function {smoke_fn!r} removed\"
assert \"def run_smoke_test\" in src, \"run_smoke_test() removed\"

r = subprocess.run([sys.executable, \"service.py\"], capture_output=True, text=True, timeout=15)
assert r.returncode == 0, f\"Exit {r.returncode}: {r.stderr[:200]}\"
print(f\"SERVICE_FUNCTIONAL: {smoke_fn} present\")
'" "service_not_functional"

# ── Check 11: LEAK annotation line context is genuinely different from original ─
# We verify that either: the LEAK line was removed, or the surrounding code
# has a fix construct that is specific to this leak type and not in the original
# red herring code (using function-name anchored context).
check "python3 -c '
import json
expected = json.load(open(\"$EXPECTED\"))
leak_type = expected[\"leak_type\"]

with open(\"service.py\", \"r\") as f:
    lines = f.readlines()

# Leak function names — anchor our context search to the function that contained the leak
leak_fn_anchors = {
    \"unbounded_cache\":      [\"def _set_cached\", \"def _get_cached\"],
    \"event_listener_leak\":  [\"def _register_request_listener\"],
    \"connection_pool_leak\": [\"def _handle_db_operation\"],
    \"circular_reference\":   [\"def _start_request\", \"def _end_request\"],
    \"global_list_append\":   [\"def _record_request\"],
}
# Fix constructs that are specific to each leak type fix.
# For connection_pool_leak we check for non-comment lines containing release.
fix_constructs = {
    \"unbounded_cache\":      [\"maxsize=\", \"MAX =\", \"MAX=\", \"if len(\", \"maxlen\"],
    \"event_listener_leak\":  [\"remove(\", \"unsubscribe(\", \"once\", \"one_shot\"],
    \"connection_pool_leak\": [\"finally:\", \"with conn\", \"__RELEASE_CHECK__\"],
    \"circular_reference\":   [\"weakref.ref\", \"weak_ref\", \".pop(\"],
    \"global_list_append\":   [\"maxlen=\", \"deque(maxlen\", \"if len(\", \"[-\"],
}

# Special check for connection_pool_leak: find a non-comment line with .release(conn
if leak_type == \"connection_pool_leak\":
    fn_lines = []
    capturing = False
    for i, ln in enumerate(lines):
        if any(a in ln for a in anchors):
            capturing = True
        if capturing:
            fn_lines.append(ln)
        if capturing and len(fn_lines) > 40:
            break
    release_lines = [ln for ln in fn_lines if \".release(conn\" in ln and not ln.strip().startswith(\"#\")]
    if release_lines:
        print(f\"LEAK_FN_FIXED (connection_pool): non-comment release call found\")
        sys.exit(0)

anchors = leak_fn_anchors.get(leak_type, [])
constructs = fix_constructs.get(leak_type, [])

# Find the leak function in the file
fn_line_idx = None
for i, line in enumerate(lines):
    for anchor in anchors:
        if anchor in line:
            fn_line_idx = i
            break
    if fn_line_idx is not None:
        break

if fn_line_idx is None:
    # Function was completely rewritten or removed — check global for fix construct
    full = \"\".join(lines)
    found = [c for c in constructs if c in full]
    assert found, f\"Leak function removed but no fix construct found globally\"
    print(f\"LEAK_FN_REWRITTEN: fix constructs {found}\")
else:
    # Extract the function body (up to 40 lines)
    start = fn_line_idx
    end = min(len(lines), fn_line_idx + 40)
    fn_body = \"\".join(lines[start:end])
    found = [c for c in constructs if c in fn_body]
    assert found, (
        f\"Leak function body has no fix construct. \"
        f\"Expected one of {constructs} in function starting at line {fn_line_idx+1}\"
    )
    print(f\"LEAK_FN_FIXED: constructs {found} in function body\")
'" "leak_fn_not_fixed"

# ── Check 12: Attestation verdict=pass ────────────────────────────────────────
check "python3 -c '
import json, sys
att = json.load(open(\"$SUBMISSION/attestation.json\"))
assert att.get(\"verdict\") == \"pass\", f\"verdict={att.get(chr(39)+chr(118)+chr(101)+chr(114)+chr(100)+chr(105)+chr(99)+chr(116)+chr(39))!r}\"
print(\"ATTESTATION_OK\")
'" "bad_attestation"

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
