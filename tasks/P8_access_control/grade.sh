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

EXPECTED_JSON="$REPORTS/expected.json"

# Load violations and exceptions from expected.json if available
VIOLATIONS='[]'
EXCEPTIONS='[]'
if [ -f "$EXPECTED_JSON" ]; then
  VIOLATIONS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('violations_to_fix', [])))" 2>/dev/null || echo '[]')
  EXCEPTIONS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('exceptions_to_preserve', [])))" 2>/dev/null || echo '[]')
fi

# 1. rbac_policy.yaml exists and is valid YAML
check "python3 -c \"
import yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
assert isinstance(policy, dict), 'Policy must be a dict'
assert 'roles' in policy, 'Missing roles key'
print('YAML_VALID')
\"" "invalid_policy_yaml"

# 2. All roles still present
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
with open('$EXPECTED_JSON') as f:
    expected = json.load(f)
roles_in_policy = set(policy.get('roles', {}).keys())
for role in expected.get('roles', []):
    assert role in roles_in_policy, f'Role {role} was removed'
print('ALL_ROLES_PRESENT')
\"" "roles_removed"

# 3. All 4 violations are fixed
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
violations = json.loads('$VIOLATIONS'.replace(\"'\", '\"'))
for v in violations:
    role_cfg = policy.get('roles', {}).get(v['role'], {})
    perms = role_cfg.get('resources', {}).get(v['resource'], [])
    assert v['permission'] not in perms, f'Violation not fixed: {v[\"role\"]}/{v[\"resource\"]}/{v[\"permission\"]}'
print('ALL_VIOLATIONS_FIXED')
\"" "violations_not_fixed"

# 4. Both exceptions are preserved
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
exceptions = json.loads('$EXCEPTIONS'.replace(\"'\", '\"'))
for e in exceptions:
    role_cfg = policy.get('roles', {}).get(e['role'], {})
    perms = role_cfg.get('resources', {}).get(e['resource'], [])
    assert e['permission'] in perms, f'Exception broken: {e[\"role\"]}/{e[\"resource\"]}/{e[\"permission\"]}'
print('EXCEPTIONS_PRESERVED')
\"" "exceptions_broken"

# 5. Violation 1 specifically fixed
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
v = json.loads('$VIOLATIONS'.replace(\"'\", '\"'))[0]
perms = policy.get('roles',{}).get(v['role'],{}).get('resources',{}).get(v['resource'],[])
assert v['permission'] not in perms, f'Violation 1 not fixed'
print('V1_FIXED')
\"" "violation_1_not_fixed"

# 6. Violation 2 specifically fixed
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
v = json.loads('$VIOLATIONS'.replace(\"'\", '\"'))[1]
perms = policy.get('roles',{}).get(v['role'],{}).get('resources',{}).get(v['resource'],[])
assert v['permission'] not in perms, f'Violation 2 not fixed'
print('V2_FIXED')
\"" "violation_2_not_fixed"

# 7. Violation 3 specifically fixed
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
v = json.loads('$VIOLATIONS'.replace(\"'\", '\"'))[2]
perms = policy.get('roles',{}).get(v['role'],{}).get('resources',{}).get(v['resource'],[])
assert v['permission'] not in perms, f'Violation 3 not fixed'
print('V3_FIXED')
\"" "violation_3_not_fixed"

# 8. Violation 4 specifically fixed
check "python3 -c \"
import json, yaml
with open('rbac_policy.yaml') as f:
    policy = yaml.safe_load(f)
v = json.loads('$VIOLATIONS'.replace(\"'\", '\"'))[3]
perms = policy.get('roles',{}).get(v['role'],{}).get('resources',{}).get(v['resource'],[])
assert v['permission'] not in perms, f'Violation 4 not fixed'
print('V4_FIXED')
\"" "violation_4_not_fixed"

# 9. test_rbac.py passes
check "python3 -m pytest test_rbac.py -q 2>/dev/null || python3 -m unittest test_rbac 2>/dev/null" \
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
