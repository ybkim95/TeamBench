        #!/usr/bin/env bash
        # Grader for GH953_scikit_learn_20853
        # Source: https://github.com/scikit-learn/scikit-learn/pull/20853
        # Repo:   https://github.com/scikit-learn/scikit-learn
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 4
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        # was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
        tb_require pytest || true
# TODO: add repo-specific dependencies

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$(pytest sklearn/tests/test_common.py sklearn/tests/test_multiclass.py -x -q --tb=short -p no:cacheprovider --override-ini=addopts= --override-ini=filterwarnings= 2>&1)
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in sklearn/ensemble/_forest.py sklearn/linear_model/_ransac.py sklearn/multiclass.py sklearn/semi_supervised/_self_training.py; do
            if [ -f "$src" ]; then
                python3 -c "import ast; ast.parse(open('$src').read())" 2>/dev/null || {
                    syntax_ok=false
                    break
                }
            fi
        done
        check "C2" "source files are valid Python" "$([ $syntax_ok = true ] && echo pass || echo fail)"

# ── C3: Test files present and intact ─────────────────────────────────
# repaired-by: scripts/repair_graders.py (R1 c3-heredoc)
# (Agents must not cheat by deleting or gutting the tests.)
# The inline python is a column-0 heredoc so it actually parses; the
# filename is passed via the environment, not interpolated into source;
# and a MISSING test file now fails instead of vacuously passing.
tests_unmodified=true
for tfile in sklearn/tests/test_common.py sklearn/tests/test_multiclass.py; do
    if [ ! -f "$tfile" ]; then
        tests_unmodified=false
        continue
    fi
    TB_TFILE="$tfile" python3 - <<'_TBPY' 2>/dev/null || tests_unmodified=false
import ast, os, sys
src = open(os.environ['TB_TFILE']).read()
tree = ast.parse(src)
fns = [n.name for n in ast.walk(tree)
       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
       and n.name.startswith('test_')]
sys.exit(0 if fns else 1)
_TBPY
done
check "C3" "test files present and intact" "$([ $tests_unmodified = true ] && echo pass || echo fail)"

# ── C4 (no test failures / 0 FAILED) REMOVED ─────────────────────────
# removed-by: scripts/repair_graders.py (R2 c4-vacuous-duplicate)
# It counted `^FAILED` lines, so a pytest COLLECTION ERROR (which
# prints ERROR, not FAILED) free-passed it, and it duplicated C1's
# pytest target. Denominator decremented accordingly.

        # ── C5: Import of fixed modules succeeds ──────────────────────────────
        import_ok=true
        for src in sklearn/ensemble/_forest.py sklearn/linear_model/_ransac.py sklearn/multiclass.py sklearn/semi_supervised/_self_training.py; do
            if [ -f "$src" ]; then
                tb_import_module "$src" 2>/dev/null || import_ok=false
            fi
        done
        check "C5" "source modules import without error" "$([ $import_ok = true ] && echo pass || echo fail)"

        finalize_grader

# hermetic-by: scripts/make_graders_hermetic.py
