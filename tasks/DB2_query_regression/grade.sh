#!/usr/bin/env bash
# DB2_query_regression grader — parse indexes.sql and verify:
#   required indexes created, forbidden indexes absent.
#
# Checks:
#   C1  schema.sql present
#   C2  queries.sql present
#   C3  dba_analysis.md present
#   C4  indexes.sql present (agent must create this)
#   C5  Q1 index exists (large table filter column)
#   C6  Q2 index exists (join FK column)
#   C7  Q3 index exists (timestamp range column)
#   C8  Q4 composite index exists (if needs_q4)
#   C9  Small reference table NOT indexed
#   C10 Summary/aggregation table NOT indexed
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

mkdir -p "${REPORTS}"

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

# ── Load expected values ───────────────────────────────────────────────────────
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
    EXPECTED_JSON="${TASK_DIR}/expected.json"
fi

IDX_Q1=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('idx_q1', 'idx_orders_customer_id'))
" 2>/dev/null || echo "idx_orders_customer_id")

IDX_Q2=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('idx_q2', 'idx_order_items_order_id'))
" 2>/dev/null || echo "idx_order_items_order_id")

IDX_Q3=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('idx_q3', 'idx_order_events_event_at'))
" 2>/dev/null || echo "idx_order_events_event_at")

IDX_Q4=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('idx_q4') or '')
" 2>/dev/null || echo "")

NEEDS_Q4=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print('true' if e.get('needs_q4', False) else 'false')
" 2>/dev/null || echo "false")

SMALL_TABLE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('small_table', 'payment_methods'))
" 2>/dev/null || echo "payment_methods")

SUMMARY_TABLE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('summary_table', 'daily_order_summary'))
" 2>/dev/null || echo "daily_order_summary")

INDEXES_SQL="${WORKSPACE}/indexes.sql"

# ── C1: schema.sql present ────────────────────────────────────────────────────
check "C1" "schema.sql present in workspace" \
    "$([ -f '${WORKSPACE}/schema.sql' ] && echo pass || echo fail)"

# ── C2: queries.sql present ───────────────────────────────────────────────────
check "C2" "queries.sql present in workspace" \
    "$([ -f '${WORKSPACE}/queries.sql' ] && echo pass || echo fail)"

# ── C3: dba_analysis.md present ───────────────────────────────────────────────
check "C3" "dba_analysis.md present in workspace" \
    "$([ -f '${WORKSPACE}/dba_analysis.md' ] && echo pass || echo fail)"

# ── C4: indexes.sql present ───────────────────────────────────────────────────
check "C4" "indexes.sql present (agent must create this file)" \
    "$([ -f '${INDEXES_SQL}' ] && echo pass || echo fail)"

# Helper: check if a CREATE INDEX for a given name exists in indexes.sql
index_exists() {
    local idx_name="$1"
    python3 -c "
import re, sys
idx = '${idx_name}'
if not idx:
    print('pass')
    sys.exit(0)
try:
    content = open('${INDEXES_SQL}').read().lower()
    idx_lower = idx.lower()
    # Match: CREATE INDEX idx_name or CREATE INDEX IF NOT EXISTS idx_name
    pattern = rf'create\s+index\s+(?:if\s+not\s+exists\s+)?{re.escape(idx_lower)}\b'
    print('pass' if re.search(pattern, content) else 'fail')
except FileNotFoundError:
    print('fail')
" 2>/dev/null || echo "fail"
}

# Helper: check that no CREATE INDEX targets a given table
table_not_indexed() {
    local table_name="$1"
    python3 -c "
import re, sys
table = '${table_name}'
try:
    content = open('${INDEXES_SQL}').read().lower()
    table_lower = table.lower()
    # Match: ON table_name (  — the ON clause of CREATE INDEX
    pattern = rf'\bon\s+{re.escape(table_lower)}\s*\('
    print('fail' if re.search(pattern, content) else 'pass')
except FileNotFoundError:
    print('pass')  # file absent — graded by C4
" 2>/dev/null || echo "pass"
}

# ── C5: Q1 index (large table filter column) ──────────────────────────────────
check "C5" "Q1 index '${IDX_Q1}' exists in indexes.sql" "$(index_exists '${IDX_Q1}')"

# ── C6: Q2 index (join FK column) ────────────────────────────────────────────
check "C6" "Q2 index '${IDX_Q2}' exists in indexes.sql" "$(index_exists '${IDX_Q2}')"

# ── C7: Q3 index (timestamp range column) ─────────────────────────────────────
check "C7" "Q3 index '${IDX_Q3}' exists in indexes.sql" "$(index_exists '${IDX_Q3}')"

# ── C8: Q4 composite index (if needs_q4) ──────────────────────────────────────
if [ "${NEEDS_Q4}" = "true" ] && [ -n "${IDX_Q4}" ]; then
    check "C8" "Q4 composite index '${IDX_Q4}' exists in indexes.sql" \
        "$(index_exists '${IDX_Q4}')"
else
    # Not needed for this seed — auto-pass
    partial=$((partial + 1))
    findings="${findings}{\"id\":\"C8\",\"ok\":true,\"note\":\"Q4 composite index not required for this seed (auto-pass)\"},"
fi

# ── C9: Small reference table NOT indexed ─────────────────────────────────────
check "C9" "No index on small table '${SMALL_TABLE}' (seq scan is optimal)" \
    "$(table_not_indexed '${SMALL_TABLE}')"

# ── C10: Summary table NOT indexed ────────────────────────────────────────────
check "C10" "No index on summary table '${SUMMARY_TABLE}' (full scan intentional)" \
    "$(table_not_indexed '${SUMMARY_TABLE}')"

# ── Write score.json ──────────────────────────────────────────────────────────
partial_score=$(python3 -c "print(round(${partial} / ${total}, 2))")
findings="${findings%,}"

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "${pass}" = "true" ] && echo "true" || echo "false" ),
  "primary": {"success": $( [ "${pass}" = "true" ] && echo 1 || echo 0 )},
  "secondary": {
    "partial_score": ${partial_score},
    "checks_passed": ${partial},
    "checks_total": ${total}
  },
  "failure_modes": [],
  "checklist": [${findings}]
}
EOF
