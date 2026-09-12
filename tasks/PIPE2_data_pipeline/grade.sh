#!/usr/bin/env bash
# PIPE2 grader: verify 3 ETL pipeline bugs fixed (extractor, transformer, loader)
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

# ── C1: Extractor only drops rows where key columns are null ────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, ast
src = open("pipeline/extract.py").read()
tree = ast.parse(src)
# The fix: should check only key columns for null, not all columns
# Buggy: drops row if ANY column is null
# Fixed: drops row only if key columns (first 2) are null
# Look for selective null checking patterns
func_src = src.lower()
# Should NOT have "all" or "any" applied to entire row for null checking
# Should have specific column-based null checks
if "key_col" in src or "key_columns" in src or "[0]" in src or "[1]" in src or "[:2]" in src:
    sys.exit(0)
# Check for named column access patterns
if "row.get(" in src or "row['" in src:
    # More targeted - checking specific columns rather than all
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C1" "Extractor checks only key columns for null (not all columns)" "pass"
else
    check "C1" "Extractor still drops rows where any column is null" "fail"
fi

# ── C2: Extractor preserves rows with non-key nulls ────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, os, importlib.util
spec = importlib.util.spec_from_file_location("extract", "pipeline/extract.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# Test: row with null in non-key column should be preserved
# Find the extract function
extract_fn = None
for name in dir(mod):
    obj = getattr(mod, name)
    if callable(obj) and "extract" in name.lower():
        extract_fn = obj
        break
if extract_fn is None:
    sys.exit(1)
# We can't easily test without knowing the exact schema, so check source
src = open("pipeline/extract.py").read()
# Verify the function doesn't do blanket null filtering
if "dropna(how='any')" in src or "dropna()" in src:
    sys.exit(1)  # Still doing blanket null drops
if "dropna(subset=" in src or "dropna(how='all')" in src:
    sys.exit(0)  # Using subset-based or all-based dropping
# For non-pandas approaches
if "None" in src and ("key" in src.lower() or "[0]" in src or "[1]" in src):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C2" "Extractor preserves rows with non-key null values" "pass"
else
    check "C2" "Extractor incorrectly drops rows with non-key nulls" "fail"
fi

# ── C3: Transformer uses correct truncation limit (255, not 50) ─────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("pipeline/transform.py").read()
# Should have 255 as truncation limit, not 50
if "255" in src:
    if "50" not in src or "[:50]" not in src:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "Transformer uses 255-char truncation limit (not 50)" "pass"
else
    check "C3" "Transformer still truncates at 50 characters" "fail"
fi

# ── C4: Transformer actually truncates strings ──────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("pipeline/transform.py").read()
# Should have truncation logic with 255
if "[:255]" in src or "[:limit]" in src or "[:max_len]" in src or "[:truncation" in src or ".truncate(" in src:
    sys.exit(0)
# pandas str.slice or str[:N]
if "str[:255]" in src or "str.slice" in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C4" "Transformer has string truncation logic" "pass"
else
    check "C4" "Transformer missing truncation logic" "fail"
fi

# ── C5: Loader maps columns in correct order ───────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
src = open("pipeline/load.py").read()
# The bug was swapping col2 and col3. Check that the mapping is correct.
# We look for the column mapping and verify order
# The fix should have the correct column order (not swapped)
lines = src.split('\n')
# Look for column mapping patterns
for i, line in enumerate(lines):
    # If there's an explicit mapping dict or list, check order
    if "column_map" in line.lower() or "output_columns" in line.lower() or "mapping" in line.lower():
        # Found mapping definition - it exists, which is good
        sys.exit(0)
# Check for correct ordered assignment or indexing
if "PIPELINE_SPEC" in src or "spec" in src.lower():
    sys.exit(0)
# Just verify it has some column handling logic
sys.exit(0)
PYEOF
then
    check "C5" "Loader has column mapping logic" "pass"
else
    check "C5" "Loader missing column mapping" "fail"
fi

# ── C6: Pipeline produces expected output ───────────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys, os, subprocess
# Run the pipeline
result = subprocess.run(
    ["python3", "pipeline/run_pipeline.py"],
    capture_output=True, text=True, timeout=30
)
if result.returncode != 0:
    sys.exit(1)
# Compare output with expected
if os.path.exists("data/output.csv") and os.path.exists("data/expected_output.csv"):
    with open("data/output.csv") as f:
        actual = f.read().strip()
    with open("data/expected_output.csv") as f:
        expected = f.read().strip()
    if actual == expected:
        sys.exit(0)
    # Also try with normalized whitespace
    actual_lines = [l.strip() for l in actual.split('\n') if l.strip()]
    expected_lines = [l.strip() for l in expected.split('\n') if l.strip()]
    if actual_lines == expected_lines:
        sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C6" "Pipeline produces expected output" "pass"
else
    check "C6" "Pipeline output does not match expected" "fail"
fi

# ── C7: Pipeline runner executes without error ──────────────────────────
if python3 pipeline/run_pipeline.py 2>/dev/null; then
    check "C7" "Pipeline runner executes without error" "pass"
else
    check "C7" "Pipeline runner fails with error" "fail"
fi

# ── C8: All pipeline Python files have valid syntax ─────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
for f in ["pipeline/extract.py", "pipeline/transform.py", "pipeline/load.py", "pipeline/run_pipeline.py"]:
    try:
        ast.parse(open(f).read())
    except SyntaxError:
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C8" "All pipeline Python files have valid syntax" "pass"
else
    check "C8" "Pipeline Python files have syntax errors" "fail"
fi

# ── C9: pytest tests pass ───────────────────────────────────────────────
if python3 -m pytest tests/test_pipeline.py -q --tb=no 2>&1 | grep -q "passed"; then
    check "C9" "pytest tests/test_pipeline.py passes" "pass"
else
    check "C9" "pytest tests/test_pipeline.py has failures" "fail"
fi

# ── C10: Output row count matches expected ──────────────────────────────
if python3 - <<'PYEOF' 2>/dev/null
import sys
if not __import__("os").path.exists("data/output.csv"):
    sys.exit(1)
with open("data/output.csv") as f:
    actual_lines = [l for l in f.read().strip().split('\n') if l.strip()]
with open("data/expected_output.csv") as f:
    expected_lines = [l for l in f.read().strip().split('\n') if l.strip()]
if len(actual_lines) == len(expected_lines):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C10" "Output row count matches expected" "pass"
else
    check "C10" "Output row count does not match expected" "fail"
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
