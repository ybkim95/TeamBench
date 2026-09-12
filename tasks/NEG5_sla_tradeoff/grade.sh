#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

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

# 1. tiers.py imports
check "python3 -c 'from tiers import TIERS'" "import_error"

# 2. All 5 tiers exist
check "python3 -c \"
from tiers import TIERS
assert len(TIERS) == 5, f'Expected 5 tiers, got {len(TIERS)}'
print('COUNT_OK')
\"" "wrong_tier_count"

# 3. All tiers pass constraint check
check "python3 -c \"
from tiers import TIERS
from constraints import check_tier
for name, tier in TIERS.items():
    errors = check_tier(tier)
    assert not errors, f'{name}: {errors}'
print('ALL_VALID')
\"" "constraint_violations"

# 4. Premium tier has strong consistency
check "python3 -c \"
from tiers import TIERS
assert TIERS['premium']['consistency'] == 'strong', 'premium must have strong consistency'
print('PREMIUM_CONSISTENCY')
\"" "premium_wrong_consistency"

# 5. Premium tier has latency >= 50
check "python3 -c \"
from tiers import TIERS
assert TIERS['premium']['latency_ms'] >= 50, f'premium latency {TIERS[\"premium\"][\"latency_ms\"]} < 50'
print('PREMIUM_LATENCY')
\"" "premium_impossible_latency"

# 6. Enterprise tier has strong consistency
check "python3 -c \"
from tiers import TIERS
assert TIERS['enterprise']['consistency'] == 'strong', 'enterprise must have strong consistency'
print('ENTERPRISE_CONSISTENCY')
\"" "enterprise_wrong_consistency"

# 7. Enterprise tier has availability <= 99.9
check "python3 -c \"
from tiers import TIERS
assert TIERS['enterprise']['availability_pct'] <= 99.9, f'enterprise availability too high'
print('ENTERPRISE_AVAIL')
\"" "enterprise_impossible_availability"

# 8. Realtime tier has low latency maintained
check "python3 -c \"
from tiers import TIERS
assert TIERS['realtime']['latency_ms'] <= 50, 'realtime should keep low latency'
print('REALTIME_LATENCY')
\"" "realtime_lost_low_latency"

# 9. test_tiers.py passes
check "python3 -m pytest test_tiers.py -q 2>/dev/null || python3 -m unittest test_tiers 2>/dev/null" \
      "tests_fail"

# 10. Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
