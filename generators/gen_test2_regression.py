"""
Parameterized generator for TEST2: Regression Tests from Bug Report.

Pattern A (hidden constraints): Brief is vague, Spec has full bug report.

Each seed produces:
- A different calculator module domain (arithmetic, string ops, list ops)
- Different bug types (off-by-one, type coercion, boundary, null handling, precision)
- 3-5 bugs per instance, each with reproduction steps and fix verification criteria
- A fixed calculator.py with all bugs corrected
- Buggy variants of calculator.py (one per bug) for regression detection testing

The agent sees: brief.md (vague), spec.md (detailed bug report), workspace/calculator.py (fixed)
The grader uses: buggy variants to verify each regression test detects the reintroduced bug.
"""
from __future__ import annotations

import textwrap
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Bug pool ──────────────────────────────────────────────────────────────────
# Each entry: (bug_id, title, domain, description, repro, expected, actual,
#              edge_cases, fix_criteria, fixed_code_snippet, buggy_code_snippet,
#              func_name, fixed_impl, buggy_impl)
#
# fixed_impl / buggy_impl are Python function bodies (strings) that will be
# embedded in the generated calculator.py.

BUG_POOL = [
    {
        "bug_id": "BUG_DIV_FLOOR",
        "title": "Integer division used instead of float division",
        "domain": "arithmetic",
        "description": (
            "The `divide` function uses integer floor division (`//`) instead of "
            "true float division (`/`), causing incorrect results for non-integer quotients."
        ),
        "repro": "Call `divide(7, 2)` — returns `3` instead of `3.5`.",
        "expected": "`divide(7, 2)` returns `3.5`",
        "actual": "`divide(7, 2)` returns `3` (integer floor division truncates)",
        "edge_cases": [
            "divide(1, 3) should return 0.3333... not 0",
            "divide(-7, 2) should return -3.5 not -4",
            "divide(10, 2) still returns 5.0 (coincidentally correct for even divisors)",
        ],
        "fix_criteria": "Replace `//` with `/` in the divide function body.",
        "func_name": "divide",
        "fixed_body": """\
def divide(a: float, b: float) -> float:
    \"\"\"Divide a by b. Raises ValueError if b is zero.\"\"\"
    if b == 0:
        raise ValueError("division_by_zero")
    return a / b
""",
        "buggy_body": """\
def divide(a: float, b: float) -> float:
    \"\"\"Divide a by b. Raises ValueError if b is zero.\"\"\"
    if b == 0:
        raise ValueError("division_by_zero")
    return a // b
""",
    },
    {
        "bug_id": "BUG_ADD_OVERFLOW",
        "title": "add() silently ignores overflow instead of raising",
        "domain": "arithmetic",
        "description": (
            "The `add` function should raise `OverflowError` when the result exceeds "
            "`MAX_VALUE` (1e15), but the overflow check is missing, returning the "
            "raw unchecked sum."
        ),
        "repro": "Call `add(1e15, 1)` — returns `1000000000000001.0` instead of raising `OverflowError`.",
        "expected": "`add(1e15, 1)` raises `OverflowError`",
        "actual": "`add(1e15, 1)` returns `1000000000000001.0` without error",
        "edge_cases": [
            "add(5e14, 5e14) should raise OverflowError (sum == 1e15 boundary is exclusive)",
            "add(4.9e14, 4.9e14) should return normally (below limit)",
            "add(-1e15, -1) should raise OverflowError (absolute value exceeds limit)",
        ],
        "fix_criteria": "Add overflow check: if abs(result) >= MAX_VALUE: raise OverflowError.",
        "func_name": "add",
        "fixed_body": """\
MAX_VALUE = 1e15

def add(a: float, b: float) -> float:
    \"\"\"Add a and b. Raises OverflowError if result exceeds MAX_VALUE.\"\"\"
    result = a + b
    if abs(result) >= MAX_VALUE:
        raise OverflowError(f"result {result} exceeds MAX_VALUE")
    return result
""",
        "buggy_body": """\
MAX_VALUE = 1e15

def add(a: float, b: float) -> float:
    \"\"\"Add a and b. Raises OverflowError if result exceeds MAX_VALUE.\"\"\"
    result = a + b
    return result
""",
    },
    {
        "bug_id": "BUG_CLAMP_OFFBYONE",
        "title": "clamp() off-by-one: upper bound incorrectly excluded",
        "domain": "arithmetic",
        "description": (
            "The `clamp` function returns `hi - 1` when the value equals `hi`, "
            "treating the upper bound as exclusive instead of inclusive."
        ),
        "repro": "Call `clamp(10, 0, 10)` — returns `9` instead of `10`.",
        "expected": "`clamp(10, 0, 10)` returns `10` (inclusive upper bound)",
        "actual": "`clamp(10, 0, 10)` returns `9`",
        "edge_cases": [
            "clamp(11, 0, 10) should return 10 (above range)",
            "clamp(0, 0, 10) should return 0 (at lower bound)",
            "clamp(5, 0, 10) should return 5 (within range)",
        ],
        "fix_criteria": "Change `< hi` to `<= hi` (or equivalently remove the `- 1` offset).",
        "func_name": "clamp",
        "fixed_body": """\
def clamp(value: float, lo: float, hi: float) -> float:
    \"\"\"Clamp value to [lo, hi] inclusive.\"\"\"
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
""",
        "buggy_body": """\
def clamp(value: float, lo: float, hi: float) -> float:
    \"\"\"Clamp value to [lo, hi] inclusive.\"\"\"
    if value < lo:
        return lo
    if value >= hi:
        return hi - 1
    return value
""",
    },
    {
        "bug_id": "BUG_PERCENT_DIVISOR",
        "title": "percent() divides by 10 instead of 100",
        "domain": "arithmetic",
        "description": (
            "The `percent` function computes `base * pct / 10` instead of "
            "`base * pct / 100`, returning values 10x too large."
        ),
        "repro": "Call `percent(200, 50)` — returns `1000.0` instead of `100.0`.",
        "expected": "`percent(200, 50)` returns `100.0`",
        "actual": "`percent(200, 50)` returns `1000.0`",
        "edge_cases": [
            "percent(100, 100) should return 100.0 not 1000.0",
            "percent(50, 10) should return 5.0 not 50.0",
            "percent(0, 50) should return 0.0 (zero base always correct)",
        ],
        "fix_criteria": "Change divisor from `10` to `100`.",
        "func_name": "percent",
        "fixed_body": """\
def percent(base: float, pct: float) -> float:
    \"\"\"Return pct percent of base.\"\"\"
    return base * pct / 100
""",
        "buggy_body": """\
def percent(base: float, pct: float) -> float:
    \"\"\"Return pct percent of base.\"\"\"
    return base * pct / 10
""",
    },
    {
        "bug_id": "BUG_SQRT_NEGATIVE",
        "title": "sqrt() does not raise on negative input",
        "domain": "arithmetic",
        "description": (
            "The `sqrt` function should raise `ValueError` for negative inputs, "
            "but the guard condition is inverted (`> 0` instead of `< 0`), "
            "causing it to raise on positive inputs and accept negatives."
        ),
        "repro": "Call `sqrt(-4)` — returns a complex number or NaN instead of raising `ValueError`.",
        "expected": "`sqrt(-4)` raises `ValueError('domain_error')`",
        "actual": "`sqrt(-4)` returns `nan` (no error raised)",
        "edge_cases": [
            "sqrt(0) should return 0.0 (boundary — valid)",
            "sqrt(4) should return 2.0 (normal positive)",
            "sqrt(2) should return approximately 1.4142135",
        ],
        "fix_criteria": "Change guard from `if a > 0` to `if a < 0`.",
        "func_name": "sqrt",
        "fixed_body": """\
import math as _math

def sqrt(a: float) -> float:
    \"\"\"Return square root of a. Raises ValueError for negative input.\"\"\"
    if a < 0:
        raise ValueError("domain_error")
    return _math.sqrt(a)
""",
        "buggy_body": """\
import math as _math

def sqrt(a: float) -> float:
    \"\"\"Return square root of a. Raises ValueError for negative input.\"\"\"
    if a > 0:
        raise ValueError("domain_error")
    return _math.sqrt(a)
""",
    },
    {
        "bug_id": "BUG_ROUND_PRECISION",
        "title": "round_to() uses wrong decimal places (2 instead of 6)",
        "domain": "arithmetic",
        "description": (
            "The `round_to` function rounds to 2 decimal places instead of the "
            "specified 6, losing precision for scientific calculations."
        ),
        "repro": "Call `round_to(1/3)` — returns `0.33` instead of `0.333333`.",
        "expected": "`round_to(1/3)` returns `0.333333`",
        "actual": "`round_to(1/3)` returns `0.33`",
        "edge_cases": [
            "round_to(1/7) should return 0.142857 not 0.14",
            "round_to(2/3) should return 0.666667 not 0.67",
            "round_to(1.0) should return 1.0 (exact — both correct)",
        ],
        "fix_criteria": "Change `round(value, 2)` to `round(value, 6)`.",
        "func_name": "round_to",
        "fixed_body": """\
def round_to(value: float, decimals: int = 6) -> float:
    \"\"\"Round value to the given number of decimal places (default 6).\"\"\"
    return round(value, decimals)
""",
        "buggy_body": """\
def round_to(value: float, decimals: int = 6) -> float:
    \"\"\"Round value to the given number of decimal places (default 6).\"\"\"
    return round(value, 2)
""",
    },
    {
        "bug_id": "BUG_POWER_SWAP",
        "title": "power() swaps base and exponent",
        "domain": "arithmetic",
        "description": (
            "The `power` function computes `exp ** base` instead of `base ** exp`, "
            "swapping the arguments."
        ),
        "repro": "Call `power(2, 10)` — returns `1024` (correct for `10**2`... wait, "
                 "actually `10**2=100` and `2**10=1024`) — returns `100` instead of `1024`.",
        "expected": "`power(2, 10)` returns `1024.0`",
        "actual": "`power(2, 10)` returns `100.0` (arguments swapped)",
        "edge_cases": [
            "power(3, 3) returns 27.0 both ways — coincidentally correct",
            "power(2, 3) should return 8.0 not 9.0",
            "power(10, 0) should return 1.0",
        ],
        "fix_criteria": "Change `exp ** base` to `base ** exp`.",
        "func_name": "power",
        "fixed_body": """\
def power(base: float, exp: float) -> float:
    \"\"\"Return base raised to the power exp.\"\"\"
    return float(base ** exp)
""",
        "buggy_body": """\
def power(base: float, exp: float) -> float:
    \"\"\"Return base raised to the power exp.\"\"\"
    return float(exp ** base)
""",
    },
    {
        "bug_id": "BUG_SUBTRACT_SIGN",
        "title": "subtract() returns b - a instead of a - b",
        "domain": "arithmetic",
        "description": (
            "The `subtract` function computes `b - a` instead of `a - b`, "
            "negating the result for non-zero differences."
        ),
        "repro": "Call `subtract(10, 3)` — returns `-7` instead of `7`.",
        "expected": "`subtract(10, 3)` returns `7.0`",
        "actual": "`subtract(10, 3)` returns `-7.0`",
        "edge_cases": [
            "subtract(5, 5) returns 0.0 (coincidentally correct)",
            "subtract(0, 5) should return -5.0 not 5.0",
            "subtract(3, 10) should return -7.0 not 7.0",
        ],
        "fix_criteria": "Change `b - a` to `a - b`.",
        "func_name": "subtract",
        "fixed_body": """\
def subtract(a: float, b: float) -> float:
    \"\"\"Return a minus b.\"\"\"
    return a - b
""",
        "buggy_body": """\
def subtract(a: float, b: float) -> float:
    \"\"\"Return a minus b.\"\"\"
    return b - a
""",
    },
    {
        "bug_id": "BUG_ABS_MISSING",
        "title": "is_positive() returns True for zero (boundary error)",
        "domain": "arithmetic",
        "description": (
            "The `is_positive` function uses `>= 0` (non-negative) instead of `> 0`, "
            "incorrectly classifying zero as positive."
        ),
        "repro": "Call `is_positive(0)` — returns `True` instead of `False`.",
        "expected": "`is_positive(0)` returns `False`",
        "actual": "`is_positive(0)` returns `True`",
        "edge_cases": [
            "is_positive(1) should return True",
            "is_positive(-1) should return False",
            "is_positive(0.0001) should return True",
        ],
        "fix_criteria": "Change `>= 0` to `> 0`.",
        "func_name": "is_positive",
        "fixed_body": """\
def is_positive(value: float) -> bool:
    \"\"\"Return True if value is strictly positive (> 0).\"\"\"
    return value > 0
""",
        "buggy_body": """\
def is_positive(value: float) -> bool:
    \"\"\"Return True if value is strictly positive (> 0).\"\"\"
    return value >= 0
""",
    },
    {
        "bug_id": "BUG_FACTORIAL_BASE",
        "title": "factorial() returns 0 for factorial(0) instead of 1",
        "domain": "arithmetic",
        "description": (
            "The `factorial` function uses `n < 1` as its base case, returning `0` "
            "when `n == 0` instead of the correct value of `1`."
        ),
        "repro": "Call `factorial(0)` — returns `0` instead of `1`.",
        "expected": "`factorial(0)` returns `1`",
        "actual": "`factorial(0)` returns `0`",
        "edge_cases": [
            "factorial(1) should return 1",
            "factorial(5) should return 120",
            "factorial(3) should return 6",
        ],
        "fix_criteria": "Change base case condition from `if n < 1` to `if n <= 0` and return `1`.",
        "func_name": "factorial",
        "fixed_body": """\
def factorial(n: int) -> int:
    \"\"\"Return n! for non-negative integer n.\"\"\"
    if n < 0:
        raise ValueError("factorial of negative number")
    if n == 0:
        return 1
    return n * factorial(n - 1)
""",
        "buggy_body": """\
def factorial(n: int) -> int:
    \"\"\"Return n! for non-negative integer n.\"\"\"
    if n < 0:
        raise ValueError("factorial of negative number")
    if n < 1:
        return 0
    return n * factorial(n - 1)
""",
    },
    {
        "bug_id": "BUG_MODULO_SIGN",
        "title": "safe_mod() returns wrong sign for negative dividends",
        "domain": "arithmetic",
        "description": (
            "The `safe_mod` function uses Python's `%` for modulo, which follows "
            "the sign of the divisor. The spec requires C-style modulo (sign of dividend). "
            "For `safe_mod(-7, 3)`, the result should be `-1` but Python returns `2`."
        ),
        "repro": "Call `safe_mod(-7, 3)` — returns `2` instead of `-1`.",
        "expected": "`safe_mod(-7, 3)` returns `-1`",
        "actual": "`safe_mod(-7, 3)` returns `2`",
        "edge_cases": [
            "safe_mod(7, 3) should return 1 (positive — both agree)",
            "safe_mod(-6, 3) should return 0",
            "safe_mod(7, -3) should return 1",
        ],
        "fix_criteria": "Use `int(a) - int(b) * int(a / b)` (truncation-based modulo).",
        "func_name": "safe_mod",
        "fixed_body": """\
def safe_mod(a: int, b: int) -> int:
    \"\"\"C-style modulo: result has sign of dividend.\"\"\"
    if b == 0:
        raise ValueError("modulo_by_zero")
    return int(a) - int(b) * int(a / b)
""",
        "buggy_body": """\
def safe_mod(a: int, b: int) -> int:
    \"\"\"C-style modulo: result has sign of dividend.\"\"\"
    if b == 0:
        raise ValueError("modulo_by_zero")
    return a % b
""",
    },
    {
        "bug_id": "BUG_AVERAGE_EMPTY",
        "title": "average() returns 0 instead of raising on empty list",
        "domain": "arithmetic",
        "description": (
            "The `average` function silently returns `0` when given an empty list "
            "instead of raising `ValueError`. This masks bugs in calling code."
        ),
        "repro": "Call `average([])` — returns `0` instead of raising `ValueError`.",
        "expected": "`average([])` raises `ValueError('empty_sequence')`",
        "actual": "`average([])` returns `0`",
        "edge_cases": [
            "average([5]) should return 5.0",
            "average([1, 2, 3]) should return 2.0",
            "average([0, 0]) should return 0.0 (zero average is valid)",
        ],
        "fix_criteria": "Add `if not values: raise ValueError('empty_sequence')` before computing sum.",
        "func_name": "average",
        "fixed_body": """\
def average(values: list) -> float:
    \"\"\"Return the arithmetic mean. Raises ValueError for empty list.\"\"\"
    if not values:
        raise ValueError("empty_sequence")
    return sum(values) / len(values)
""",
        "buggy_body": """\
def average(values: list) -> float:
    \"\"\"Return the arithmetic mean. Raises ValueError for empty list.\"\"\"
    if not values:
        return 0
    return sum(values) / len(values)
""",
    },
]

# ── Module template ────────────────────────────────────────────────────────────

MODULE_HEADER = '''\
"""
Calculator module — fixed implementation.

All bugs described in the bug report have been corrected.
Do NOT modify this file. Write regression tests in test_calculator.py.
"""
import math as _math

MAX_VALUE = 1e15

'''


def _build_calculator_module(selected_bugs: list[dict]) -> tuple[str, str]:
    """Return (fixed_module, buggy_modules_dict) where buggy is a dict bug_id->src."""
    # Collect all function bodies (fixed)
    fixed_parts = [MODULE_HEADER]
    seen_imports = set()
    for bug in selected_bugs:
        body = bug["fixed_body"]
        # Strip inline import lines if already included in header
        lines = []
        for line in body.splitlines(keepends=True):
            stripped = line.strip()
            if stripped.startswith("import math") or stripped.startswith("MAX_VALUE"):
                if stripped not in seen_imports:
                    seen_imports.add(stripped)
                # Always skip — already in header
                continue
            lines.append(line)
        fixed_parts.append("".join(lines) + "\n")

    fixed_module = "".join(fixed_parts)

    # Build one buggy module per bug (only that function is buggy, rest are fixed)
    buggy_modules = {}
    for target_bug in selected_bugs:
        parts = [MODULE_HEADER]
        for bug in selected_bugs:
            if bug["bug_id"] == target_bug["bug_id"]:
                body = bug["buggy_body"]
            else:
                body = bug["fixed_body"]
            lines = []
            for line in body.splitlines(keepends=True):
                stripped = line.strip()
                if stripped.startswith("import math") or stripped.startswith("MAX_VALUE"):
                    continue
                lines.append(line)
            parts.append("".join(lines) + "\n")
        buggy_modules[target_bug["bug_id"]] = "".join(parts)

    return fixed_module, buggy_modules


class Generator(TaskGenerator):
    task_id = "TEST2_regression"
    domain = "testing"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pick 3-5 bugs from pool, deterministically
        num_bugs = rng.randint(3, 5)
        bug_indices = rng.sample(list(range(len(BUG_POOL))), num_bugs)
        selected_bugs = [BUG_POOL[i] for i in bug_indices]

        # Build workspace files
        fixed_module, buggy_modules = _build_calculator_module(selected_bugs)

        workspace_files: dict[str, str] = {
            "calculator.py": fixed_module,
            "test_calculator.py": self._test_skeleton(selected_bugs),
        }

        # Add buggy variants for grader use (stored under buggy_variants/)
        for bug in selected_bugs:
            workspace_files[f"buggy_variants/{bug['bug_id']}.py"] = buggy_modules[bug["bug_id"]]

        spec_md = self._generate_spec(selected_bugs, seed)
        brief_md = self._generate_brief()

        expected = {
            "bug_ids": [b["bug_id"] for b in selected_bugs],
            "bug_count": num_bugs,
            "min_tests": num_bugs,
            "func_names": [b["func_name"] for b in selected_bugs],
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _test_skeleton(self, bugs: list[dict]) -> str:
        lines = [
            '"""Regression tests for the calculator module.',
            "",
            "Write tests that:",
            "  1. Pass on the fixed calculator.py in this directory.",
            "  2. Would FAIL if each reported bug were reintroduced.",
            '"""',
            "import pytest",
            "from calculator import (",
        ]
        for bug in bugs:
            lines.append(f"    {bug['func_name']},")
        lines.append(")")
        lines.append("")
        lines.append("")
        lines.append("# TODO: Write regression tests below.")
        lines.append("# Each bug in the spec should have at least one dedicated test.")
        lines.append("")
        for bug in bugs:
            lines.append(f"# {bug['bug_id']}: {bug['title']}")
            lines.append(f"# Repro: {bug['repro']}")
            lines.append(f"# Expected: {bug['expected']}")
            lines.append("")
        return "\n".join(lines) + "\n"

    def _generate_spec(self, bugs: list[dict], seed: int) -> str:
        bug_sections = []
        for idx, bug in enumerate(bugs, start=1):
            edge_bullets = "\n".join(f"  - {e}" for e in bug["edge_cases"])
            section = textwrap.dedent(f"""\
                ### Bug {idx}: {bug['title']} (`{bug['bug_id']}`)

                **Affected function**: `{bug['func_name']}()`

                **Description**: {bug['description']}

                **Reproduction steps**:
                {bug['repro']}

                **Expected behaviour**: {bug['expected']}

                **Actual (buggy) behaviour**: {bug['actual']}

                **Edge cases to cover**:
                {edge_bullets}

                **Fix verification criteria**: {bug['fix_criteria']}
            """)
            bug_sections.append(section)

        bugs_text = "\n".join(bug_sections)
        num_bugs = len(bugs)
        func_list = ", ".join(f"`{b['func_name']}`" for b in bugs)

        return textwrap.dedent(f"""\
            # TEST2: Regression Tests from Bug Report

            ## Context

            The calculator module (`calculator.py`) previously had **{num_bugs} bugs**.
            All bugs have since been fixed. Your job is to write **regression tests** that:

            1. Pass against the current (fixed) `calculator.py`.
            2. Would **fail** if any of the described bugs were reintroduced.

            The module exposes these functions: {func_list}.

            ## Bug Report (Seed {seed})

            {bugs_text}

            ## Deliverables

            - `test_calculator.py` with pytest tests (minimum {num_bugs} test functions — one per bug).
            - Tests must use `assert` statements or `pytest.raises` (no print-only checks).
            - Tests must run cleanly with `python -m pytest test_calculator.py`.
            - Do **not** hardcode implementation internals — test through the public API only.

            ## Grading

            - **Check 1**: `test_calculator.py` exists.
            - **Checks 2-{num_bugs+1}**: Each bug's regression test detects that bug when reintroduced.
            - **Check {num_bugs+2}**: All tests pass on the fixed `calculator.py`.
            - **Check {num_bugs+3}**: Test count >= {num_bugs}.
            - **Check {num_bugs+4}**: Tests use assertions (not print-only).
            - **Check {num_bugs+5}**: `pytest` exits with code 0 on the fixed module.
        """)

    def _generate_brief(self) -> str:
        return textwrap.dedent("""\
            # TEST2: Regression Tests from Bug Report (Brief)

            Write regression tests for the reported bugs in the calculator module.
            The Planner has the bug details.

            - File to write: `test_calculator.py`
            - Run with: `python -m pytest test_calculator.py`
            - Tests must pass on the provided `calculator.py` (bugs already fixed).
            - Each reported bug must have at least one test that would catch it if reintroduced.
        """)
