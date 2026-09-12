        #!/usr/bin/env bash
        # Grader for GH485_bootrun-backend_111
        # Source: https://github.com/I5-Team/bootrun-backend/pull/111
        # Repo:   https://github.com/I5-Team/bootrun-backend
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 8
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        # was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
        tb_require pytest || true
# TODO: add repo-specific dependencies

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
        for src in alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py app/models/progress.py app/services/enrollment_service.py; do
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
        for src in alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py app/models/progress.py app/services/enrollment_service.py; do
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
for _src in alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py app/models/progress.py app/services/enrollment_service.py; do
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
_linecount=$(wc -l < 'app/models/progress.py' 2>/dev/null || echo 0)
check "C7" "app/models/progress.py has at least 28 lines (not wiped)" \
    "$([ "$_linecount" -ge 28 ] && echo pass || echo fail)"
unset _linecount

# ── C8: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('app/models/progress.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["Enrollment", "Progress"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C8" "key symbols still defined in app/models/progress.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C9: Fix pattern present ────────────────────────────────────────
# The fix should introduce this pattern
check "C9" "fix pattern present: fix introduces expected string" \
    "$(grep -qF 'Upgrade schema.' 'alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py' 2>/dev/null && echo pass || echo fail)"

# ── C10: Fixed pattern removed ─────────────────────────────────────
# The old buggy pattern should no longer appear in the fixed file
check "C10" "old buggy pattern removed: old pattern removed by fix" \
    "$(grep -qF '총 시청 시간 (초)' 'alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py' 2>/dev/null && echo fail || echo pass)"

        finalize_grader

# hermetic-by: scripts/make_graders_hermetic.py
