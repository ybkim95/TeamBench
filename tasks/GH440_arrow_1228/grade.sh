        #!/usr/bin/env bash
        # Grader for GH440_arrow_1228
        # Source: https://github.com/arrow-py/arrow/pull/1228
        # Repo:   https://github.com/arrow-py/arrow
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 7
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
        for src in arrow/_version.py; do
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
        for src in arrow/_version.py; do
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
for _src in arrow/_version.py; do
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
_linecount=$(wc -l < 'arrow/_version.py' 2>/dev/null || echo 0)
check "C7" "arrow/_version.py has at least 5 lines (not wiped)" \
    "$([ "$_linecount" -ge 5 ] && echo pass || echo fail)"
unset _linecount

# ── C8: Fix pattern present ────────────────────────────────────────
# The fix should introduce this pattern
check "C8" "fix pattern present: fix introduces expected string" \
    "$(grep -qF '1.4.0' 'arrow/_version.py' 2>/dev/null && echo pass || echo fail)"

# ── C9: Fixed pattern removed ─────────────────────────────────────
# The old buggy pattern should no longer appear in the fixed file
check "C9" "old buggy pattern removed: old pattern removed by fix" \
    "$(grep -qF '1.3.0' 'arrow/_version.py' 2>/dev/null && echo fail || echo pass)"

        finalize_grader

# hermetic-by: scripts/make_graders_hermetic.py
