#!/usr/bin/env bash
# TS1_type_mismatch grader
# Checks: tsc --noEmit passes, ts-node test.ts passes, no @ts-ignore suppressions added
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

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

# ── C1: npm install succeeds ──────────────────────────────────────────────────
npm install --prefer-offline 2>&1 >/dev/null && npm_ok="pass" || npm_ok="fail"
check "C1" "npm install succeeds" "$npm_ok"

# ── C2: tsc --noEmit exits 0 (no TypeScript errors) ──────────────────────────
tsc_output=$(npx tsc --noEmit 2>&1 || true)
tsc_errors=$(echo "$tsc_output" | grep -c "error TS" || true)
if [ "$tsc_errors" -eq 0 ]; then
    check "C2" "tsc --noEmit exits 0 (no type errors)" "pass"
else
    check "C2" "tsc --noEmit exits 0 (no type errors) — got ${tsc_errors} error(s)" "fail"
fi

# ── C3: No @ts-ignore suppressions added ─────────────────────────────────────
ignore_count=$(grep -h "@ts-ignore\|@ts-expect-error" handlers.ts service.ts 2>/dev/null | wc -l || true)
if [ "$ignore_count" -eq 0 ]; then
    check "C3" "No @ts-ignore or @ts-expect-error suppressions added" "pass"
else
    check "C3" "No @ts-ignore or @ts-expect-error suppressions — found ${ignore_count}" "fail"
fi

# ── C4: types.ts was not modified ────────────────────────────────────────────
# Compare against expected.json if available, otherwise check for common violations
if [ -f "${REPORTS}/expected.json" ]; then
    expected_entity=$(python3 -c "import json; d=json.load(open('${REPORTS}/expected.json')); print(d.get('entity',''))" 2>/dev/null || echo "")
    if [ -n "$expected_entity" ]; then
        # types.ts must still export the expected interface
        if grep -q "export interface ${expected_entity}" types.ts 2>/dev/null; then
            check "C4" "types.ts still exports ${expected_entity} interface unchanged" "pass"
        else
            check "C4" "types.ts still exports ${expected_entity} interface" "fail"
        fi
    else
        check "C4" "types.ts present and unchanged (entity name unknown)" "pass"
    fi
else
    check "C4" "types.ts present" "$([ -f types.ts ] && echo pass || echo fail)"
fi

# ── C5: test.ts was not modified ─────────────────────────────────────────────
# The test file should still contain the typed assertion patterns
if grep -q "Promise<void>" test.ts 2>/dev/null; then
    check "C5" "test.ts not modified (type check signature present)" "pass"
else
    check "C5" "test.ts not modified" "fail"
fi

# ── C6: handlers.ts exists and has required exports ──────────────────────────
if [ -f handlers.ts ]; then
    export_count=$(grep -c "^export async function" handlers.ts 2>/dev/null || true)
    if [ "$export_count" -ge 3 ]; then
        check "C6" "handlers.ts exports at least 3 handler functions" "pass"
    else
        check "C6" "handlers.ts exports at least 3 handler functions (found ${export_count})" "fail"
    fi
else
    check "C6" "handlers.ts exists" "fail"
fi

# ── C7: service.ts exists and exports service object ─────────────────────────
if grep -q "export const.*Service" service.ts 2>/dev/null; then
    check "C7" "service.ts exports service object" "pass"
else
    check "C7" "service.ts exports service object" "fail"
fi

# ── C8-C10: ts-node test.ts passes ───────────────────────────────────────────
test_output=$(npx ts-node test.ts 2>&1)
test_exit=$?

# C8: test runner exits 0
if [ "$test_exit" = "0" ]; then
    check "C8" "ts-node test.ts exits 0" "pass"
else
    check "C8" "ts-node test.ts exits 0" "fail"
fi

# C9: at least 3 PASS lines in test output
pass_count=$(echo "$test_output" | grep -c "PASS" || true)
if [ "$pass_count" -ge 3 ]; then
    check "C9" "At least 3 test assertions pass (got ${pass_count})" "pass"
else
    check "C9" "At least 3 test assertions pass (got ${pass_count})" "fail"
fi

# C10: no FAIL lines in test output
fail_count=$(echo "$test_output" | grep -c "FAIL" || true)
if [ "$fail_count" -eq 0 ]; then
    check "C10" "No test assertions fail" "pass"
else
    check "C10" "No test assertions fail (got ${fail_count} failures)" "fail"
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
