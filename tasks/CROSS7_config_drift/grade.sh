#!/usr/bin/env bash
# CROSS7 grader: verify all 4 config reconciliation bugs are fixed
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

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

# Install dependencies
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest pyyaml || true

# -------------------------------------------------------------------
# C1: pytest tests/ overall pass
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "All pytest tests pass" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# -------------------------------------------------------------------
# C2: Bug 1 — override check is per-service (not global)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, yaml, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service, SERVICES

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))

# Find a service that has changed fields NOT in its overrides
# These should revert to canonical
for svc in SERVICES:
    svc_config = load_yaml(os.path.join(base_dir, svc, "config.yaml"))
    svc_overrides = overrides.get(svc, {})
    keep_changed = svc_overrides.get("keep_changed", [])
    result = reconcile_service(canonical, svc_config, svc, overrides)
    for key, val in canonical.items():
        if key in svc_config and svc_config[key] != val:
            if key not in keep_changed:
                # This drift should be reverted
                if isinstance(val, bool):
                    ok = result[key] is val
                else:
                    ok = result[key] == val
                assert ok, (
                    f"{svc}: {key} should be reverted to canonical {val!r}, "
                    f"got {result[key]!r}"
                )
sys.exit(0)
PYEOF
then
    check "C2" "Override check is per-service (non-overridden drifts reverted)" "pass"
else
    check "C2" "Override check is still global (other service overrides leak)" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 2 — service-specific added fields are preserved
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service, SERVICES

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))

for svc in SERVICES:
    svc_config = load_yaml(os.path.join(base_dir, svc, "config.yaml"))
    svc_overrides = overrides.get(svc, {})
    keep_added = svc_overrides.get("keep_added", [])
    if not keep_added:
        continue
    result = reconcile_service(canonical, svc_config, svc, overrides)
    for field in keep_added:
        assert field in result, (
            f"{svc}: added field {field!r} should be preserved, but was deleted"
        )
sys.exit(0)
PYEOF
then
    check "C3" "Service-specific added fields preserved" "pass"
else
    check "C3" "Service-specific added fields incorrectly deleted" "fail"
fi

# -------------------------------------------------------------------
# C4: Bug 3 — deprecated fields not re-added
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service, SERVICES

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))
deprecated = overrides.get("deprecated", [])

for svc in SERVICES:
    svc_config = load_yaml(os.path.join(base_dir, svc, "config.yaml"))
    # Check if this service removed deprecated fields
    for field in deprecated:
        if field not in svc_config:
            result = reconcile_service(canonical, svc_config, svc, overrides)
            assert field not in result, (
                f"{svc}: deprecated field {field!r} was re-added from canonical"
            )
sys.exit(0)
PYEOF
then
    check "C4" "Deprecated fields not re-added to services that removed them" "pass"
else
    check "C4" "Deprecated fields incorrectly re-added from canonical" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 4 — type normalization (string "true" == bool True)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))

# Simulate a config with string "true" where canonical has bool True
test_config = dict(canonical)
bool_key = None
for k, v in canonical.items():
    if isinstance(v, bool):
        bool_key = k
        break
assert bool_key, "No boolean field in canonical"
test_config[bool_key] = "true" if canonical[bool_key] else "false"

result = reconcile_service(canonical, test_config, "test_svc", overrides)
# After type normalization, value should match canonical
val = result[bool_key]
if isinstance(val, bool):
    assert val == canonical[bool_key]
elif isinstance(val, str):
    assert val.lower() == str(canonical[bool_key]).lower()
else:
    raise AssertionError(f"Unexpected type for {bool_key}: {type(val)}")
sys.exit(0)
PYEOF
then
    check "C5" "Type normalization handles string/bool comparison" "pass"
else
    check "C5" "Type normalization missing (string 'true' != bool True)" "fail"
fi

# -------------------------------------------------------------------
# C6: All service configs have all non-deprecated canonical keys
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service, SERVICES

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))
deprecated = overrides.get("deprecated", [])

for svc in SERVICES:
    svc_config = load_yaml(os.path.join(base_dir, svc, "config.yaml"))
    result = reconcile_service(canonical, svc_config, svc, overrides)
    for key in canonical:
        if key in deprecated and key not in svc_config:
            continue
        assert key in result, f"{svc} missing canonical key: {key}"
sys.exit(0)
PYEOF
then
    check "C6" "All services have all non-deprecated canonical keys" "pass"
else
    check "C6" "Some services missing canonical keys after reconciliation" "fail"
fi

# -------------------------------------------------------------------
# C7: reconcile.py parses without syntax errors
# -------------------------------------------------------------------
if python3 -c "import ast; ast.parse(open('reconcile.py').read())" 2>/dev/null; then
    check "C7" "reconcile.py parses without syntax errors" "pass"
else
    check "C7" "Syntax error in reconcile.py" "fail"
fi

# -------------------------------------------------------------------
# C8: overrides.md parser works correctly
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, ".")
from reconcile import parse_overrides
overrides = parse_overrides("overrides.md")
assert "deprecated" in overrides, "parse_overrides must return deprecated list"
assert len(overrides["deprecated"]) >= 1, "Must detect deprecated fields"
sys.exit(0)
PYEOF
then
    check "C8" "overrides.md parser detects deprecated fields" "pass"
else
    check "C8" "overrides.md parser broken" "fail"
fi

# -------------------------------------------------------------------
# C9: test_reconcile.py passes individually
# -------------------------------------------------------------------
if python -m pytest tests/test_reconcile.py -q --tb=no 2>/dev/null; then
    check "C9" "test_reconcile.py passes" "pass"
else
    check "C9" "test_reconcile.py has failures" "fail"
fi

# -------------------------------------------------------------------
# C10: reconcile produces valid YAML output
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, yaml, os
sys.path.insert(0, ".")
from reconcile import load_yaml, parse_overrides, reconcile_service, SERVICES

base_dir = os.path.dirname(os.path.abspath("reconcile.py"))
canonical = load_yaml(os.path.join(base_dir, "canonical_config.yaml"))
overrides = parse_overrides(os.path.join(base_dir, "overrides.md"))

for svc in SERVICES:
    svc_config = load_yaml(os.path.join(base_dir, svc, "config.yaml"))
    result = reconcile_service(canonical, svc_config, svc, overrides)
    # Must be serializable as YAML
    yaml_str = yaml.dump(result)
    loaded = yaml.safe_load(yaml_str)
    assert loaded == result, f"YAML round-trip failed for {svc}"
sys.exit(0)
PYEOF
then
    check "C10" "Reconciled configs are valid YAML" "pass"
else
    check "C10" "Reconciled output not valid YAML" "fail"
fi

# -------------------------------------------------------------------
# Compute score
# -------------------------------------------------------------------
partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
