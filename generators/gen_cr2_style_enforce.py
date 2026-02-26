"""
Parameterized generator for CR2: Style Guide Enforcement.

Each seed produces:
- A different code domain (data_utils, api_client, parser_lib, test_helpers)
- A Python source file with 8-15 deliberate style violations covering:
    - camelCase function/variable names that should be snake_case
    - lowercase class names that should be PascalCase
    - Public functions missing type hints
    - Missing or malformed docstrings (not Google style)
    - Wildcard imports
    - Wrong import order (stdlib mixed with third-party, or third-party before stdlib)
    - Lines exceeding 88 characters
    - Missing trailing commas in multi-line collections
- spec.md: complete style guide with examples (Planner-visible)
- brief.md: vague "fix style issues" description (Executor-visible)

TNI Pattern E (Compliance Rules):
- Brief: "The code has style violations. Fix them to match our coding standards."
- Spec: Complete style guide with rules and examples. Planner relays the exact
  rules to the Executor so the Executor knows precisely what to fix.
- The code must remain functionally correct after all style fixes.
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ---------------------------------------------------------------------------
# Domain definitions
# ---------------------------------------------------------------------------

DOMAINS = [
    {
        "name": "data_utils",
        "title": "Data Utilities Library",
        "description": "provides data transformation and validation helpers",
        "module_file": "data_utils.py",
        "class_bad": "dataProcessor",        # should be DataProcessor
        "class_good": "DataProcessor",
        "class2_bad": "recordValidator",      # should be RecordValidator
        "class2_good": "RecordValidator",
        "noun": "record",
        "noun_plural": "records",
        "field1": "name",
        "field2": "value",
        "field3": "category",
    },
    {
        "name": "api_client",
        "title": "API Client Library",
        "description": "handles HTTP requests, response parsing, and retry logic",
        "module_file": "api_client.py",
        "class_bad": "httpClient",            # should be HttpClient
        "class_good": "HttpClient",
        "class2_bad": "responseParser",       # should be ResponseParser
        "class2_good": "ResponseParser",
        "noun": "request",
        "noun_plural": "requests",
        "field1": "url",
        "field2": "status",
        "field3": "headers",
    },
    {
        "name": "parser_lib",
        "title": "Parser Utilities Library",
        "description": "parses structured text formats into Python objects",
        "module_file": "parser_lib.py",
        "class_bad": "tokenParser",           # should be TokenParser
        "class_good": "TokenParser",
        "class2_bad": "astBuilder",           # should be AstBuilder
        "class2_good": "AstBuilder",
        "noun": "token",
        "noun_plural": "tokens",
        "field1": "kind",
        "field2": "text",
        "field3": "position",
    },
    {
        "name": "test_helpers",
        "title": "Test Helper Utilities",
        "description": "provides fixtures, stubs, and assertion helpers for tests",
        "module_file": "test_helpers.py",
        "class_bad": "mockFactory",           # should be MockFactory
        "class_good": "MockFactory",
        "class2_bad": "assertionHelper",      # should be AssertionHelper
        "class2_good": "AssertionHelper",
        "noun": "fixture",
        "noun_plural": "fixtures",
        "field1": "key",
        "field2": "payload",
        "field3": "metadata",
    },
]

# ---------------------------------------------------------------------------
# Violation variant pools
# Each tuple: (bad_fn_name, good_fn_name, description_of_violation)
# ---------------------------------------------------------------------------

# camelCase function names that must become snake_case
CAMEL_FN_VARIANTS = [
    ("parseInput",       "parse_input",       "function name is camelCase, must be snake_case"),
    ("loadData",         "load_data",         "function name is camelCase, must be snake_case"),
    ("buildOutput",      "build_output",      "function name is camelCase, must be snake_case"),
    ("fetchRecords",     "fetch_records",     "function name is camelCase, must be snake_case"),
    ("formatValue",      "format_value",      "function name is camelCase, must be snake_case"),
    ("validateSchema",   "validate_schema",   "function name is camelCase, must be snake_case"),
    ("normalizeText",    "normalize_text",    "function name is camelCase, must be snake_case"),
    ("computeHash",      "compute_hash",      "function name is camelCase, must be snake_case"),
    ("mergeResults",     "merge_results",     "function name is camelCase, must be snake_case"),
    ("filterItems",      "filter_items",      "function name is camelCase, must be snake_case"),
]

# camelCase local variable names that must become snake_case
CAMEL_VAR_VARIANTS = [
    ("inputData",    "input_data"),
    ("outputList",   "output_list"),
    ("itemCount",    "item_count"),
    ("maxRetries",   "max_retries"),
    ("rawBytes",     "raw_bytes"),
    ("numErrors",    "num_errors"),
    ("tempBuffer",   "temp_buffer"),
    ("isValid",      "is_valid"),
]

# Import order violation pairs: (bad_block, good_block, description)
# All variants use stdlib-only imports so the generated module can actually be imported.
# The violation is that imports are not in alphabetical order within the stdlib group,
# or that two logically separate import groups lack a blank line between them.
IMPORT_VARIANTS = [
    (
        "import os\nimport json\nimport sys\nimport re\nimport collections",
        "import collections\nimport json\nimport os\nimport re\nimport sys",
        "stdlib imports are not in alphabetical order",
    ),
    (
        "import datetime\nimport pathlib\nimport collections\nimport hashlib",
        "import collections\nimport datetime\nimport hashlib\nimport pathlib",
        "stdlib imports are not in alphabetical order",
    ),
    (
        "import typing\nimport hashlib\nimport itertools\nimport functools",
        "import functools\nimport hashlib\nimport itertools\nimport typing",
        "stdlib imports are not in alphabetical order",
    ),
    (
        "import string\nimport math\nimport functools\nimport os\nimport re",
        "import functools\nimport math\nimport os\nimport re\nimport string",
        "stdlib imports are not in alphabetical order",
    ),
]


class Generator(TaskGenerator):
    task_id = "CR2_style_enforce"
    domain = "code_review"
    difficulty = "easy"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        domain = DOMAINS[rng.randint(0, len(DOMAINS) - 1)]

        # Pick 2 camelCase function violations
        fn_violations = rng.sample(CAMEL_FN_VARIANTS, 2)
        fn1_bad, fn1_good, fn1_desc = fn_violations[0]
        fn2_bad, fn2_good, fn2_desc = fn_violations[1]

        # Pick 2 camelCase variable violations
        var_violations = rng.sample(CAMEL_VAR_VARIANTS, 2)
        var1_bad, var1_good = var_violations[0]
        var2_bad, var2_good = var_violations[1]

        # Pick import order violation
        imp = IMPORT_VARIANTS[rng.randint(0, len(IMPORT_VARIANTS) - 1)]
        bad_imports, good_imports, import_desc = imp

        # Line length: generate a long comment line (>88 chars)
        long_line_len = rng.randint(95, 115)
        long_comment = "# " + ("This is a very long comment that documents important behaviour of this module in detail."[:long_line_len - 2])
        # Ensure it's actually over 88
        while len(long_comment) <= 88:
            long_comment += " detail"

        module_file = domain["module_file"]

        workspace_files = {
            module_file: self._generate_module(
                domain, fn1_bad, fn1_good, fn2_bad, fn2_good,
                var1_bad, var1_good, var2_bad, var2_good,
                bad_imports, long_comment,
            ),
            "tests/__init__.py": "",
            "tests/test_module.py": self._generate_tests(
                domain, fn1_good, fn2_good, module_file,
            ),
        }

        expected = {
            "domain": domain["name"],
            "module_file": module_file,
            "class_bad": domain["class_bad"],
            "class_good": domain["class_good"],
            "class2_bad": domain["class2_bad"],
            "class2_good": domain["class2_good"],
            "fn1_bad": fn1_bad,
            "fn1_good": fn1_good,
            "fn2_bad": fn2_bad,
            "fn2_good": fn2_good,
            "var1_bad": var1_bad,
            "var1_good": var1_good,
            "var2_bad": var2_bad,
            "var2_good": var2_good,
            "import_desc": import_desc,
            "good_imports": good_imports,
            "max_line_length": 88,
        }

        spec_md = self._generate_spec(
            domain, fn1_bad, fn1_good, fn1_desc, fn2_bad, fn2_good, fn2_desc,
            var1_bad, var1_good, var2_bad, var2_good,
            bad_imports, good_imports, import_desc, long_comment, module_file,
        )
        brief_md = self._generate_brief(domain, module_file)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ------------------------------------------------------------------
    # Workspace file generation
    # ------------------------------------------------------------------

    def _generate_module(
        self,
        domain: dict,
        fn1_bad: str, fn1_good: str,
        fn2_bad: str, fn2_good: str,
        var1_bad: str, var1_good: str,
        var2_bad: str, var2_good: str,
        bad_imports: str,
        long_comment: str,
    ) -> str:
        d = domain
        noun = d["noun"]
        plural = d["noun_plural"]
        f1 = d["field1"]
        f2 = d["field2"]
        f3 = d["field3"]
        cls_bad = d["class_bad"]
        cls2_bad = d["class2_bad"]
        cls_good = d["class_good"]
        cls2_good = d["class2_good"]

        # Build module with deliberate violations:
        # 1. Wrong import order (bad_imports)
        # 2. Wildcard import
        # 3. class names in lowercase/camelCase (not PascalCase)
        # 4. Two camelCase function names
        # 5. Two camelCase local variable names
        # 6. Missing type hints on public functions
        # 7. Missing/bad docstrings
        # 8. A line exceeding 88 characters
        # 9. Missing trailing comma in multi-line dict/list

        return f'''"""{d["title"]}

This module {d["description"]}.
"""
{bad_imports}
from typing import *


{long_comment}


class {cls_bad}:
    """Processes {plural} from various sources."""

    def __init__(self, config):
        self.config = config
        self.results = []

    def {fn1_bad}(self, raw):
        """Load {plural} from raw input.

        Args:
            raw: The raw input data.

        Returns:
            A list of processed {noun} dicts.
        """
        {var1_bad} = []
        for item in raw:
            processed = {{
                "{f1}": str(item.get("{f1}", "")),
                "{f2}": item.get("{f2}"),
                "{f3}": item.get("{f3}", "default")
            }}
            {var1_bad}.append(processed)
        return {var1_bad}

    def process(self, {plural}):
        # No docstring here - this is also a violation
        # Missing type hints on public method
        {var2_bad} = 0
        for {noun} in {plural}:
            if {noun}.get("{f2}") is not None:
                {var2_bad} += 1
        return {var2_bad}


class {cls2_bad}:
    """Validates {plural} against a schema."""

    def validate(self, {noun}):
        # Missing type hints
        # Bad docstring style
        """validate a {noun} dict. returns True if valid."""
        required = [
            "{f1}",
            "{f2}",
            "{f3}"
        ]
        return all(k in {noun} for k in required)


def {fn2_bad}(items, threshold):
    # Missing type hints and Google-style docstring
    """filter items above threshold"""
    return [x for x in items if x.get("{f2}", 0) > threshold]


def _internal_helper(value):
    """Internal helper — no type hints required for private functions."""
    return str(value).strip().lower()
'''

    def _generate_tests(
        self,
        domain: dict,
        fn1_good: str,
        fn2_good: str,
        module_file: str,
    ) -> str:
        noun = domain["noun"]
        plural = domain["noun_plural"]
        f1 = domain["field1"]
        f2 = domain["field2"]
        f3 = domain["field3"]
        cls_good = domain["class_good"]
        cls2_good = domain["class2_good"]
        mod = module_file.replace(".py", "")

        return f'''"""Tests for {domain["title"]}.

These tests verify correctness BEFORE and AFTER style fixes.
They must all pass without modification.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import {mod}


@pytest.fixture
def sample_{plural}():
    return [
        {{"{f1}": "alpha", "{f2}": 10, "{f3}": "cat_a"}},
        {{"{f1}": "beta",  "{f2}": 5,  "{f3}": "cat_b"}},
        {{"{f1}": "gamma", "{f2}": 20, "{f3}": "cat_a"}},
    ]


def test_{fn1_good}(sample_{plural}):
    processor = {mod}.{cls_good}(config={{}})
    result = processor.{fn1_good}(sample_{plural})
    assert len(result) == 3
    assert all("{f1}" in r for r in result)


def test_{fn1_good}_empty():
    processor = {mod}.{cls_good}(config={{}})
    result = processor.{fn1_good}([])
    assert result == []


def test_process_count(sample_{plural}):
    processor = {mod}.{cls_good}(config={{}})
    count = processor.process(sample_{plural})
    assert count == 3


def test_process_count_with_none():
    processor = {mod}.{cls_good}(config={{}})
    {plural}_with_none = [
        {{"{f1}": "x", "{f2}": None, "{f3}": "c"}},
        {{"{f1}": "y", "{f2}": 1,    "{f3}": "c"}},
    ]
    assert processor.process({plural}_with_none) == 1


def test_validate_valid(sample_{plural}):
    validator = {mod}.{cls2_good}()
    assert validator.validate(sample_{plural}[0]) is True


def test_validate_missing_field():
    validator = {mod}.{cls2_good}()
    assert validator.validate({{"{f1}": "x", "{f2}": 1}}) is False


def test_{fn2_good}(sample_{plural}):
    result = {mod}.{fn2_good}(sample_{plural}, threshold=8)
    values = [r["{f2}"] for r in result]
    assert set(values) == {{10, 20}}


def test_{fn2_good}_no_results(sample_{plural}):
    result = {mod}.{fn2_good}(sample_{plural}, threshold=100)
    assert result == []


def test_{fn2_good}_all_results(sample_{plural}):
    result = {mod}.{fn2_good}(sample_{plural}, threshold=-1)
    assert len(result) == 3
'''

    # ------------------------------------------------------------------
    # Spec and Brief
    # ------------------------------------------------------------------

    def _generate_spec(
        self,
        domain: dict,
        fn1_bad: str, fn1_good: str, fn1_desc: str,
        fn2_bad: str, fn2_good: str, fn2_desc: str,
        var1_bad: str, var1_good: str,
        var2_bad: str, var2_good: str,
        bad_imports: str, good_imports: str, import_desc: str,
        long_comment: str,
        module_file: str,
    ) -> str:
        cls_bad = domain["class_bad"]
        cls_good = domain["class_good"]
        cls2_bad = domain["class2_bad"]
        cls2_good = domain["class2_good"]

        return f"""# CR2: Style Guide Enforcement

## Overview

The `{module_file}` file contains multiple style violations that must be fixed
to conform to the project's coding standard.  The code is **functionally
correct** — do not change logic, only style.

All existing tests (`tests/test_module.py`) must continue to pass after fixes.

---

## Style Guide

### 1. Naming Conventions

#### Functions and Variables — `snake_case`

All function names and local variable names must use `snake_case`.

```python
# WRONG
def parseInput(raw):
    inputData = []

# CORRECT
def parse_input(raw):
    input_data = []
```

#### Classes — `PascalCase`

All class names must use `PascalCase` (also called UpperCamelCase).

```python
# WRONG
class dataProcessor:
    ...

class recordValidator:
    ...

# CORRECT
class DataProcessor:
    ...

class RecordValidator:
    ...
```

---

### 2. Maximum Line Length — 88 Characters

No line may exceed 88 characters.  Break long lines using implicit continuation
inside parentheses, brackets, or braces.

```python
# WRONG (> 88 chars)
# This is a very long comment that documents important behaviour of this module in detail and goes on far too long.

# CORRECT (wrapped or shortened)
# This is a comment that documents important behaviour of this module.
```

---

### 3. Docstrings — Google Style

Every **public** function and method must have a Google-style docstring.
Private functions (names starting with `_`) are exempt.

Google-style docstring format:

```python
def function_name(arg1: str, arg2: int) -> list:
    \"\"\"One-line summary ending with a period.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.

    Returns:
        Description of the return value.
    \"\"\"
```

Rules:
- First line is a one-line summary ending with a period.
- Blank line after the summary if there are Args/Returns sections.
- Args section lists each parameter with a colon and description.
- Returns section describes the return value.
- Raises section (if needed) lists exceptions.

---

### 4. Import Order

Imports must be in alphabetical order within each group, with groups separated
by a blank line:

1. Standard library imports (alphabetical)
2. Third-party imports (alphabetical)
3. Local/first-party imports (alphabetical)

```python
# WRONG — stdlib imports are not alphabetically ordered
{bad_imports}

# CORRECT — stdlib imports in alphabetical order
{good_imports}
```

---

### 5. No Wildcard Imports

Wildcard imports (`from module import *`) are forbidden.

```python
# WRONG
from typing import *

# CORRECT
from typing import Any, Dict, List, Optional
```

---

### 6. Type Hints on Public Functions

Every **public** function and method (not starting with `_`) must have type
annotations on all parameters and the return type.

```python
# WRONG — no type hints
def load_records(self, raw):
    ...

def filter_items(items, threshold):
    ...

# CORRECT — full type hints
def load_records(self, raw: list) -> list:
    ...

def filter_items(items: list, threshold: float) -> list:
    ...
```

---

### 7. Trailing Commas in Multi-line Collections

When a collection (dict, list, tuple, function call) spans multiple lines with
one element per line, each element — including the last — must have a trailing
comma.

```python
# WRONG — missing trailing comma on last element
required = [
    "field_a",
    "field_b",
    "field_c"
]

# CORRECT — trailing comma after last element
required = [
    "field_a",
    "field_b",
    "field_c",
]
```

---

## Violations in `{module_file}`

The file contains the following violations that must be fixed:

| # | Category | What to Fix |
|---|----------|-------------|
| 1 | Class naming | `{cls_bad}` → `{cls_good}` (must be PascalCase) |
| 2 | Class naming | `{cls2_bad}` → `{cls2_good}` (must be PascalCase) |
| 3 | Function naming | `{fn1_bad}` → `{fn1_good}` ({fn1_desc}) |
| 4 | Function naming | `{fn2_bad}` → `{fn2_good}` ({fn2_desc}) |
| 5 | Variable naming | `{var1_bad}` → `{var1_good}` (local variable, must be snake_case) |
| 6 | Variable naming | `{var2_bad}` → `{var2_good}` (local variable, must be snake_case) |
| 7 | Wildcard import | `from typing import *` → explicit names |
| 8 | Import order | {import_desc} |
| 9 | Line length | Long comment line exceeds 88 characters — shorten it |
| 10 | Docstring style | `process` method missing docstring entirely |
| 11 | Docstring style | `{cls2_good}.validate` has a one-line non-Google docstring — convert to Google style |
| 12 | Docstring style | `{fn2_good}` has a one-line non-Google docstring — convert to Google style |
| 13 | Type hints | `{cls_good}.{fn1_good}` missing parameter and return type hints |
| 14 | Type hints | `{cls_good}.process` missing parameter and return type hints |
| 15 | Type hints | `{cls2_good}.validate` missing parameter and return type hints |
| 16 | Type hints | `{fn2_good}` missing parameter and return type hints |
| 17 | Trailing comma | Multi-line list in `validate` method is missing trailing comma |
| 18 | Trailing comma | Multi-line dict in `{fn1_good}` is missing trailing comma |

## Constraints

- Do **not** change the logic of any function.
- Do **not** modify `tests/test_module.py`.
- All tests must pass after fixes.
- Private function `_internal_helper` is exempt from type hints and docstring rules.

## Deliverables

1. `{module_file}` with all style violations corrected.
2. `tests/test_module.py` passing without modification.
3. Verifier writes `attestation.json` with `verdict: pass` once all checks pass.
"""

    def _generate_brief(self, domain: dict, module_file: str) -> str:
        return f"""# CR2: Style Guide Enforcement (Brief)

## Your Task

The `{module_file}` in your workspace has style violations that must be fixed
to comply with the project's coding standards.

The code is **functionally correct** — do **not** change its logic.

## What You Know

- The file is `{module_file}`.
- It contains naming, import, docstring, type hint, line length, and formatting issues.
- The full style guide and the exact list of violations have been provided to the Planner.
- Follow the Planner's instructions precisely — they specify every violation and its fix.
- `tests/test_module.py` must pass without modification after your changes.
- Do **not** modify `tests/test_module.py`.
- The Verifier will check your fixes against the style guide rules.
"""
