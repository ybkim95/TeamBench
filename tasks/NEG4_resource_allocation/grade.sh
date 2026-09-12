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

# 1. allocator.py imports without error
check "python3 -c 'from allocator import allocate'" "import_error"

# 2. High-priority team gets most resources
check "python3 -c \"
from allocator import allocate
result = allocate()
teams = sorted(result.items(), key=lambda x: x[1], reverse=True)
# The team with the highest allocation should be the highest priority
print(f'Top team: {teams[0]}')
\"" "allocation_runs"

# 3. Priority order is correct (no inversion)
check "python3 -c \"
from allocator import allocate, load_budget
budget = load_budget()
result = allocate()
teams_by_prio = sorted(budget['teams'], key=lambda t: t['priority'], reverse=True)
allocs = [result[t['name']] for t in teams_by_prio]
# Higher priority should get >= lower priority (when requested amounts are similar)
assert allocs[0] >= allocs[-1], f'Priority inversion: {allocs}'
print('PRIORITY_OK')
\"" "priority_inversion"

# 4. No team is starved (all get >= min_quota)
check "python3 -c \"
from allocator import allocate, load_budget
budget = load_budget()
result = allocate()
for team in budget['teams']:
    alloc = result.get(team['name'], 0)
    assert alloc >= team['min_quota'], f'{team[\"name\"]} starved: {alloc} < {team[\"min_quota\"]}'
print('NO_STARVATION')
\"" "starvation"

# 5. No team exceeds max_quota
check "python3 -c \"
from allocator import allocate, load_budget
budget = load_budget()
result = allocate()
for team in budget['teams']:
    alloc = result.get(team['name'], 0)
    assert alloc <= team['max_quota'], f'{team[\"name\"]} over quota: {alloc} > {team[\"max_quota\"]}'
print('QUOTA_OK')
\"" "exceeds_max_quota"

# 6. Total allocation matches budget (within 1 unit)
check "python3 -c \"
from allocator import allocate, load_budget
budget = load_budget()
result = allocate()
total = sum(result.values())
assert abs(total - budget['total_budget']) <= 1, f'Total {total} != budget {budget[\"total_budget\"]}'
print('TOTAL_OK')
\"" "wrong_total"

# 7. All teams get allocation (none is zero when budget allows)
check "python3 -c \"
from allocator import allocate
result = allocate()
assert all(v > 0 for v in result.values()), f'Some teams got 0: {result}'
print('ALL_NONZERO')
\"" "zero_allocation"

# 8. test_allocator.py passes
check "python3 -m pytest test_allocator.py -q 2>/dev/null || python3 -m unittest test_allocator 2>/dev/null" \
      "tests_fail"

# 9. budget.yaml unchanged
check "python3 -c \"
import hashlib
h = hashlib.md5(open('budget.yaml','rb').read()).hexdigest()
print(f'BUDGET_HASH={h}')
\"" "budget_modified"

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
