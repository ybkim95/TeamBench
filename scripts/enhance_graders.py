#!/usr/bin/env python3
"""
enhance_graders.py — Improve grading rigor for TeamBench GitHub-sourced tasks.

Auto-generated graders average ~5 checks. This script adds additional checks
targeting source integrity, forbidden patterns, key symbol preservation, and
fix-specific behaviour derived from spec.md diffs.

Usage:
    python scripts/enhance_graders.py --task GH17_aiohttp_10151
    python scripts/enhance_graders.py --all-github
    python scripts/enhance_graders.py --dry-run
    python scripts/enhance_graders.py --dry-run --task GH28_jinja_1852
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
TASKS_DIR = REPO_ROOT / "tasks"
HARNESS_HELPERS = "$(dirname \"$0\")/../../harness/grader_helpers.sh"

# ---------------------------------------------------------------------------
# Helpers: parse curation_notes.json
# ---------------------------------------------------------------------------

def load_curation_notes(task_dir: Path) -> dict:
    p = task_dir / "curation_notes.json"
    if p.exists() and p.stat().st_size > 2:
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def load_task_yaml(task_dir: Path) -> dict:
    """Parse task.yaml as a simple key:value store (no full YAML parser needed)."""
    p = task_dir / "task.yaml"
    result = {}
    if not p.exists():
        return result
    for line in p.read_text().splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def load_spec_md(task_dir: Path) -> str:
    p = task_dir / "spec.md"
    return p.read_text() if p.exists() else ""


# ---------------------------------------------------------------------------
# Helpers: parse existing grade.sh
# ---------------------------------------------------------------------------

def parse_existing_grade(grade_sh: str) -> dict:
    """Return metadata about the existing grader."""
    info = {
        "check_count": 0,
        "uses_init_grader": False,
        "uses_helpers": False,
        "source_files_in_grader": [],
        "test_files_in_grader": [],
        "has_syntax_check": False,
        "has_import_check": False,
        "has_no_test_modification_check": False,
        "has_no_hack_check": False,
        "has_file_existence_check": False,
        "has_key_symbol_check": False,
        "has_fix_specific_check": False,
        "existing_check_ids": [],
    }

    # Count checks
    m = re.search(r"init_grader\s+(\d+)", grade_sh)
    if m:
        info["check_count"] = int(m.group(1))
        info["uses_init_grader"] = True
    else:
        # Old-style CHECKS counter
        info["check_count"] = len(re.findall(r'(?:^|\n)\s*check\s+["\']?C\d+', grade_sh))
        if not info["check_count"]:
            info["check_count"] = len(re.findall(r'CHECKS=\$\(\(CHECKS \+ 1\)\)', grade_sh))

    info["uses_helpers"] = "grader_helpers.sh" in grade_sh

    # Detect source/test files mentioned
    info["source_files_in_grader"] = re.findall(
        r'for src in ([^;]+?);', grade_sh
    )
    info["test_files_in_grader"] = re.findall(
        r'for tfile in ([^;]+?);', grade_sh
    )

    # Detect existing check categories
    lower = grade_sh.lower()
    info["has_syntax_check"] = "ast.parse" in grade_sh or "syntax" in lower
    info["has_import_check"] = "import_ok" in grade_sh or "importlib" in grade_sh
    info["has_no_test_modification_check"] = "test files" in lower or "tests_unmodified" in grade_sh
    info["has_no_hack_check"] = "hack" in lower or "forbidden" in lower or "cheat" in lower
    info["has_file_existence_check"] = "-f " in grade_sh and "exists" in lower
    info["has_key_symbol_check"] = "class " in grade_sh and "ast.walk" in grade_sh
    info["has_fix_specific_check"] = "C6" in grade_sh or "C7" in grade_sh

    # Collect existing check IDs
    info["existing_check_ids"] = re.findall(r'"(C\d+)"', grade_sh)

    return info


def next_check_id(existing_ids: list[str]) -> str:
    """Return the next unused CXX id."""
    nums = [int(re.search(r"\d+", cid).group()) for cid in existing_ids if re.search(r"\d+", cid)]
    return f"C{max(nums) + 1}" if nums else "C6"


# ---------------------------------------------------------------------------
# Diff analysis: extract symbols changed in the PR
# ---------------------------------------------------------------------------

def extract_diff_symbols(spec_md: str, language: str) -> dict:
    """
    Parse diff hunks from spec.md and extract:
    - functions/classes added or modified
    - string literals that appear in + lines (potential assert targets)
    - removed patterns (things that should no longer appear)
    - added patterns (things that must now appear)
    """
    result = {
        "added_lines": [],
        "removed_lines": [],
        "modified_functions": [],
        "modified_classes": [],
        "added_string_literals": [],
        "removed_string_literals": [],
        "source_files_from_diff": [],
    }

    # Extract diff blocks
    diff_blocks = re.findall(r"```diff\n(.*?)```", spec_md, re.DOTALL)
    if not diff_blocks:
        return result

    # Track which file each diff belongs to
    current_file = None
    for line in spec_md.splitlines():
        fn_match = re.match(r"### `([^`]+)`", line)
        if fn_match:
            current_file = fn_match.group(1)
            if current_file and current_file not in result["source_files_from_diff"]:
                result["source_files_from_diff"].append(current_file)

    for block in diff_blocks:
        for line in block.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:].strip()
                result["added_lines"].append(content)
                # Extract string literals from added lines
                for lit in re.findall(r'"([^"]{3,60})"', content):
                    result["added_string_literals"].append(lit)
                for lit in re.findall(r"'([^']{3,60})'", content):
                    result["added_string_literals"].append(lit)
                # Python: detect def/class
                if language == "python":
                    m = re.match(r"def (\w+)\s*\(", content)
                    if m:
                        result["modified_functions"].append(m.group(1))
                    m = re.match(r"class (\w+)[\s(:]", content)
                    if m:
                        result["modified_classes"].append(m.group(1))

            elif line.startswith("-") and not line.startswith("---"):
                content = line[1:].strip()
                result["removed_lines"].append(content)
                for lit in re.findall(r'"([^"]{3,60})"', content):
                    result["removed_string_literals"].append(lit)
                for lit in re.findall(r"'([^']{3,60})'", content):
                    result["removed_string_literals"].append(lit)

    # Deduplicate
    result["modified_functions"] = list(dict.fromkeys(result["modified_functions"]))
    result["modified_classes"] = list(dict.fromkeys(result["modified_classes"]))
    result["added_string_literals"] = list(dict.fromkeys(result["added_string_literals"]))
    result["removed_string_literals"] = list(dict.fromkeys(result["removed_string_literals"]))

    return result


# ---------------------------------------------------------------------------
# Check generators
# ---------------------------------------------------------------------------

def gen_file_exists_check(cid: str, filepath: str) -> str:
    """Check that a source file was not deleted."""
    return dedent(f"""\
        # ── {cid}: Source file still exists ──────────────────────────────────
        check "{cid}" "source file {filepath} not deleted" \\
            "$([ -f '{filepath}' ] && echo pass || echo fail)"
    """)


def gen_syntax_check_multi(cid: str, files: list[str]) -> str:
    """AST syntax check across multiple files."""
    file_list = " ".join(files)
    return dedent(f"""\
        # ── {cid}: Syntax validity of all source files ────────────────────────
        _syntax_ok=true
        for _src in {file_list}; do
            [ -f "$_src" ] || continue
            python3 -c "import ast; ast.parse(open('$_src').read())" 2>/dev/null || {{
                _syntax_ok=false; break
            }}
        done
        check "{cid}" "all source files parse without SyntaxError" \\
            "$([ $_syntax_ok = true ] && echo pass || echo fail)"
        unset _syntax_ok _src
    """)


def gen_no_hack_check(cid: str, files: list[str]) -> str:
    """Forbid # HACK / # XXX / stub bodies in source files."""
    file_list = " ".join(files)
    return dedent(f"""\
        # ── {cid}: No forbidden cheat patterns ───────────────────────────────
        # Reject # HACK, # XXX, bare-pass functions, empty stub bodies
        _hack_found=false
        for _src in {file_list}; do
            [ -f "$_src" ] || continue
            if grep -qE '^[[:space:]]*(#[[:space:]]*(HACK|XXX|FIXME|NOFIX)|pass[[:space:]]*$)' "$_src" 2>/dev/null; then
                _hack_found=true; break
            fi
        done
        check "{cid}" "no forbidden stub/cheat patterns (HACK, XXX, bare pass)" \\
            "$([ $_hack_found = false ] && echo pass || echo fail)"
        unset _hack_found _src
    """)


def gen_empty_function_check(cid: str, files: list[str]) -> str:
    """Check that no function bodies are trivially empty (only pass/...)."""
    file_list = " ".join(files)
    return dedent(f"""\
        # ── {cid}: No trivially-empty function bodies ─────────────────────────
        _empty_ok=true
        for _src in {file_list}; do
            [ -f "$_src" ] || continue
            python3 - "$_src" <<'_PYEOF' 2>/dev/null || {{ _empty_ok=false; break; }}
import ast, sys
tree = ast.parse(open(sys.argv[1]).read())
for node in ast.walk(tree):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    body = node.body
    # Trivially empty: sole statement is Pass or Expr(Ellipsis/None/str-docstring then pass)
    non_doc = [s for s in body if not (
        isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    if len(non_doc) == 1 and isinstance(non_doc[0], ast.Pass):
        print(f"Empty function: {{node.name}} at line {{node.lineno}}", file=sys.stderr)
        sys.exit(1)
sys.exit(0)
_PYEOF
        done
        check "{cid}" "no trivially-empty (pass-only) function bodies in source" \\
            "$([ $_empty_ok = true ] && echo pass || echo fail)"
        unset _empty_ok _src
    """)


def gen_key_symbol_check(cid: str, filepath: str, symbols: list[str], language: str) -> str:
    """Check that key functions/classes are still defined."""
    if not symbols:
        return ""
    if language == "python":
        sym_list = ", ".join(f'"{s}"' for s in symbols[:4])
        # Must NOT use dedent here: heredoc body must start at column 0,
        # so we write the whole block at column 0 manually.
        return (
            f"# ── {cid}: Key symbols still defined ──────────────────────────────\n"
            f"python3 - <<'_PYEOF' 2>/dev/null && _sym_ok=true || _sym_ok=false\n"
            f"import ast, sys\n"
            f"src = open('{filepath}').read()\n"
            f"tree = ast.parse(src)\n"
            f"defined = {{n.name for n in ast.walk(tree)\n"
            f"            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}}\n"
            f"required = [{sym_list}]\n"
            f"missing = [s for s in required if s not in defined]\n"
            f"if missing:\n"
            f"    print(f'Missing symbols: {{missing}}', file=sys.stderr)\n"
            f"    sys.exit(1)\n"
            f"sys.exit(0)\n"
            f"_PYEOF\n"
            f'check "{cid}" "key symbols still defined in {filepath}" \\\n'
            f'    "$([ ${{_sym_ok:-false}} = true ] && echo pass || echo fail)"\n'
            f"unset _sym_ok\n"
        )
    return ""


def gen_import_check(cid: str, module_path: str) -> str:
    """Check that a module can be imported (exec_module)."""
    return dedent(f"""\
        # ── {cid}: Module loads without import-time error ────────────────────
        python3 - <<'_PYEOF' 2>/dev/null && _imp_ok=true || _imp_ok=false
import importlib.util, sys
spec = importlib.util.spec_from_file_location('_mod', '{module_path}')
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception as e:
    print(f"Import error: {{e}}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
_PYEOF
        check "{cid}" "{module_path} loads without import-time error" \\
            "$([ ${{_imp_ok:-false}} = true ] && echo pass || echo fail)"
        unset _imp_ok
    """)


def gen_no_test_modification_check(cid: str, test_files: list[str]) -> str:
    """Verify test files still contain test functions (weren't gutted)."""
    file_list = " ".join(test_files)
    return dedent(f"""\
        # ── {cid}: Test files not gutted ────────────────────────────────────
        _tests_ok=true
        for _tf in {file_list}; do
            [ -f "$_tf" ] || continue
            python3 - "$_tf" <<'_PYEOF' 2>/dev/null || {{ _tests_ok=false; break; }}
import ast, sys
src = open(sys.argv[1]).read()
tree = ast.parse(src)
fns = [n.name for n in ast.walk(tree)
       if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
sys.exit(0 if fns else 1)
_PYEOF
        done
        check "{cid}" "test files present and contain test functions" \\
            "$([ $_tests_ok = true ] && echo pass || echo fail)"
        unset _tests_ok _tf
    """)


def gen_removed_pattern_check(cid: str, filepath: str, pattern: str, desc: str) -> str:
    """Check that a pattern from the old code no longer appears (was fixed)."""
    # Escape for bash grep -qF
    escaped = pattern.replace("'", "'\\''")
    return dedent(f"""\
        # ── {cid}: Fixed pattern removed ─────────────────────────────────────
        # The old buggy pattern should no longer appear in the fixed file
        check "{cid}" "old buggy pattern removed: {desc}" \\
            "$(grep -qF '{escaped}' '{filepath}' 2>/dev/null && echo fail || echo pass)"
    """)


def gen_added_pattern_check(cid: str, filepath: str, pattern: str, desc: str) -> str:
    """Check that a pattern from the fix now appears."""
    escaped = pattern.replace("'", "'\\''")
    return dedent(f"""\
        # ── {cid}: Fix pattern present ────────────────────────────────────────
        # The fix should introduce this pattern
        check "{cid}" "fix pattern present: {desc}" \\
            "$(grep -qF '{escaped}' '{filepath}' 2>/dev/null && echo pass || echo fail)"
    """)


def gen_no_hardcoded_answer_check(cid: str, files: list[str]) -> str:
    """Check for hardcoded magic values that would indicate cheating."""
    file_list = " ".join(files)
    return dedent(f"""\
        # ── {cid}: No hardcoded magic / cheating markers ──────────────────────
        _cheat_found=false
        for _src in {file_list}; do
            [ -f "$_src" ] || continue
            # Patterns that suggest a hardcoded shortcut rather than a real fix
            if grep -qE '(HARDCODED|MAGIC_ANSWER|# CHEAT|raise NotImplementedError.*TODO)' \\
                    "$_src" 2>/dev/null; then
                _cheat_found=true; break
            fi
        done
        check "{cid}" "no hardcoded magic / cheating markers in source" \\
            "$([ $_cheat_found = false ] && echo pass || echo fail)"
        unset _cheat_found _src
    """)


def gen_go_vet_check(cid: str) -> str:
    return dedent(f"""\
        # ── {cid}: go vet passes ───────────────────────────────────────────────
        check "{cid}" "go vet ./... passes" \\
            "$(go vet ./... 2>/dev/null && echo pass || echo fail)"
    """)


def gen_go_build_check(cid: str) -> str:
    return dedent(f"""\
        # ── {cid}: go build passes ────────────────────────────────────────────
        check "{cid}" "go build ./... succeeds" \\
            "$(go build ./... 2>/dev/null && echo pass || echo fail)"
    """)


def gen_file_unchanged_size_check(cid: str, filepath: str, min_lines: int) -> str:
    """Check a file hasn't been wiped out (has at least min_lines)."""
    return dedent(f"""\
        # ── {cid}: Source file not wiped ─────────────────────────────────────
        _linecount=$(wc -l < '{filepath}' 2>/dev/null || echo 0)
        check "{cid}" "{filepath} has at least {min_lines} lines (not wiped)" \\
            "$([ \"$_linecount\" -ge {min_lines} ] && echo pass || echo fail)"
        unset _linecount
    """)


# ---------------------------------------------------------------------------
# Diff-specific check: operator/comparison change
# ---------------------------------------------------------------------------

def _infer_fix_specific_checks(
    diff_symbols: dict,
    source_files: list[str],
    curation_notes: dict,
    spec_md: str,
    start_cid_num: int,
) -> tuple[list[str], int]:
    """
    Attempt to generate 1-3 fix-specific checks from diff analysis.
    Returns (list_of_check_blocks, next_cid_num).
    """
    checks = []
    n = start_cid_num

    added = diff_symbols.get("added_lines", [])
    removed = diff_symbols.get("removed_lines", [])
    src_files_from_diff = diff_symbols.get("source_files_from_diff", [])

    if not source_files and src_files_from_diff:
        source_files = src_files_from_diff[:2]

    if not source_files:
        return checks, n

    primary_src = source_files[0]

    # --- Check 1: comparison operator fix (e.g. <= -> <, != -> ==, etc.)
    # Find lines where only a comparison operator changed
    for rem_line in removed[:10]:
        for add_line in added[:10]:
            # Strip whitespace, find single-token difference
            r_tok = re.sub(r"\s+", " ", rem_line).strip()
            a_tok = re.sub(r"\s+", " ", add_line).strip()
            if r_tok == a_tok:
                continue
            # Common operator pairs
            op_pairs = [
                ("<=", "<"), ("<", "<="), (">=", ">"), (">", ">="),
                ("!=", "=="), ("==", "!="), ("is not", "is"),
            ]
            for old_op, new_op in op_pairs:
                if old_op in r_tok and new_op in a_tok:
                    # The old operator should be gone, new should be present
                    # Find the context around the operator in the old line
                    # and check that it's no longer present
                    old_fragment = r_tok[:60]
                    new_fragment = a_tok[:60]
                    # Only use if short enough to be a grep-able literal
                    if len(old_fragment) < 80 and old_op in old_fragment:
                        cid = f"C{n}"; n += 1
                        # Check old buggy comparison is gone
                        block = gen_removed_pattern_check(
                            cid, primary_src, old_fragment,
                            f"old {old_op!r} comparison replaced with {new_op!r}"
                        )
                        checks.append(block)
                        break
                if checks:
                    break
            if checks:
                break

    # --- Check 2: added string literal now present in file
    added_lits = diff_symbols.get("added_string_literals", [])
    # Filter to useful short literals (not single words, not very long)
    useful_lits = [
        lit for lit in added_lits
        if 8 <= len(lit) <= 50
        and not lit.startswith("http")
        and " " in lit or any(c in lit for c in "._-{}")
    ][:3]

    for lit in useful_lits[:1]:
        cid = f"C{n}"; n += 1
        block = gen_added_pattern_check(
            cid, primary_src, lit,
            f"fix introduces expected string"
        )
        checks.append(block)

    # --- Check 3: removed string literal no longer present
    removed_lits = diff_symbols.get("removed_string_literals", [])
    useful_removed = [
        lit for lit in removed_lits
        if 8 <= len(lit) <= 50
        and " " in lit or any(c in lit for c in "._-{}")
    ][:3]

    for lit in useful_removed[:1]:
        # Only add if the literal doesn't also appear in added_lits
        if lit not in added_lits:
            cid = f"C{n}"; n += 1
            block = gen_removed_pattern_check(
                cid, primary_src, lit,
                f"old pattern removed by fix"
            )
            checks.append(block)

    return checks, n


# ---------------------------------------------------------------------------
# Core: build the enhancement block for one grader
# ---------------------------------------------------------------------------

def build_enhancement(
    task_id: str,
    task_dir: Path,
    grade_sh: str,
) -> Optional[str]:
    """
    Returns a bash snippet to append before `finalize_grader`,
    plus the new total count. Returns None if nothing to add.
    """
    notes = load_curation_notes(task_dir)
    task_yaml = load_task_yaml(task_dir)
    spec_md = load_spec_md(task_dir)
    info = parse_existing_grade(grade_sh)

    language = task_yaml.get("languages", "[python]")
    is_python = "python" in language
    is_go = "go" in language

    source_files: list[str] = notes.get("source_files", [])
    test_files: list[str] = notes.get("test_files", [])
    changed_files: list[str] = notes.get("changed_files", [])

    # Diff analysis
    diff_symbols = extract_diff_symbols(spec_md, "python" if is_python else "go")
    if not source_files and diff_symbols["source_files_from_diff"]:
        source_files = diff_symbols["source_files_from_diff"]

    if not source_files:
        # Infer from changed_files: non-test, non-changelog files
        source_files = [
            f for f in changed_files
            if not re.search(r"(test|TEST|CHANGES|changelog|\.rst$|\.md$)", f)
        ]

    # If still nothing, infer from existing grader's "for src in ..." patterns
    if not source_files:
        for pat in info["source_files_in_grader"]:
            files = pat.split()
            source_files.extend(f for f in files if f and "*" not in f)

    # Python files only (filter non-py for python repos)
    if is_python:
        python_source = [f for f in source_files if f.endswith(".py")]
    else:
        python_source = []

    new_checks: list[str] = []
    existing = list(info["existing_check_ids"])
    cid_num = max(
        (int(re.search(r"\d+", c).group()) for c in existing if re.search(r"\d+", c)),
        default=5
    ) + 1

    def next_cid() -> str:
        nonlocal cid_num
        cid = f"C{cid_num}"
        existing.append(cid)
        cid_num += 1
        return cid

    # ── Block A: File existence checks ───────────────────────────────────────
    if not info["has_file_existence_check"] and source_files:
        for filepath in source_files[:3]:
            cid = next_cid()
            new_checks.append(gen_file_exists_check(cid, filepath))

    # ── Block B: Syntax check (if not already present) ────────────────────
    # The automated graders already have C2 syntax check; skip if present.
    # Only add if we found NEW source files not covered.
    if is_python and python_source and not info["has_syntax_check"]:
        cid = next_cid()
        new_checks.append(gen_syntax_check_multi(cid, python_source[:4]))

    # ── Block C: No-hack / no-cheat check ────────────────────────────────
    if not info["has_no_hack_check"] and python_source:
        cid = next_cid()
        new_checks.append(gen_no_hack_check(cid, python_source[:4]))

    # ── Block D: Hardcoded magic check ───────────────────────────────────
    if is_python and python_source:
        cid = next_cid()
        new_checks.append(gen_no_hardcoded_answer_check(cid, python_source[:4]))

    # ── Block E: File size / not-wiped check ─────────────────────────────
    for filepath in python_source[:2]:
        ws_path = task_dir / "workspace" / filepath
        if ws_path.exists():
            line_count = len(ws_path.read_text().splitlines())
            # Require at least 50% of original lines
            min_lines = max(5, line_count // 2)
            cid = next_cid()
            new_checks.append(gen_file_unchanged_size_check(cid, filepath, min_lines))

    # ── Block F: Key symbol preservation ─────────────────────────────────
    if not info["has_key_symbol_check"] and is_python and python_source:
        for filepath in python_source[:2]:
            ws_path = task_dir / "workspace" / filepath
            if not ws_path.exists():
                continue
            # Extract top-level function/class names from workspace version
            try:
                import ast as _ast
                src = ws_path.read_text()
                tree = _ast.parse(src)
                symbols = [
                    n.name for n in tree.body
                    if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef))
                    and not n.name.startswith("_")
                ][:6]
            except Exception:
                symbols = []
            if symbols:
                cid = next_cid()
                new_checks.append(gen_key_symbol_check(cid, filepath, symbols, "python"))

    # ── Block G: Test file integrity check ───────────────────────────────
    if not info["has_no_test_modification_check"] and test_files:
        py_tests = [f for f in test_files if f.endswith(".py")][:3]
        if py_tests:
            cid = next_cid()
            new_checks.append(gen_no_test_modification_check(cid, py_tests))

    # ── Block H: Import check for primary module ──────────────────────────
    if not info["has_import_check"] and is_python and python_source:
        for filepath in python_source[:1]:
            ws_path = task_dir / "workspace" / filepath
            if ws_path.exists():
                cid = next_cid()
                new_checks.append(gen_import_check(cid, filepath))

    # ── Block I: Go-specific checks ───────────────────────────────────────
    if is_go and not info["has_fix_specific_check"]:
        if "go build" not in grade_sh:
            cid = next_cid()
            new_checks.append(gen_go_build_check(cid))
        if "go vet" not in grade_sh:
            cid = next_cid()
            new_checks.append(gen_go_vet_check(cid))

    # ── Block J: Diff-derived fix-specific checks ─────────────────────────
    if spec_md and not info["has_fix_specific_check"]:
        fix_checks, cid_num = _infer_fix_specific_checks(
            diff_symbols, source_files, notes, spec_md, cid_num
        )
        # Register their IDs in existing list
        for blk in fix_checks:
            m = re.search(r'"(C\d+)"', blk)
            if m:
                existing.append(m.group(1))
        new_checks.extend(fix_checks)

    # Empty function check — add for Python tasks
    if is_python and python_source and len(new_checks) < 3:
        cid = next_cid()
        new_checks.append(gen_empty_function_check(cid, python_source[:2]))

    if not new_checks:
        return None

    header = dedent("""\

        # ════════════════════════════════════════════════════════════════════
        # ENHANCED CHECKS (added by scripts/enhance_graders.py)
        # ════════════════════════════════════════════════════════════════════
    """)
    return header + "\n".join(new_checks)


# ---------------------------------------------------------------------------
# Grade.sh rewriter
# ---------------------------------------------------------------------------

def _find_finalize_line(grade_sh: str) -> int:
    """Return the index of the finalize_grader call or score.json write."""
    for marker in [
        "finalize_grader",
        "score.json",
        'cat > "${REPORTS}/score.json"',
        'cat > "$REPORTS/score.json"',
        "partial_score=",
    ]:
        idx = grade_sh.find(marker)
        if idx != -1:
            # Find the start of that line
            line_start = grade_sh.rfind("\n", 0, idx) + 1
            return line_start
    return len(grade_sh)  # append at end


def _update_init_grader_count(grade_sh: str, additional: int) -> str:
    """Update the init_grader N argument."""
    def replacer(m):
        old_n = int(m.group(1))
        new_n = old_n + additional
        return m.group(0).replace(m.group(1), str(new_n))
    return re.sub(r"(init_grader\s+)(\d+)", lambda m: m.group(1) + str(int(m.group(2)) + additional), grade_sh)


ENHANCEMENT_MARKER = "ENHANCED CHECKS (added by scripts/enhance_graders.py)"


def enhance_grade_sh(task_id: str, task_dir: Path, dry_run: bool = False) -> dict:
    """
    Read grade.sh, compute enhancement, optionally write it back.
    Returns a result dict with keys: task_id, original_checks, new_checks, changed.
    """
    grade_path = task_dir / "grade.sh"
    if not grade_path.exists():
        return {"task_id": task_id, "error": "grade.sh not found", "changed": False}

    original = grade_path.read_text()

    # Idempotency: skip if already enhanced
    if ENHANCEMENT_MARKER in original:
        info = parse_existing_grade(original)
        return {
            "task_id": task_id,
            "original_checks": info["check_count"],
            "new_checks": info["check_count"],
            "added_checks": 0,
            "changed": False,
            "reason": "already enhanced (idempotent skip)",
        }

    info = parse_existing_grade(original)
    original_count = info["check_count"]

    enhancement = build_enhancement(task_id, task_dir, original)
    if enhancement is None:
        return {
            "task_id": task_id,
            "original_checks": original_count,
            "new_checks": original_count,
            "added_checks": 0,
            "changed": False,
            "reason": "no additional checks generated",
        }

    # Count how many new check() calls are in the enhancement block
    added_count = len(re.findall(r'\bcheck\s+"C\d+"', enhancement))

    # Insert before finalize_grader (or score.json write)
    insert_at = _find_finalize_line(original)
    new_content = original[:insert_at] + enhancement + "\n" + original[insert_at:]

    # Update init_grader count if present
    if info["uses_init_grader"]:
        new_content = _update_init_grader_count(new_content, added_count)

    new_check_count = original_count + added_count

    result = {
        "task_id": task_id,
        "original_checks": original_count,
        "new_checks": new_check_count,
        "added_checks": added_count,
        "changed": True,
    }

    if dry_run:
        print(f"\n{'='*70}")
        print(f"DRY-RUN: {task_id}  ({original_count} -> {new_check_count} checks, +{added_count})")
        print(f"{'='*70}")
        print(enhancement)
    else:
        grade_path.write_text(new_content)
        print(f"  {task_id}: {original_count} -> {new_check_count} checks (+{added_count})")

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def get_all_gh_tasks() -> list[str]:
    return sorted(
        d for d in os.listdir(TASKS_DIR)
        if d.startswith("GH") and (TASKS_DIR / d).is_dir()
    )


def main():
    parser = argparse.ArgumentParser(
        description="Enhance grading rigor for TeamBench GitHub-sourced tasks."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task", metavar="TASK_ID",
                       help="Enhance a single task (e.g. GH17_aiohttp_10151)")
    group.add_argument("--all-github", action="store_true",
                       help="Enhance all GH* tasks")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing files")
    args = parser.parse_args()

    tasks = [args.task] if args.task else get_all_gh_tasks()

    results = []
    for task_id in tasks:
        task_dir = TASKS_DIR / task_id
        if not task_dir.is_dir():
            print(f"ERROR: Task directory not found: {task_dir}", file=sys.stderr)
            sys.exit(1)
        r = enhance_grade_sh(task_id, task_dir, dry_run=args.dry_run)
        results.append(r)

    # Summary
    changed = [r for r in results if r.get("changed")]
    total_added = sum(r.get("added_checks", 0) for r in changed)
    original_avg = sum(r.get("original_checks", 0) for r in results) / max(len(results), 1)
    new_avg = sum(r.get("new_checks", r.get("original_checks", 0)) for r in results) / max(len(results), 1)

    print(f"\n{'='*60}")
    print(f"Summary: {len(tasks)} tasks, {len(changed)} enhanced, {total_added} checks added")
    print(f"Average checks: {original_avg:.1f} -> {new_avg:.1f}")
    if args.dry_run:
        print("(dry-run: no files written)")


if __name__ == "__main__":
    main()
