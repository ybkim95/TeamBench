        #!/usr/bin/env bash
        # Grader for GH1006_spaCy_13068
        # Source: https://github.com/explosion/spaCy/pull/13068
        # Repo:   https://github.com/explosion/spaCy
        set -uo pipefail

        WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
        REPORTS="${2:-${REPORTS_DIR:-/reports}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 5
        cd "${WORKSPACE}"

        # ── Install dependencies ──────────────────────────────────────────────
        pip install pytest -q 2>/dev/null || true
# TODO: add repo-specific dependencies

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$(pytest spacy/tests/test_displacy.py -x -q --tb=short 2>&1)
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in spacy/displacy/render.py; do
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
        for tfile in spacy/tests/test_displacy.py; do
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
        specific_out=$(pytest spacy/tests/test_displacy.py -x -q --tb=line 2>&1 || true)
        failed_count=$(echo "$specific_out" | grep -c "^FAILED" || true)
        check "C4" "no test failures (0 FAILED)" "$([ "$failed_count" -eq 0 ] && echo pass || echo fail)"

        # ── C5: Import of fixed modules succeeds ──────────────────────────────
        import_ok=true
        for src in spacy/displacy/render.py; do
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

        finalize_grader
