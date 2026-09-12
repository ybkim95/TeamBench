#!/usr/bin/env bash
# TRAP2 grader: verify genuine bugs fixed and false issues preserved
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=8
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
# Detect seed-parameterised names from processor.py source
# -------------------------------------------------------------------
PROC_CLASS=$(python3 -c "
import ast, sys
src = open('lib/processor.py').read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(node.name)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null || echo "DataProcessor")

TS_FIELD=$(python3 -c "
import ast, sys
src = open('lib/processor.py').read()
# Find the lambda key inside process() — key=lambda r: r[\"<field>\"]
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'process':
        for child in ast.walk(node):
            if isinstance(child, ast.Subscript):
                if isinstance(child.slice, ast.Constant):
                    print(child.slice.value)
                    sys.exit(0)
sys.exit(1)
" 2>/dev/null || echo "timestamp")

SORTER_CLASS=$(python3 -c "
import ast, sys
src = open('lib/sorter.py').read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(node.name)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null || echo "Sorter")

CACHE_CLASS=$(python3 -c "
import ast, sys
src = open('lib/cache.py').read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(node.name)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null || echo "DataCache")

READER_CLASS=$(python3 -c "
import ast, sys
src = open('lib/reader.py').read()
tree = ast.parse(src)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        print(node.name)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null || echo "BatchReader")

# -------------------------------------------------------------------
# Issue 1: Off-by-one in pagination (processor.py)
# page=1 must return items [0:page_size], not [page_size:2*page_size]
# -------------------------------------------------------------------
if python3 - "$PROC_CLASS" "$TS_FIELD" <<'PYEOF' 2>/dev/null
import importlib.util, sys
proc_cls_name = sys.argv[1]
ts_field = sys.argv[2]
spec = importlib.util.spec_from_file_location("processor", "lib/processor.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
proc = getattr(mod, proc_cls_name)()
records = [{"id": i, ts_field: i, "value": i} for i in range(10)]
result = proc.paginate(records, page=1, page_size=3)
assert result == records[0:3], f"page=1 got {result}"
result2 = proc.paginate(records, page=2, page_size=3)
assert result2 == records[3:6], f"page=2 got {result2}"
sys.exit(0)
PYEOF
then
    check "I1" "Issue 1 fixed: pagination off-by-one corrected" "pass"
else
    check "I1" "Issue 1 not fixed: pagination still returns wrong page" "fail"
fi

# -------------------------------------------------------------------
# Issue 2: Missing null check on empty input (processor.py)
# -------------------------------------------------------------------
if python3 - "$PROC_CLASS" <<'PYEOF' 2>/dev/null
import importlib.util, sys
proc_cls_name = sys.argv[1]
spec = importlib.util.spec_from_file_location("processor", "lib/processor.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
proc = getattr(mod, proc_cls_name)()
try:
    result = proc.process([])
    sys.exit(0)
except (IndexError, KeyError, TypeError, AttributeError):
    sys.exit(1)
PYEOF
then
    check "I2" "Issue 2 fixed: empty input handled without crash" "pass"
else
    check "I2" "Issue 2 not fixed: empty input still crashes" "fail"
fi

# -------------------------------------------------------------------
# Issue 3: Wrong sort order — must be descending by ts_field (processor.py)
# -------------------------------------------------------------------
if python3 - "$PROC_CLASS" "$TS_FIELD" <<'PYEOF' 2>/dev/null
import importlib.util, sys
proc_cls_name = sys.argv[1]
ts_field = sys.argv[2]
spec = importlib.util.spec_from_file_location("processor", "lib/processor.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
proc = getattr(mod, proc_cls_name)()
records = [{"id": i, ts_field: v, "value": v} for i, v in enumerate([3, 1, 5, 2])]
result = proc.process(records)
ts_vals = [r[ts_field] for r in result]
assert ts_vals == sorted(ts_vals, reverse=True), f"not descending: {ts_vals}"
sys.exit(0)
PYEOF
then
    check "I3" "Issue 3 fixed: sort order is descending by timestamp field" "pass"
else
    check "I3" "Issue 3 not fixed: sort order still wrong" "fail"
fi

# -------------------------------------------------------------------
# Issue 4: Date format mismatch in sorter.py (%d/%m/%Y -> %Y-%m-%d)
# -------------------------------------------------------------------
if python3 - "$SORTER_CLASS" <<'PYEOF' 2>/dev/null
import importlib.util, sys
sorter_cls_name = sys.argv[1]
spec = importlib.util.spec_from_file_location("sorter", "lib/sorter.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
s = getattr(mod, sorter_cls_name)()
d = s.parse_date("2024-01-15")
assert d.year == 2024 and d.month == 1 and d.day == 15, f"wrong parse: {d}"
sys.exit(0)
PYEOF
then
    check "I4" "Issue 4 fixed: date format string corrected to %Y-%m-%d" "pass"
else
    check "I4" "Issue 4 not fixed: date parsing still uses wrong format" "fail"
fi

# -------------------------------------------------------------------
# Issue 5: Unclosed file handle in sorter.py load_data()
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('lib/sorter.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'load_data':
        src_func = ast.unparse(node)
        has_with = 'with open' in src_func
        has_close = '.close()' in src_func
        if has_with or has_close:
            sys.exit(0)
        else:
            sys.exit(1)
sys.exit(1)
PYEOF
then
    check "I5" "Issue 5 fixed: file handle closed in load_data()" "pass"
else
    check "I5" "Issue 5 not fixed: file handle still unclosed in load_data()" "fail"
fi

# -------------------------------------------------------------------
# Issue 6 (FALSE): cache.py double invalidation must be PRESERVED
# invalidate_on_write() must call both clear() and rebuild_index()
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('lib/cache.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'invalidate_on_write':
        src_func = ast.unparse(node)
        has_clear = 'clear()' in src_func or 'self.clear()' in src_func
        has_rebuild = 'rebuild_index()' in src_func or 'self.rebuild_index()' in src_func
        if has_clear and has_rebuild:
            sys.exit(0)
        sys.exit(1)
sys.exit(1)
PYEOF
then
    check "I6" "Issue 6 preserved: double invalidation (clear+rebuild) intact" "pass"
else
    check "I6" "Issue 6 incorrectly changed: double invalidation removed from cache.py" "fail"
fi

# -------------------------------------------------------------------
# Issue 7 (FALSE): sorter.py stable_sort() must still use insertion sort
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('lib/sorter.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'stable_sort':
        # Skip the docstring (first Expr(Constant(...)) statement) when scanning
        body_stmts = node.body
        if (body_stmts and isinstance(body_stmts[0], ast.Expr)
                and isinstance(body_stmts[0].value, ast.Constant)):
            body_stmts = body_stmts[1:]
        body_src = ast.unparse(ast.Module(body=body_stmts, type_ignores=[]))

        forbidden = ['sorted(', '.sort(', 'heapq', 'merge_sort', 'quick_sort', 'timsort']
        for f in forbidden:
            if f in body_src:
                sys.exit(1)

        # Must have insertion-sort inner loop: while with j index manipulation
        has_loop = ('for ' in body_src and
                    ('while ' in body_src or 'j - 1' in body_src or
                     'j-1' in body_src or 'j >= ' in body_src or 'j > ' in body_src))
        if has_loop:
            sys.exit(0)
        sys.exit(1)
sys.exit(1)
PYEOF
then
    check "I7" "Issue 7 preserved: stable_sort() still uses insertion sort" "pass"
else
    check "I7" "Issue 7 incorrectly changed: sort algorithm replaced in sorter.py" "fail"
fi

# -------------------------------------------------------------------
# Issue 8 (FALSE): reader.py parse_batch() must NOT have try/except
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('lib/reader.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'parse_batch':
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                sys.exit(1)
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "I8" "Issue 8 preserved: parse_batch() has no try/except (intentional propagation)" "pass"
else
    check "I8" "Issue 8 incorrectly changed: try/except added to parse_batch() in reader.py" "fail"
fi

# -------------------------------------------------------------------
# Run pytest (informational counts only)
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
    "issues_correct": $partial,
    "total_issues": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
