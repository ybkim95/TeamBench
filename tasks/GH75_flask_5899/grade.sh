        #!/usr/bin/env bash
        # Grader for GH75_flask_5899
        # Source: https://github.com/pallets/flask/pull/5899
        # Repo:   https://github.com/pallets/flask
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 10
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        # was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
        tb_require flask pytest || true

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$(python -m pytest -x -q --tb=short -p no:cacheprovider --override-ini=addopts= --override-ini=filterwarnings= 2>&1)
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in src/flask/app.py src/flask/sansio/app.py; do
            if [ -f "$src" ]; then
                python3 -c "import ast; ast.parse(open('$src').read())" 2>/dev/null || {
                    syntax_ok=false
                    break
                }
            fi
        done
        check "C2" "source files are valid Python" "$([ $syntax_ok = true ] && echo pass || echo fail)"

# ── C3 (test files present and intact) REMOVED ───────────────────────
# removed-by: scripts/repair_graders.py (R1 c3-not-evaluable)
# The shipped workspace contains NONE of the test files this check
# named, so the check is not evaluable for this task. Scoring an
# unevaluable check either awards free credit (the pre-repair
# behaviour) or caps partial_score below 1.0 forever. Removed and
# denominator decremented instead.
# not evaluable: tests/

# ── C4 (no test failures / 0 FAILED) REMOVED ─────────────────────────
# removed-by: scripts/repair_graders.py (R2 c4-vacuous-duplicate)
# It counted `^FAILED` lines, so a pytest COLLECTION ERROR (which
# prints ERROR, not FAILED) free-passed it, and it duplicated C1's
# pytest target. Denominator decremented accordingly.

        # ── C5: Import of fixed modules succeeds ──────────────────────────────
        import_ok=true
        for src in src/flask/app.py src/flask/sansio/app.py; do
            if [ -f "$src" ]; then
                tb_import_module "$src" 2>/dev/null || import_ok=false
            fi
        done
        check "C5" "source modules import without error" "$([ $import_ok = true ] && echo pass || echo fail)"


# ════════════════════════════════════════════════════════════════════
# ENHANCED CHECKS (added by scripts/enhance_graders.py)
# ════════════════════════════════════════════════════════════════════
# ── C6: No hardcoded magic / cheating markers ──────────────────────
_cheat_found=false
for _src in src/flask/app.py src/flask/sansio/app.py; do
    [ -f "$_src" ] || continue
    # Patterns that suggest a hardcoded shortcut rather than a real fix
    if grep -qE '(HARDCODED|MAGIC_ANSWER|# CHEAT|raise NotImplementedError.*TODO)' \
            "$_src" 2>/dev/null; then
        _cheat_found=true; break
    fi
done
check "C6" "no hardcoded magic / cheating markers in source" \
    "$([ $_cheat_found = false ] && echo pass || echo fail)"
unset _cheat_found _src

# ── C7: Source file not wiped ─────────────────────────────────────
_linecount=$(wc -l < 'src/flask/app.py' 2>/dev/null || echo 0)
check "C7" "src/flask/app.py has at least 795 lines (not wiped)" \
    "$([ "$_linecount" -ge 795 ] && echo pass || echo fail)"
unset _linecount

# ── C8: Source file not wiped ─────────────────────────────────────
_linecount=$(wc -l < 'src/flask/sansio/app.py' 2>/dev/null || echo 0)
check "C8" "src/flask/sansio/app.py has at least 504 lines (not wiped)" \
    "$([ "$_linecount" -ge 504 ] && echo pass || echo fail)"
unset _linecount

# ── C9: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('src/flask/app.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["remove_ctx", "add_ctx", "Flask"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C9" "key symbols still defined in src/flask/app.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C10: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('src/flask/sansio/app.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["App"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C10" "key symbols still defined in src/flask/sansio/app.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C11: Fixed pattern removed ─────────────────────────────────────
# The old buggy pattern should no longer appear in the fixed file
check "C11" "old buggy pattern removed: old 'is not' comparison replaced with 'is'" \
    "$(grep -qF 'if error is not None and self.should_ignore_error(error):' 'src/flask/app.py' 2>/dev/null && echo fail || echo pass)"

# ── C12: Fix pattern present ────────────────────────────────────────
# The fix should introduce this pattern
check "C12" "fix pattern present: fix introduces expected string" \
    "$(grep -qF 'The '\''should_ignore_error'\'' method is deprecated and will' 'src/flask/app.py' 2>/dev/null && echo pass || echo fail)"

        finalize_grader

# hermetic-by: scripts/make_graders_hermetic.py
