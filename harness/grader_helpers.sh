#!/usr/bin/env bash
# ============================================================================
# TeamBench Grader Helper Library
#
# Source this file at the top of grade.sh scripts to get common grading
# functions. Reduces boilerplate by ~50 lines per grader.
#
# Usage:
#   #!/usr/bin/env bash
#   set -euo pipefail
#   WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
#   REPORTS="${2:-${REPORTS_DIR:-/reports}}"
#   source "$(dirname "$0")/../../harness/grader_helpers.sh"
#   init_grader 10   # total number of checks
#   cd "${WORKSPACE}"
#
#   check "C1" "description" "pass"
#   ...
#   finalize_grader
# ============================================================================

# ── State variables ──────────────────────────────────────────────────────────
_GRADER_PASS=true
_GRADER_PARTIAL=0
_GRADER_TOTAL=0
_GRADER_FINDINGS=""

# ── init_grader(total_checks) ───────────────────────────────────────────────
# Initialize the grader with the expected number of checks.
init_grader() {
    _GRADER_TOTAL="${1:?init_grader requires total_checks argument}"
    _GRADER_PASS=true
    _GRADER_PARTIAL=0
    _GRADER_FINDINGS=""

    # Activate venv if available
    source /usr/local/lib/venv/bin/activate 2>/dev/null || true
}

# ── check(id, description, "pass"|"fail") ──────────────────────────────────
# Record a single check result.
check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        _GRADER_PARTIAL=$((_GRADER_PARTIAL + 1))
        _GRADER_FINDINGS="${_GRADER_FINDINGS}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        _GRADER_PASS=false
        _GRADER_FINDINGS="${_GRADER_FINDINGS}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

# ── run_pytest_check(check_id, description, test_path, [extra_args...]) ─────
# Run pytest on a test file/directory and record pass/fail.
run_pytest_check() {
    local id="$1"
    local desc="$2"
    local test_path="$3"
    shift 3
    local extra_args=("$@")

    if python -m pytest "$test_path" -q --tb=short "${extra_args[@]}" 2>&1 | tail -5 | grep -qE "passed|no tests"; then
        check "$id" "$desc" "pass"
    else
        check "$id" "$desc" "fail"
    fi
}

# ── run_python_check(check_id, description, python_code) ───────────────────
# Run inline Python code that prints "pass" or "fail" to stdout.
run_python_check() {
    local id="$1"
    local desc="$2"
    local code="$3"

    local result
    result=$(python3 -c "$code" 2>/dev/null || echo "fail")
    check "$id" "$desc" "$result"
}

# ── check_file_exists(check_id, description, filepath) ─────────────────────
# Check that a file exists.
check_file_exists() {
    local id="$1"
    local desc="$2"
    local filepath="$3"

    if [ -f "$filepath" ]; then
        check "$id" "$desc" "pass"
    else
        check "$id" "$desc" "fail"
    fi
}

# ── check_file_contains(check_id, description, filepath, pattern) ──────────
# Check that a file contains a grep pattern.
check_file_contains() {
    local id="$1"
    local desc="$2"
    local filepath="$3"
    local pattern="$4"

    if grep -qE "$pattern" "$filepath" 2>/dev/null; then
        check "$id" "$desc" "pass"
    else
        check "$id" "$desc" "fail"
    fi
}

# ── check_file_not_contains(check_id, description, filepath, pattern) ──────
# Check that a file does NOT contain a grep pattern.
check_file_not_contains() {
    local id="$1"
    local desc="$2"
    local filepath="$3"
    local pattern="$4"

    if grep -qE "$pattern" "$filepath" 2>/dev/null; then
        check "$id" "$desc" "fail"
    else
        check "$id" "$desc" "pass"
    fi
}

# ── check_command_succeeds(check_id, description, command...) ──────────────
# Check that a command exits with status 0.
check_command_succeeds() {
    local id="$1"
    local desc="$2"
    shift 2

    if "$@" >/dev/null 2>&1; then
        check "$id" "$desc" "pass"
    else
        check "$id" "$desc" "fail"
    fi
}

# ── check_go_builds(check_id, description, go_dir) ────────────────────────
# Check that a Go project compiles.
check_go_builds() {
    local id="$1"
    local desc="$2"
    local go_dir="$3"

    if (cd "$go_dir" && go build ./... 2>/dev/null); then
        check "$id" "$desc" "pass"
    else
        check "$id" "$desc" "fail"
    fi
}

# ── run_inline_python(python_code) ─────────────────────────────────────────
# Run inline Python and capture JSON output. Used for complex multi-check
# grading. The Python code should print a JSON dict like {"C2": true, "C3": false}.
run_inline_python() {
    local code="$1"
    local output_file="/tmp/_grader_inline_$$.json"

    (python3 -c "$code") > "$output_file" 2>/tmp/_grader_inline_err_$$.txt || true

    if [ -f "$output_file" ] && [ -s "$output_file" ]; then
        echo "$output_file"
    else
        echo ""
    fi
}

# ── parse_inline_result(output_file, check_id, description) ───────────────
# Parse a single check result from inline Python JSON output.
parse_inline_result() {
    local output_file="$1"
    local id="$2"
    local desc="$3"

    if [ -z "$output_file" ] || [ ! -f "$output_file" ]; then
        check "$id" "$desc" "fail"
        return
    fi

    local val
    val=$(python3 -c "
import json, sys
d = json.load(open('$output_file'))
print('pass' if d.get('$id', False) else 'fail')
" 2>/dev/null || echo "fail")
    check "$id" "$desc" "$val"
}

# ── finalize_grader() ──────────────────────────────────────────────────────
# Write score.json and exit. Call this at the end of every grade.sh.
finalize_grader() {
    local reports_dir="${REPORTS:-/reports}"
    local partial_score
    # hardened-by: scripts/repair_graders.py: guard a zero denominator so a grader whose checks
    # were all removed still emits a well-formed score.json instead of
    # dying on ZeroDivisionError and producing no score at all.
    if [ "${_GRADER_TOTAL:-0}" -le 0 ]; then _GRADER_TOTAL=1; fi
    partial_score=$(python3 -c "print(round($_GRADER_PARTIAL / $_GRADER_TOTAL, 2))")

    # Remove trailing comma from findings
    _GRADER_FINDINGS="${_GRADER_FINDINGS%,}"

    mkdir -p "${reports_dir}"
    cat > "${reports_dir}/score.json" <<EOF
{
  "pass": $( [ "$_GRADER_PASS" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $_GRADER_PARTIAL,
    "checks_total": $_GRADER_TOTAL
  },
  "failure_modes": [],
  "checklist": [$_GRADER_FINDINGS]
}
EOF
}

# ── tb_require(pkg...) ──────────────────────────────────────────────────────
# Assert that grader dependencies are importable. Never installs, never touches
# the network. A missing dependency is an ENVIRONMENT failure, not a submission
# failure, so it is reported as such instead of being charged to the agent.
tb_require() {
    local missing=""
    for _pkg in "$@"; do
        local _mod
        case "$_pkg" in
            pyyaml) _mod=yaml ;;
            pyjwt|PyJWT) _mod=jwt ;;
            pytest-cov) _mod=pytest_cov ;;
            pytest-asyncio) _mod=pytest_asyncio ;;
            python-dotenv) _mod=dotenv ;;
            argon2-cffi) _mod=argon2 ;;
            pip-audit) _mod=pip_audit ;;
            *) _mod=$(echo "$_pkg" | tr '-' '_') ;;
        esac
        python3 -c "import ${_mod}" 2>/dev/null || missing="${missing} ${_pkg}"
    done
    if [ -n "${missing}" ]; then
        echo "GRADER ENVIRONMENT INCOMPLETE, missing:${missing}" >&2
        echo "  build it with: pip install -r harness/requirements.graders.txt" >&2
        _GRADER_ENV_MISSING="${missing}"
        return 1
    fi
    return 0
}

# tb_import_module <path/to/source_file.py>
#
# Import a source file BY ITS DOTTED MODULE NAME. Exit 0 if it imports.
#
# The check this replaces did:
#     spec = importlib.util.spec_from_file_location('mod', src_path)
#     spec.loader.exec_module(module_from_spec(spec))
# which loads a package-internal file as a detached top-level module called
# 'mod'. Every relative import inside it then raises
#     ImportError: attempted relative import with no known parent package
# so the check could never pass, whatever the submission did: measured failing
# with the maintainers' own merged fix applied on 37 of 59 staged tasks, which
# also made the grader's overall `pass` unreachable and capped partial_score
# below 1.0. Importing by package name resolves relative imports the way Python
# does, and still answers the question the check is asking.
#
# A timeout is applied because importing a package runs its __init__, and a few
# repos load a model or open a socket there.
tb_import_module() {
    timeout 60 python3 - "$1" <<'TBPYEOF'
import importlib, os, sys

rel = sys.argv[1].replace(os.sep, "/")
if rel.endswith(".py"):
    rel = rel[:-3]
parts = [p for p in rel.split("/") if p not in ("", ".")]
# `src/` and `lib/` are layout, not part of the module path
while parts and parts[0] in ("src", "lib"):
    parts.pop(0)
if parts and parts[-1] == "__init__":
    parts.pop()
if not parts:
    sys.exit(0)
for root in ("src", "lib", "."):
    if os.path.isdir(root):
        sys.path.insert(0, os.path.abspath(root))
try:
    importlib.import_module(".".join(parts))
except Exception as e:
    sys.stderr.write("%s: %s\n" % (type(e).__name__, str(e)[:160]))
    sys.exit(1)
TBPYEOF
}
