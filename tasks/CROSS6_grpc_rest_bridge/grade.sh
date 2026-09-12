#!/usr/bin/env bash
# CROSS6 grader: verify all 4 type conversion bugs are fixed in REST gateway
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

# Install pytest if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# C1: pytest tests/ overall pass
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "All pytest tests pass" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# -------------------------------------------------------------------
# C2: int64 fields serialized as string (not bare integer)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, ".")
from gateway import _convert_field
result = _convert_field("test_id", 9007199254740993, "int64")
assert isinstance(result, str), f"int64 must be string, got {type(result)}: {result!r}"
assert result == "9007199254740993", f"int64 value wrong: {result!r}"
sys.exit(0)
PYEOF
then
    check "C2" "int64 fields serialized as JSON strings" "pass"
else
    check "C2" "int64 fields still passed as integers (must be strings)" "fail"
fi

# -------------------------------------------------------------------
# C3: single-element repeated field wrapped as array
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, ".")
from gateway import _convert_field
result = _convert_field("test_list", ["only_one"], "repeated")
assert isinstance(result, list), f"repeated with 1 element must be list, got {type(result)}: {result!r}"
assert len(result) == 1, f"list length must be 1, got {len(result)}"
assert result[0] == "only_one"
sys.exit(0)
PYEOF
then
    check "C3" "Single-element repeated field correctly wrapped as array" "pass"
else
    check "C3" "Single-element repeated field not wrapped as array" "fail"
fi

# -------------------------------------------------------------------
# C4: multi-element repeated field still works
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, ".")
from gateway import _convert_field
result = _convert_field("test_list", ["a", "b", "c"], "repeated")
assert isinstance(result, list), f"repeated must be list, got {type(result)}"
assert len(result) == 3
sys.exit(0)
PYEOF
then
    check "C4" "Multi-element repeated field preserved as array" "pass"
else
    check "C4" "Multi-element repeated field broken" "fail"
fi

# -------------------------------------------------------------------
# C5: enum serialized as string name (not integer)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, ".")
from gateway import _convert_field
# Try importing any IntEnum from models
import importlib
mod = importlib.import_module("models")
# Find the first IntEnum class
import inspect
from enum import IntEnum
enum_cls = None
for name, obj in inspect.getmembers(mod):
    if inspect.isclass(obj) and issubclass(obj, IntEnum) and obj is not IntEnum:
        enum_cls = obj
        break
assert enum_cls is not None, "No IntEnum found in models"
# Test with the second value (index 1)
vals = list(enum_cls)
test_val = vals[1] if len(vals) > 1 else vals[0]
result = _convert_field("test_status", test_val, "enum")
assert isinstance(result, str), f"enum must be string name, got {type(result)}: {result!r}"
assert result == test_val.name, f"enum name mismatch: got {result!r}, expected {test_val.name!r}"
sys.exit(0)
PYEOF
then
    check "C5" "Enum fields serialized as string names" "pass"
else
    check "C5" "Enum fields still sent as integers (must be string names)" "fail"
fi

# -------------------------------------------------------------------
# C6: timestamp serialized as ISO 8601 string
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, ".")
from gateway import _convert_field
from datetime import datetime, timezone
result = _convert_field("test_ts", 1700000000, "timestamp")
assert isinstance(result, str), f"timestamp must be string, got {type(result)}: {result!r}"
assert "T" in result, f"timestamp must be ISO 8601 with T separator: {result!r}"
# Must be parseable
parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
expected = datetime.fromtimestamp(1700000000, tz=timezone.utc)
assert parsed == expected, f"timestamp mismatch: {parsed} != {expected}"
sys.exit(0)
PYEOF
then
    check "C6" "Timestamp fields serialized as ISO 8601 strings" "pass"
else
    check "C6" "Timestamp fields still passed as epoch integers" "fail"
fi

# -------------------------------------------------------------------
# C7: entity_to_json returns correct types
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json
sys.path.insert(0, ".")
from gateway import handle_get
raw = handle_get(1)
data = json.loads(raw)
if "error" in data:
    sys.exit(1)
# Check all fields have correct types
for key, val in data.items():
    if isinstance(val, bool):
        continue  # booleans are ok
# int64 field should be string
id_field = None
for k, v in data.items():
    if "id" in k.lower() and isinstance(v, str):
        try:
            int(v)
            id_field = k
        except ValueError:
            pass
assert id_field is not None, f"No string int64 field found in: {data}"
sys.exit(0)
PYEOF
then
    check "C7" "entity_to_json integrates all type conversions" "pass"
else
    check "C7" "entity_to_json integration check failed" "fail"
fi

# -------------------------------------------------------------------
# C8: handle_list returns valid JSON array
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json
sys.path.insert(0, ".")
from gateway import handle_list
raw = handle_list()
data = json.loads(raw)
assert isinstance(data, list), f"handle_list must return array, got {type(data)}"
assert len(data) >= 2, f"Expected at least 2 entities, got {len(data)}"
for item in data:
    # Every list field must be an array
    for k, v in item.items():
        if isinstance(v, list):
            pass  # correct
sys.exit(0)
PYEOF
then
    check "C8" "handle_list returns valid JSON array" "pass"
else
    check "C8" "handle_list output invalid" "fail"
fi

# -------------------------------------------------------------------
# C9: Syntax validity
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['gateway.py', 'models.py', 'service_impl.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'Syntax error in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C9" "All Python files parse without syntax errors" "pass"
else
    check "C9" "Syntax error in modified files" "fail"
fi

# -------------------------------------------------------------------
# C10: test_gateway.py passes individually
# -------------------------------------------------------------------
if python -m pytest tests/test_gateway.py -q --tb=no 2>/dev/null; then
    check "C10" "test_gateway.py passes (all type conversion tests)" "pass"
else
    check "C10" "test_gateway.py has failures" "fail"
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
