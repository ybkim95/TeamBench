#!/usr/bin/env bash
# CROSS5 grader: verify Python producer + Java consumer event schema reconciliation
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

# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# ── C1: Producer uses correct eventId field name ────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open("producer/event_producer.py").read()
# Must use "eventId" (camelCase), not "event_id" (snake_case)
if '"eventId"' in src or "'eventId'" in src:
    # Must NOT still have event_id as a dict key
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == "event_id":
            # Check if it's a dict key assignment
            sys.exit(1)
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C1" "Producer uses 'eventId' field name (not event_id)" "pass"
else
    check "C1" "Producer still uses snake_case 'event_id'" "fail"
fi

# ── C2: Producer uses correct timestamp field name ──────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("producer/event_producer.py").read()
# Must use "timestamp" not "created_at"
if ('"timestamp"' in src or "'timestamp'" in src):
    if '"created_at"' not in src and "'created_at'" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C2" "Producer uses 'timestamp' field name (not created_at)" "pass"
else
    check "C2" "Producer still uses 'created_at' field name" "fail"
fi

# ── C3: Producer uses correct payload field name ────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("producer/event_producer.py").read()
# Must use "payload" not "data"
if ('"payload"' in src or "'payload'" in src):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "Producer uses 'payload' field name (not data)" "pass"
else
    check "C3" "Producer still uses 'data' field name" "fail"
fi

# ── C4: Producer uses correct sourceService field name ──────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("producer/event_producer.py").read()
if ('"sourceService"' in src or "'sourceService'" in src):
    if '"source_service"' not in src and "'source_service'" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C4" "Producer uses 'sourceService' field name (not source_service)" "pass"
else
    check "C4" "Producer still uses snake_case 'source_service'" "fail"
fi

# ── C5: Producer uses correct correlationId field name ──────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("producer/event_producer.py").read()
if ('"correlationId"' in src or "'correlationId'" in src):
    if '"correlation_id"' not in src and "'correlation_id'" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "Producer uses 'correlationId' field name (not correlation_id)" "pass"
else
    check "C5" "Producer still uses snake_case 'correlation_id'" "fail"
fi

# ── C6: Producer sends epoch milliseconds (not ISO-8601) ────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, ast
src = open("producer/event_producer.py").read()
# Should contain time() * 1000 or similar epoch ms conversion
# Should NOT contain isoformat() or strftime for the timestamp field
if "isoformat()" in src:
    sys.exit(1)
# Look for epoch conversion patterns
if "* 1000" in src or "*1000" in src or "int(time" in src or "int(datetime" in src:
    sys.exit(0)
# Also accept calendar.timegm or time.mktime patterns
if "timegm" in src or "mktime" in src or "timestamp()" in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C6" "Producer sends epoch milliseconds (not ISO-8601 strings)" "pass"
else
    check "C6" "Producer still sends ISO-8601 timestamp strings" "fail"
fi

# ── C7: Consumer base64-decodes binary payloads (not hex) ───────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("consumer/src/main/java/EventConsumer.java").read()
# Should use Base64 decoder, not hex decoding
if "Base64" in src:
    # Should NOT have hex decode pattern
    if "Hex.decode" not in src and "hexStringToByteArray" not in src and "DatatypeConverter.parseHexBinary" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "Consumer uses Base64 decoding (not hex decoding)" "pass"
else
    check "C7" "Consumer still uses hex decoding for binary payloads" "fail"
fi

# ── C8: event_schema.json is unchanged ──────────────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import json, hashlib, sys, os
# Verify schema wasn't modified by checking it still has required fields
schema = json.load(open("schema/event_schema.json"))
required_fields = {"eventId", "timestamp", "payload", "sourceService", "correlationId"}
props = set(schema.get("properties", {}).keys())
if required_fields.issubset(props):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C8" "event_schema.json is unchanged and valid" "pass"
else
    check "C8" "event_schema.json was modified or is invalid" "fail"
fi

# ── C9: Producer Python file has valid syntax ───────────────────────────
if python3 -c "import ast; ast.parse(open('producer/event_producer.py').read())" 2>/dev/null; then
    check "C9" "Producer Python file has valid syntax" "pass"
else
    check "C9" "Producer Python file has syntax errors" "fail"
fi

# ── C10: Consumer Java file has valid syntax (basic check) ──────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("consumer/src/main/java/EventConsumer.java").read()
# Basic Java syntax checks: matching braces, has class definition
if "class EventConsumer" in src:
    opens = src.count("{")
    closes = src.count("}")
    if opens == closes and opens > 0:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C10" "Consumer Java file has valid structure" "pass"
else
    check "C10" "Consumer Java file has structural issues" "fail"
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

# hermetic-by: scripts/make_graders_hermetic.py
