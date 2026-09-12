#!/usr/bin/env bash
# PIPE3 grader: verify all 3 serialization mismatch bugs are fixed
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
# C2: Bug 1 — datetime serialization uses ISO 8601 (T separator)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json
sys.path.insert(0, ".")
from datetime import datetime

# Import the serialize function dynamically
import importlib
producer = importlib.import_module("producer")

# Find the event class
models = importlib.import_module("models")
import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and name != "object" and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break
assert event_cls, "No dataclass event found in models"

# Find the timestamp field
ts_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname
        break
assert ts_field, "No datetime field found"

# Create test event
fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "test-001"
    else:
        fields[fname] = "test"
event = event_cls(**fields)

serialized = producer.serialize_event(event)
data = json.loads(serialized)
ts = data[ts_field]
assert "T" in ts, f"Timestamp must have ISO 8601 T separator, got: {ts!r}"
sys.exit(0)
PYEOF
then
    check "C2" "Datetime uses ISO 8601 format (T separator)" "pass"
else
    check "C2" "Datetime still uses space-separated format (default=str)" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 1 — processor can parse producer output
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json
sys.path.insert(0, ".")
from datetime import datetime
import importlib

producer = importlib.import_module("producer")
processor = importlib.import_module("processor")
models = importlib.import_module("models")

import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break

ts_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname
        break

fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "test-001"
    else:
        fields[fname] = "test"
event = event_cls(**fields)

serialized = producer.serialize_event(event)
data = json.loads(serialized)
# parse_timestamp must not raise
parsed = processor.parse_timestamp(data[ts_field])
assert isinstance(parsed, datetime)
sys.exit(0)
PYEOF
then
    check "C3" "Processor can parse producer datetime output" "pass"
else
    check "C3" "Processor fails to parse producer datetime (fromisoformat error)" "fail"
fi

# -------------------------------------------------------------------
# C4: Bug 2 — processor output is bare objects (no envelope)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json, tempfile, os
sys.path.insert(0, ".")
from datetime import datetime
import importlib

producer = importlib.import_module("producer")
processor = importlib.import_module("processor")
models = importlib.import_module("models")

import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break

ts_field = None
id_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname
    if "id" in fname:
        id_field = fname

fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "test-001"
    else:
        fields[fname] = "test"
event = event_cls(**fields)

with tempfile.TemporaryDirectory() as tmp:
    prod_path = os.path.join(tmp, "produced.jsonl")
    proc_path = os.path.join(tmp, "processed.jsonl")
    producer.produce_events([event], prod_path)
    processor.process_events(prod_path, proc_path)

    with open(proc_path, "r", encoding="utf-8") as f:
        line = f.readline().strip()
    data = json.loads(line)
    # Must be bare object with id_field at top level
    assert id_field in data, (
        f"Processed output must be bare object with '{id_field}' at top level, "
        f"got keys: {list(data.keys())}"
    )
    assert "data" not in data or isinstance(data.get("data"), str), (
        f"Output still wrapped in envelope: {list(data.keys())}"
    )
sys.exit(0)
PYEOF
then
    check "C4" "Processor output is bare objects (no envelope)" "pass"
else
    check "C4" "Processor output still wrapped in {data: ...} envelope" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 3 — processor writes UTF-8 (not latin-1)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, json, tempfile, os
sys.path.insert(0, ".")
from datetime import datetime
import importlib

producer = importlib.import_module("producer")
processor = importlib.import_module("processor")
models = importlib.import_module("models")

import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break

ts_field = None
user_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname
    elif "name" in fname or "user" in fname or "holder" in fname or "sensor" in fname:
        user_field = fname

fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "test-001"
    elif fname == user_field:
        fields[fname] = "M\u00fcller"  # Non-ASCII
    else:
        fields[fname] = "test"
event = event_cls(**fields)

with tempfile.TemporaryDirectory() as tmp:
    prod_path = os.path.join(tmp, "produced.jsonl")
    proc_path = os.path.join(tmp, "processed.jsonl")
    producer.produce_events([event], prod_path)
    processor.process_events(prod_path, proc_path)

    # Reading as UTF-8 must not raise
    with open(proc_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "M\u00fcller" in content, f"Non-ASCII content lost: {content!r}"
sys.exit(0)
PYEOF
then
    check "C5" "Processor writes UTF-8 (non-ASCII preserved)" "pass"
else
    check "C5" "Processor still writes latin-1 (UnicodeDecodeError on read)" "fail"
fi

# -------------------------------------------------------------------
# C6: Full pipeline (produce -> process -> sink) works end-to-end
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, tempfile, os
sys.path.insert(0, ".")
from datetime import datetime
import importlib

producer = importlib.import_module("producer")
processor = importlib.import_module("processor")
sink = importlib.import_module("sink")
models = importlib.import_module("models")

import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break

ts_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname

fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "evt-001"
    else:
        fields[fname] = "test"

events = [event_cls(**fields)]

with tempfile.TemporaryDirectory() as tmp:
    prod_path = os.path.join(tmp, "produced.jsonl")
    proc_path = os.path.join(tmp, "processed.jsonl")
    producer.produce_events(events, prod_path)
    processor.process_events(prod_path, proc_path)
    loaded = sink.load_processed_events(proc_path)
    assert len(loaded) == 1, f"Expected 1 event, got {len(loaded)}"
sys.exit(0)
PYEOF
then
    check "C6" "Full pipeline (produce->process->sink) works end-to-end" "pass"
else
    check "C6" "Full pipeline fails" "fail"
fi

# -------------------------------------------------------------------
# C7: test_pipeline.py passes
# -------------------------------------------------------------------
if python -m pytest tests/test_pipeline.py -q --tb=no 2>/dev/null; then
    check "C7" "test_pipeline.py passes" "pass"
else
    check "C7" "test_pipeline.py has failures" "fail"
fi

# -------------------------------------------------------------------
# C8: test_serialization.py passes
# -------------------------------------------------------------------
if python -m pytest tests/test_serialization.py -q --tb=no 2>/dev/null; then
    check "C8" "test_serialization.py passes" "pass"
else
    check "C8" "test_serialization.py has failures" "fail"
fi

# -------------------------------------------------------------------
# C9: All Python files parse
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['producer.py', 'processor.py', 'sink.py', 'models.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'Syntax error in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C9" "All Python files parse without syntax errors" "pass"
else
    check "C9" "Syntax error in pipeline files" "fail"
fi

# -------------------------------------------------------------------
# C10: Euro sign and special chars survive full pipeline
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, tempfile, os, json
sys.path.insert(0, ".")
from datetime import datetime
import importlib

producer = importlib.import_module("producer")
processor = importlib.import_module("processor")
sink = importlib.import_module("sink")
models = importlib.import_module("models")

import inspect
event_cls = None
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
        event_cls = obj
        break

ts_field = None
value_field = None
for fname, fobj in event_cls.__dataclass_fields__.items():
    if fobj.type == datetime or "datetime" in str(fobj.type):
        ts_field = fname
    elif "url" in fname or "value" in fname or "description" in fname or "location" in fname:
        value_field = fname

fields = {}
for fname in event_cls.__dataclass_fields__:
    if fname == ts_field:
        fields[fname] = datetime(2023, 11, 14, 22, 13, 20)
    elif "id" in fname:
        fields[fname] = "evt-001"
    elif fname == value_field:
        fields[fname] = "Price: \u20ac99.99"
    else:
        fields[fname] = "test"

events = [event_cls(**fields)]

with tempfile.TemporaryDirectory() as tmp:
    prod_path = os.path.join(tmp, "produced.jsonl")
    proc_path = os.path.join(tmp, "processed.jsonl")
    producer.produce_events(events, prod_path)
    processor.process_events(prod_path, proc_path)
    loaded = sink.load_processed_events(proc_path)
    assert "\u20ac" in loaded[0][value_field], f"Euro sign lost: {loaded[0][value_field]!r}"
sys.exit(0)
PYEOF
then
    check "C10" "Special characters (euro sign) survive full pipeline" "pass"
else
    check "C10" "Special characters lost in pipeline (encoding issue)" "fail"
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
