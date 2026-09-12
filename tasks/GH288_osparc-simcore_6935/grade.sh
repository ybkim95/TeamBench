        #!/usr/bin/env bash
        # Grader for GH288_osparc-simcore_6935
        # Source: https://github.com/ITISFoundation/osparc-simcore/pull/6935
        # Repo:   https://github.com/ITISFoundation/osparc-simcore
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 10
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        # was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
        tb_require pytest || true
# TODO: add repo-specific dependencies

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$(pytest services/storage/tests/unit/test_db_file_meta_data.py services/storage/tests/unit/test_handlers_files.py services/storage/tests/unit/test_simcore_s3_dsm_utils.py -x -q --tb=short -p no:cacheprovider --override-ini=addopts= --override-ini=filterwarnings= 2>&1)
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in services/storage/src/simcore_service_storage/db_file_meta_data.py services/storage/src/simcore_service_storage/simcore_s3_dsm.py services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py; do
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
for tfile in services/storage/tests/unit/test_db_file_meta_data.py services/storage/tests/unit/test_handlers_files.py services/storage/tests/unit/test_simcore_s3_dsm_utils.py; do
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
        for src in services/storage/src/simcore_service_storage/db_file_meta_data.py services/storage/src/simcore_service_storage/simcore_s3_dsm.py services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py; do
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
for _src in services/storage/src/simcore_service_storage/db_file_meta_data.py services/storage/src/simcore_service_storage/simcore_s3_dsm.py services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py; do
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
_linecount=$(wc -l < 'services/storage/src/simcore_service_storage/db_file_meta_data.py' 2>/dev/null || echo 0)
check "C7" "services/storage/src/simcore_service_storage/db_file_meta_data.py has at least 103 lines (not wiped)" \
    "$([ "$_linecount" -ge 103 ] && echo pass || echo fail)"
unset _linecount

# ── C8: Source file not wiped ─────────────────────────────────────
_linecount=$(wc -l < 'services/storage/src/simcore_service_storage/simcore_s3_dsm.py' 2>/dev/null || echo 0)
check "C8" "services/storage/src/simcore_service_storage/simcore_s3_dsm.py has at least 550 lines (not wiped)" \
    "$([ "$_linecount" -ge 550 ] && echo pass || echo fail)"
unset _linecount

# ── C9: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('services/storage/src/simcore_service_storage/db_file_meta_data.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["exists", "upsert", "insert", "get"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C9" "key symbols still defined in services/storage/src/simcore_service_storage/db_file_meta_data.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C10: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('services/storage/src/simcore_service_storage/simcore_s3_dsm.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["SimcoreS3DataManager", "create_simcore_s3_data_manager"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C10" "key symbols still defined in services/storage/src/simcore_service_storage/simcore_s3_dsm.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C11: Fix pattern present ────────────────────────────────────────
# The fix should introduce this pattern
check "C11" "fix pattern present: fix introduces expected string" \
    "$(grep -qF ').split(' 'services/storage/src/simcore_service_storage/db_file_meta_data.py' 2>/dev/null && echo pass || echo fail)"

        finalize_grader

# hermetic-by: scripts/make_graders_hermetic.py
