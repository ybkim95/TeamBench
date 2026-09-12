#!/usr/bin/env bash
# CROSS3 grader: verify all 4 translation bugs and 2 error mapping bugs are fixed
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
# C2: test_translation.py passes (all 4 type fixes)
# -------------------------------------------------------------------
if python -m pytest tests/test_translation.py -q --tb=no 2>/dev/null; then
    check "C2" "test_translation.py passes (all 4 type conversion tests)" "pass"
else
    check "C2" "test_translation.py has failures (type conversion bugs remain)" "fail"
fi

# -------------------------------------------------------------------
# C3: test_errors.py passes (HTTP->error code mapping)
# -------------------------------------------------------------------
if python -m pytest tests/test_errors.py -q --tb=no 2>/dev/null; then
    check "C3" "test_errors.py passes (HTTP->error code mapping correct)" "pass"
else
    check "C3" "test_errors.py has failures (error mapping bugs remain)" "fail"
fi

# -------------------------------------------------------------------
# C4: int64 field not truncated (value > 2^32)
# Introspects the message dataclass to find the int64 ID field dynamically.
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, importlib.util, dataclasses

# Load translator
spec = importlib.util.spec_from_file_location("translator", "bridge/translator.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

large_id = 9007199254740993  # > 2^32, fits in int64
# Build a data dict with every STATUS_MAP key as possible status value
# and every conceivable field name for the id field
status_keys = list(mod.STATUS_MAP.keys())
status_val = status_keys[1] if len(status_keys) > 1 else status_keys[0]

# Pass large_id under every plausible id field name so one will match
data = {k: large_id for k in ["record_id", "event_id", "device_id", "asset_id"]}
data.update({k: "test" for k in ["event_type", "reading_type", "media_type", "type_field"]})
data.update({k: "dGVzdA==" for k in ["payload", "raw_bytes", "thumbnail"]})
data.update({k: status_val for k in ["status", "device_status", "publish_status"]})
data.update({k: 0 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})

msg = mod.translate_event(data)

# Find which field holds an int and check it wasn't truncated
found = False
for f in dataclasses.fields(msg):
    val = getattr(msg, f.name)
    if val == large_id:
        found = True
        break
    if isinstance(val, int) and val != 0 and val == large_id & 0xFFFFFFFF:
        raise AssertionError(f"int64 truncated in field {f.name}: got {val}, expected {large_id}")

assert found, f"No field holds large_id={large_id}; fields: {[(f.name, getattr(msg,f.name)) for f in dataclasses.fields(msg)]}"
sys.exit(0)
PYEOF
then
    check "C4" "int64 field not truncated (large values preserved)" "pass"
else
    check "C4" "int64 field still truncated (& 0xFFFFFFFF mask not removed)" "fail"
fi

# -------------------------------------------------------------------
# C5: bytes field is base64-decoded (not raw string)
# Introspects the message to find the bytes payload field dynamically.
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, base64, dataclasses, importlib.util
spec = importlib.util.spec_from_file_location("translator", "bridge/translator.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

raw = b"binary data here"
b64 = base64.b64encode(raw).decode()
status_val = list(mod.STATUS_MAP.keys())[1]

data = {k: 1 for k in ["record_id", "event_id", "device_id", "asset_id"]}
data.update({k: "test" for k in ["event_type", "reading_type", "media_type"]})
data.update({k: b64 for k in ["payload", "raw_bytes", "thumbnail"]})
data.update({k: status_val for k in ["status", "device_status", "publish_status"]})
data.update({k: 0 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})

msg = mod.translate_event(data)

# Find a field that holds bytes and check it decoded correctly
found = False
for f in dataclasses.fields(msg):
    val = getattr(msg, f.name)
    if val == raw:
        found = True
        break
    if isinstance(val, str) and val == b64:
        raise AssertionError(f"field {f.name} is still a base64 string, not decoded bytes")

assert found, f"No field holds decoded bytes {raw!r}; fields: {[(f.name, getattr(msg,f.name)) for f in dataclasses.fields(msg)]}"
sys.exit(0)
PYEOF
then
    check "C5" "bytes field is base64-decoded correctly" "pass"
else
    check "C5" "bytes field not decoded (still string or wrong content)" "fail"
fi

# -------------------------------------------------------------------
# C6: oneof field has exactly one variant set
# Detects the oneof field pair dynamically via validate_oneof().
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, base64, dataclasses, importlib.util
spec = importlib.util.spec_from_file_location("translator", "bridge/translator.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status_val = list(mod.STATUS_MAP.keys())[1]

# Find the text content key name — it's the one in the schema with type str
# that is NOT event_type/reading_type/media_type/type_field.
# Strategy: pass a unique sentinel text under all plausible oneof text keys.
sentinel = "ONEOF_SENTINEL_TEXT_12345"
data = {k: 1 for k in ["record_id", "event_id", "device_id", "asset_id"]}
data.update({k: "test_type" for k in ["event_type", "reading_type", "media_type"]})
data.update({k: "dGVzdA==" for k in ["payload", "raw_bytes", "thumbnail"]})
data.update({k: status_val for k in ["status", "device_status", "publish_status"]})
data.update({k: 0 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})
# Set all plausible text-content oneof keys to sentinel
for k in ["text_content", "label", "caption"]:
    data[k] = sentinel

msg = mod.translate_event(data)

# Find fields that hold the sentinel string or non-empty bytes (potential oneof violation)
truthy_fields = []
for f in dataclasses.fields(msg):
    val = getattr(msg, f.name)
    if val == sentinel or (isinstance(val, bytes) and val and val != b"dGVzdA=="):
        truthy_fields.append((f.name, val))

# The oneof is violated if more than one content field is truthy simultaneously
# Use validate_oneof if available
try:
    msg.validate_oneof()
except ValueError as e:
    raise AssertionError(f"validate_oneof raised: {e}")

# Also test with neither content key present — should not set both fields truthy
data2 = {k: 1 for k in ["record_id", "event_id", "device_id", "asset_id"]}
data2.update({k: "test_type" for k in ["event_type", "reading_type", "media_type"]})
data2.update({k: "dGVzdA==" for k in ["payload", "raw_bytes", "thumbnail"]})
data2.update({k: status_val for k in ["status", "device_status", "publish_status"]})
data2.update({k: 0 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})
msg2 = mod.translate_event(data2)
try:
    msg2.validate_oneof()
except ValueError as e:
    raise AssertionError(f"validate_oneof on empty input raised: {e}")

sys.exit(0)
PYEOF
then
    check "C6" "oneof field has at most one variant set" "pass"
else
    check "C6" "oneof violation: multiple variants set simultaneously" "fail"
fi

# -------------------------------------------------------------------
# C7: enum string mapped to integer
# Uses STATUS_MAP from translator to build test cases dynamically.
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, dataclasses, importlib.util
spec = importlib.util.spec_from_file_location("translator", "bridge/translator.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

tests = list(mod.STATUS_MAP.items())  # [("STATUS_ACTIVE", 1), ...]

# Detect the status field name: probe with a non-zero status and find which
# field name contains "status" and holds an int after translation.
probe_str, probe_int = [(s, i) for s, i in tests if i != 0][0]
probe_data = {k: 1 for k in ["record_id", "event_id", "device_id", "asset_id"]}
probe_data.update({k: "test" for k in ["event_type", "reading_type", "media_type"]})
probe_data.update({k: "dGVzdA==" for k in ["payload", "raw_bytes", "thumbnail"]})
probe_data.update({k: probe_str for k in ["status", "device_status", "publish_status"]})
probe_data.update({k: 999 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})
probe_msg = mod.translate_event(probe_data)
# The status field is the one that holds probe_int (not 1 from IDs, not 999 from timestamps)
status_field = None
for f in dataclasses.fields(probe_msg):
    val = getattr(probe_msg, f.name)
    if isinstance(val, int) and val == probe_int and "status" in f.name.lower():
        status_field = f.name
        break
assert status_field is not None, \
    f"Could not detect status field; fields: {[(f.name, getattr(probe_msg,f.name)) for f in dataclasses.fields(probe_msg)]}"

for status_str, expected_int in tests:
    data = {k: 1 for k in ["record_id", "event_id", "device_id", "asset_id"]}
    data.update({k: "test" for k in ["event_type", "reading_type", "media_type"]})
    data.update({k: "dGVzdA==" for k in ["payload", "raw_bytes", "thumbnail"]})
    data.update({k: status_str for k in ["status", "device_status", "publish_status"]})
    data.update({k: 999 for k in ["timestamp", "occurred_at", "sampled_at", "created_at"]})
    msg = mod.translate_event(data)
    val = getattr(msg, status_field)
    if val == status_str:
        raise AssertionError(f"field {status_field} still holds string {status_str!r}, not mapped to int")
    assert isinstance(val, int), \
        f"{status_field} must be int for {status_str}, got {type(val)}: {val!r}"
    assert val == expected_int, \
        f"{status_str} -> field {status_field}: expected {expected_int}, got {val}"
sys.exit(0)
PYEOF
then
    check "C7" "enum strings correctly mapped to integer values" "pass"
else
    check "C7" "enum not mapped: status still a string or wrong integer" "fail"
fi

# -------------------------------------------------------------------
# C8: HTTP 404 maps to NOT_FOUND (code 5, not 3)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, importlib.util
spec = importlib.util.spec_from_file_location("error_mapper", "bridge/error_mapper.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

result = mod.map_http_error(404, "not found")
NOT_FOUND = 5
assert result.code == NOT_FOUND, f"HTTP 404 must map to NOT_FOUND (5), got code={result.code}"
sys.exit(0)
PYEOF
then
    check "C8" "HTTP 404 maps to NOT_FOUND (code 5)" "pass"
else
    check "C8" "HTTP 404 still maps to wrong error code (should be NOT_FOUND=5)" "fail"
fi

# -------------------------------------------------------------------
# C9: HTTP 429 maps to RESOURCE_EXHAUSTED (code 8, not 13)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, importlib.util
spec = importlib.util.spec_from_file_location("error_mapper", "bridge/error_mapper.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

result = mod.map_http_error(429, "rate limited")
RESOURCE_EXHAUSTED = 8
assert result.code == RESOURCE_EXHAUSTED, \
    f"HTTP 429 must map to RESOURCE_EXHAUSTED (8), got code={result.code}"
sys.exit(0)
PYEOF
then
    check "C9" "HTTP 429 maps to RESOURCE_EXHAUSTED (code 8)" "pass"
else
    check "C9" "HTTP 429 still maps to wrong error code (should be RESOURCE_EXHAUSTED=8)" "fail"
fi

# -------------------------------------------------------------------
# C10: Syntax validity (both modified files parse without error)
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['bridge/translator.py', 'bridge/error_mapper.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'Syntax error in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C10" "bridge/translator.py and bridge/error_mapper.py parse without syntax errors" "pass"
else
    check "C10" "Syntax error in translator.py or error_mapper.py" "fail"
fi

# -------------------------------------------------------------------
# Collect pytest counts (informational)
# -------------------------------------------------------------------
pytest_out=$(python -m pytest tests/ -q --tb=no 2>&1 || true)
pytest_pass=$(echo "$pytest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
pytest_fail=$(echo "$pytest_out" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
