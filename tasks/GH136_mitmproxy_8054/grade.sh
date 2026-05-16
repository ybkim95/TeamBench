        #!/usr/bin/env bash
        # Grader for GH136_mitmproxy_8054
        # Source: https://github.com/mitmproxy/mitmproxy/pull/8054
        # Repo:   https://github.com/mitmproxy/mitmproxy
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 9
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        pip install pytest -q 2>/dev/null || true
# TODO: add repo-specific dependencies

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$(pytest test/mitmproxy/contentviews/test__view_zip.py -x -q --tb=short 2>&1)
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in mitmproxy/contentviews/__init__.py mitmproxy/contentviews/_view_zip.py; do
            if [ -f "$src" ]; then
                python3 -c "import ast; ast.parse(open('$src').read())" 2>/dev/null || {
                    syntax_ok=false
                    break
                }
            fi
        done
        check "C2" "source files are valid Python" "$([ $syntax_ok = true ] && echo pass || echo fail)"

        # ── C3: No test files modified ────────────────────────────────────────
        # (Agents must not cheat by patching tests)
        tests_unmodified=true
        for tfile in test/mitmproxy/contentviews/test__view_zip.py; do
            if [ -f "$tfile" ]; then
                # Check file exists and has test functions (basic sanity)
                python3 -c "
        import ast, sys
        src = open('$tfile').read()
        tree = ast.parse(src)
        fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
        sys.exit(0 if fns else 1)
        " 2>/dev/null || tests_unmodified=false
            fi
        done
        check "C3" "test files present and intact" "$([ $tests_unmodified = true ] && echo pass || echo fail)"

        # ── C4: Specific failure mode no longer triggers ───────────────────────
        # Run failing test patterns from the PR to catch regression
        specific_out=$(pytest test/mitmproxy/contentviews/test__view_zip.py -x -q --tb=line 2>&1 || true)
        failed_count=$(echo "$specific_out" | grep -c "^FAILED" || true)
        check "C4" "no test failures (0 FAILED)" "$([ "$failed_count" -eq 0 ] && echo pass || echo fail)"

        # ── C5: Import of fixed modules succeeds ──────────────────────────────
        import_ok=true
        for src in mitmproxy/contentviews/__init__.py mitmproxy/contentviews/_view_zip.py; do
            if [ -f "$src" ]; then
                python3 - "$src" <<'PYEOF' 2>/dev/null || import_ok=false
import importlib.util, sys
src_path = sys.argv[1]
spec = importlib.util.spec_from_file_location('mod', src_path)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    sys.exit(1)
PYEOF
            fi
        done
        check "C5" "source modules import without error" "$([ $import_ok = true ] && echo pass || echo fail)"


# ════════════════════════════════════════════════════════════════════
# ENHANCED CHECKS (added by scripts/enhance_graders.py)
# ════════════════════════════════════════════════════════════════════
# ── C6: No hardcoded magic / cheating markers ──────────────────────
_cheat_found=false
for _src in mitmproxy/contentviews/__init__.py mitmproxy/contentviews/_view_zip.py; do
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
_linecount=$(wc -l < 'mitmproxy/contentviews/__init__.py' 2>/dev/null || echo 0)
check "C7" "mitmproxy/contentviews/__init__.py has at least 96 lines (not wiped)" \
    "$([ "$_linecount" -ge 96 ] && echo pass || echo fail)"
unset _linecount

# ── C8: Key symbols still defined ──────────────────────────────
python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false
import ast, sys
src = open('mitmproxy/contentviews/__init__.py').read()
tree = ast.parse(src)
defined = {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
required = ["ContentviewResult", "prettify_message", "reencode_message", "add"]
missing = [s for s in required if s not in defined]
if missing:
    print(f'Missing symbols: {missing}', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
check "C8" "key symbols still defined in mitmproxy/contentviews/__init__.py" \
    "$([ ${_sym_ok:-false} = true ] && echo pass || echo fail)"
unset _sym_ok

# ── C9: Fix pattern present ────────────────────────────────────────
# The fix should introduce this pattern
check "C9" "fix pattern present: fix introduces expected string" \
    "$(grep -qF 'ZIP Archive' 'mitmproxy/contentviews/__init__.py' 2>/dev/null && echo pass || echo fail)"

        finalize_grader
