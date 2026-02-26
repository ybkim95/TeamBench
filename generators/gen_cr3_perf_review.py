"""
Parameterized generator for CR3: Performance Optimization from Profiler Report.

Each seed produces:
- A different application domain (data processing, text analysis, graph traversal,
  sorting/filtering, matrix operations)
- Working but slow Python code with 3 embedded performance hotspots:
    Hotspot 1: O(n^2) nested loop that should use a dict/set lookup
    Hotspot 2: Repeated expensive computation that should be cached
    Hotspot 3: Building a full list where a generator suffices
- A profiler_report.txt in the workspace showing timing data for 3 functions
  (with function names and call counts, but NOT the fix strategy)
- A performance budget embedded in the spec

TNI driver (Pattern A + C — hidden constraints + multi-criteria):
- Brief: "The application is too slow. Optimize it. The Planner has the profiler report."
- Spec: Profiler report with hotspots AND fix strategies + performance budget
- The Executor cannot see the fix strategies or budget — only the Planner can.
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ---------------------------------------------------------------------------
# Domain definitions
# ---------------------------------------------------------------------------

DOMAINS = [
    {
        "name": "data_processing",
        "title": "Data Record Processor",
        "description": "processes records from an in-memory dataset",
        "module_file": "processor.py",
        "data_noun": "record",
        "data_noun_plural": "records",
        "key_field": "id",
        "value_field": "score",
        "tag_field": "category",
    },
    {
        "name": "text_analysis",
        "title": "Text Corpus Analyser",
        "description": "analyses word frequencies and token patterns in text corpora",
        "module_file": "analyser.py",
        "data_noun": "document",
        "data_noun_plural": "documents",
        "key_field": "doc_id",
        "value_field": "word_count",
        "tag_field": "topic",
    },
    {
        "name": "graph_traversal",
        "title": "Graph Path Finder",
        "description": "finds paths and computes metrics over adjacency lists",
        "module_file": "graph.py",
        "data_noun": "node",
        "data_noun_plural": "nodes",
        "key_field": "node_id",
        "value_field": "weight",
        "tag_field": "group",
    },
    {
        "name": "sorting_filtering",
        "title": "Inventory Filter Engine",
        "description": "filters and ranks inventory items by configurable criteria",
        "module_file": "filter_engine.py",
        "data_noun": "item",
        "data_noun_plural": "items",
        "key_field": "sku",
        "value_field": "price",
        "tag_field": "department",
    },
    {
        "name": "matrix_ops",
        "title": "Matrix Statistics Engine",
        "description": "computes statistical metrics over numeric matrices",
        "module_file": "matrix_stats.py",
        "data_noun": "row",
        "data_noun_plural": "rows",
        "key_field": "row_id",
        "value_field": "magnitude",
        "tag_field": "label",
    },
]

# Hotspot 1 variants: O(n^2) linear search -> dict lookup
# (slow_fn_name, fast_strategy_description)
HOTSPOT1_VARIANTS = [
    ("find_duplicates",        "use a seen-set (set lookup) instead of scanning results list"),
    ("find_matching_pairs",    "build a value->index dict once; look up complement in O(1)"),
    ("find_common_keys",       "convert second list to a set; use set intersection"),
    ("locate_by_attribute",    "build a dict keyed by attribute once; look up directly"),
    ("cross_reference",        "build a lookup dict from reference list; avoid inner loop"),
]

# Hotspot 2 variants: repeated computation -> cache/memoize
# (slow_fn_name, fast_strategy_description)
HOTSPOT2_VARIANTS = [
    ("compute_signature",  "cache result in a dict keyed by input; compute only on first call"),
    ("compute_checksum",   "memoize with a module-level dict; skip recomputation on repeat input"),
    ("compute_metric",     "cache in _cache dict; return cached value when key present"),
    ("compute_hash",       "use functools.lru_cache or a manual dict cache"),
    ("compute_score",      "store result in _memo dict; guard with 'if key in _memo' check"),
]

# Hotspot 3 variants: full list build -> generator
# (slow_fn_name, fast_strategy_description)
HOTSPOT3_VARIANTS = [
    ("collect_values",   "use a generator expression instead of list comprehension"),
    ("extract_fields",   "yield items one at a time instead of building a full list"),
    ("gather_results",   "return a generator with 'yield from' instead of list append loop"),
    ("enumerate_items",  "use (x for x in ...) generator; caller controls materialisation"),
    ("produce_output",   "replace list accumulation with a generator function using yield"),
]

# Performance budgets (ms) per domain — tight enough to require fixes, loose enough to be achievable
BUDGETS_MS = [150, 200, 250, 120, 180]


class Generator(TaskGenerator):
    task_id = "CR3_perf_review"
    domain = "code_review"
    difficulty = "medium"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        domain = DOMAINS[rng.randint(0, len(DOMAINS) - 1)]
        h1_name, h1_strategy = HOTSPOT1_VARIANTS[rng.randint(0, len(HOTSPOT1_VARIANTS) - 1)]
        h2_name, h2_strategy = HOTSPOT2_VARIANTS[rng.randint(0, len(HOTSPOT2_VARIANTS) - 1)]
        h3_name, h3_strategy = HOTSPOT3_VARIANTS[rng.randint(0, len(HOTSPOT3_VARIANTS) - 1)]
        budget_ms = BUDGETS_MS[rng.randint(0, len(BUDGETS_MS) - 1)]

        # Profiler timings — slow version timings shown in report
        h1_ms  = rng.randint(400, 900)
        h1_calls = rng.randint(500, 2000)
        h2_ms  = rng.randint(300, 700)
        h2_calls = rng.randint(1000, 5000)
        h3_ms  = rng.randint(200, 500)
        h3_calls = rng.randint(200, 800)
        total_slow_ms = h1_ms + h2_ms + h3_ms

        module_file = domain["module_file"]

        workspace_files = {
            module_file: self._generate_module(domain, h1_name, h2_name, h3_name),
            "profiler_report.txt": self._generate_profiler_report(
                domain, h1_name, h1_ms, h1_calls,
                h2_name, h2_ms, h2_calls,
                h3_name, h3_ms, h3_calls,
                total_slow_ms, budget_ms,
            ),
            "tests/__init__.py": "",
            "tests/test_module.py": self._generate_tests(domain, module_file, h1_name, h2_name, h3_name),
        }

        expected = {
            "domain": domain["name"],
            "module_file": module_file,
            "hotspot1_fn": h1_name,
            "hotspot2_fn": h2_name,
            "hotspot3_fn": h3_name,
            "hotspot1_strategy": h1_strategy,
            "hotspot2_strategy": h2_strategy,
            "hotspot3_strategy": h3_strategy,
            "budget_ms": budget_ms,
            "total_slow_ms": total_slow_ms,
        }

        spec_md = self._generate_spec(
            domain, module_file,
            h1_name, h1_strategy, h1_ms, h1_calls,
            h2_name, h2_strategy, h2_ms, h2_calls,
            h3_name, h3_strategy, h3_ms, h3_calls,
            total_slow_ms, budget_ms,
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
    # Workspace generation
    # ------------------------------------------------------------------

    def _generate_module(
        self,
        domain: dict,
        h1_name: str,
        h2_name: str,
        h3_name: str,
    ) -> str:
        d = domain
        noun = d["data_noun"]
        plural = d["data_noun_plural"]
        key = d["key_field"]
        val = d["value_field"]
        tag = d["tag_field"]

        return f'''"""
{d["title"]}

This module {d["description"]}.
It is functionally correct but has three performance hotspots identified
by the profiler.  Do NOT change the public API or alter correctness.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Hotspot 1 — O(n^2) linear scan
# ---------------------------------------------------------------------------

def {h1_name}(
    {plural}: List[Dict[str, Any]],
    reference: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return every {noun} whose {key!r} appears in *reference*.

    Performance note: currently uses a nested O(n*m) scan.
    """
    matches = []
    for {noun} in {plural}:
        for ref in reference:
            if {noun}["{key}"] == ref["{key}"]:
                matches.append({noun})
                break
    return matches


# ---------------------------------------------------------------------------
# Hotspot 2 — repeated expensive computation without caching
# ---------------------------------------------------------------------------

def {h2_name}(value: float) -> float:
    """Compute an expensive derived metric for *value*.

    The same input may be supplied thousands of times; the result is
    deterministic but the computation is artificially heavy.
    """
    # Simulate expensive work (sum of harmonic series as proxy)
    result = 0.0
    n = max(1, int(abs(value) * 100) + 1)
    for i in range(1, n + 1):
        result += math.sqrt(value * i) / (i * i)
    return result


# ---------------------------------------------------------------------------
# Hotspot 3 — builds full list when a generator would suffice
# ---------------------------------------------------------------------------

def {h3_name}(
    {plural}: Iterable[Dict[str, Any]],
    threshold: float,
) -> List[float]:
    """Return {val} values for all {plural} whose {val} exceeds *threshold*.

    Currently materialises a complete list in memory; callers only ever
    iterate the result once.
    """
    results = []
    for {noun} in {plural}:
        v = float({noun}["{val}"])
        if v > threshold:
            results.append(v)
    return results


# ---------------------------------------------------------------------------
# Supporting helpers (do NOT modify these)
# ---------------------------------------------------------------------------

def load_{plural}(n: int = 500) -> List[Dict[str, Any]]:
    """Generate *n* synthetic {noun} dicts for benchmarking."""
    return [
        {{
            "{key}": i,
            "{val}": float(i % 97) + 0.5,
            "{tag}": f"group_{{i % 10}}",
        }}
        for i in range(n)
    ]


def run_benchmark() -> float:
    """Run all three hotspot functions and return elapsed time in ms."""
    {plural} = load_{plural}(500)
    reference = load_{plural}(250)
    threshold = 30.0

    t0 = time.perf_counter()
    {h1_name}({plural}, reference)
    for r in {plural}:
        {h2_name}(r["{val}"])
    list({h3_name}({plural}, threshold))
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return elapsed_ms
'''

    def _generate_profiler_report(
        self,
        domain: dict,
        h1_name: str, h1_ms: int, h1_calls: int,
        h2_name: str, h2_ms: int, h2_calls: int,
        h3_name: str, h3_ms: int, h3_calls: int,
        total_ms: int, budget_ms: int,
    ) -> str:
        return f"""Performance Profiler Report
===========================

Module  : {domain["module_file"]}
Profile : cProfile (cumulative time, top functions)
Run at  : 2025-03-10 09:14:02 UTC
Dataset : 500 {domain["data_noun_plural"]}, 250 reference entries

SUMMARY
-------
Total elapsed      : {total_ms} ms
Performance budget : {budget_ms} ms
Status             : OVER BUDGET  ({total_ms - budget_ms} ms above target)

TOP HOTSPOTS (by cumulative time)
----------------------------------
Rank  Function              Calls     Cumulative (ms)   % of total
----  --------------------  --------  ----------------  ----------
1     {h1_name:<20}  {h1_calls:<8}  {h1_ms:<16}  {round(100*h1_ms/max(1,total_ms))}%
2     {h2_name:<20}  {h2_calls:<8}  {h2_ms:<16}  {round(100*h2_ms/max(1,total_ms))}%
3     {h3_name:<20}  {h3_calls:<8}  {h3_ms:<16}  {round(100*h3_ms/max(1,total_ms))}%

NOTES
-----
All three functions are functionally correct.
Optimization must preserve observable behaviour (return values, types).
The detailed fix strategies have been shared with the team lead.
"""

    def _generate_tests(
        self,
        domain: dict,
        module_file: str,
        h1_name: str,
        h2_name: str,
        h3_name: str,
    ) -> str:
        noun = domain["data_noun"]
        plural = domain["data_noun_plural"]
        key = domain["key_field"]
        val = domain["value_field"]
        tag = domain["tag_field"]
        mod = module_file.replace(".py", "")

        return f'''"""Tests for {domain["title"]}.

These tests verify functional correctness BEFORE and AFTER optimization.
They must all pass without modification.
"""
from __future__ import annotations

import importlib
import math
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import {mod}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_{plural}():
    return [
        {{"{key}": 0, "{val}": 10.5, "{tag}": "group_0"}},
        {{"{key}": 1, "{val}": 55.5, "{tag}": "group_1"}},
        {{"{key}": 2, "{val}": 30.0, "{tag}": "group_2"}},
        {{"{key}": 3, "{val}": 5.0,  "{tag}": "group_0"}},
        {{"{key}": 4, "{val}": 80.0, "{tag}": "group_4"}},
    ]

@pytest.fixture
def reference_{plural}():
    return [
        {{"{key}": 1, "{val}": 55.5, "{tag}": "group_1"}},
        {{"{key}": 3, "{val}": 5.0,  "{tag}": "group_0"}},
    ]


# ---------------------------------------------------------------------------
# Hotspot 1 tests
# ---------------------------------------------------------------------------

def test_{h1_name}_returns_matches(sample_{plural}, reference_{plural}):
    result = {mod}.{h1_name}(sample_{plural}, reference_{plural})
    keys = {{r["{key}"] for r in result}}
    assert keys == {{1, 3}}


def test_{h1_name}_empty_reference(sample_{plural}):
    result = {mod}.{h1_name}(sample_{plural}, [])
    assert result == []


def test_{h1_name}_no_match():
    data = [{{"{key}": 99, "{val}": 1.0, "{tag}": "x"}}]
    ref  = [{{"{key}": 0,  "{val}": 0.0, "{tag}": "y"}}]
    assert {mod}.{h1_name}(data, ref) == []


def test_{h1_name}_all_match(sample_{plural}):
    result = {mod}.{h1_name}(sample_{plural}, sample_{plural})
    assert len(result) == len(sample_{plural})


# ---------------------------------------------------------------------------
# Hotspot 2 tests
# ---------------------------------------------------------------------------

def test_{h2_name}_deterministic():
    a = {mod}.{h2_name}(3.0)
    b = {mod}.{h2_name}(3.0)
    assert abs(a - b) < 1e-9


def test_{h2_name}_different_inputs():
    assert {mod}.{h2_name}(1.0) != {mod}.{h2_name}(2.0)


def test_{h2_name}_zero():
    result = {mod}.{h2_name}(0.0)
    assert isinstance(result, float)


def test_{h2_name}_positive():
    result = {mod}.{h2_name}(5.0)
    assert result > 0


# ---------------------------------------------------------------------------
# Hotspot 3 tests
# ---------------------------------------------------------------------------

def test_{h3_name}_filters_correctly(sample_{plural}):
    result = {mod}.{h3_name}(sample_{plural}, threshold=30.0)
    # values > 30.0 are 55.5 and 80.0
    vals = list(result)
    assert set(vals) == {{55.5, 80.0}}


def test_{h3_name}_empty_input():
    result = {mod}.{h3_name}([], threshold=0.0)
    assert list(result) == []


def test_{h3_name}_no_values_above_threshold(sample_{plural}):
    result = {mod}.{h3_name}(sample_{plural}, threshold=1000.0)
    assert list(result) == []


def test_{h3_name}_all_above_threshold(sample_{plural}):
    result = {mod}.{h3_name}(sample_{plural}, threshold=-1.0)
    vals = list(result)
    assert len(vals) == len(sample_{plural})


# ---------------------------------------------------------------------------
# Benchmark: after optimization, run_benchmark() must not take forever
# (we don\'t enforce the full budget in CI — just sanity check it runs)
# ---------------------------------------------------------------------------

def test_run_benchmark_completes():
    elapsed = {mod}.run_benchmark()
    assert isinstance(elapsed, float)
    assert elapsed >= 0
'''

    # ------------------------------------------------------------------
    # Spec and Brief
    # ------------------------------------------------------------------

    def _generate_spec(
        self,
        domain: dict,
        module_file: str,
        h1_name: str, h1_strategy: str, h1_ms: int, h1_calls: int,
        h2_name: str, h2_strategy: str, h2_ms: int, h2_calls: int,
        h3_name: str, h3_strategy: str, h3_ms: int, h3_calls: int,
        total_ms: int,
        budget_ms: int,
    ) -> str:
        noun = domain["data_noun"]
        plural = domain["data_noun_plural"]
        key = domain["key_field"]
        val = domain["value_field"]

        return f"""# CR3: Performance Optimization from Profiler Report

## Goal
Optimize the three profiled hotspot functions in `{module_file}` so the
module meets its performance budget.  All existing tests must continue to pass.

## Module Under Review
**{domain["title"]}** — `{module_file}`

This module {domain["description"]}.

---

## Profiler Findings

Total runtime before optimization: **{total_ms} ms**
Performance budget: **{budget_ms} ms**
Gap to close: **{total_ms - budget_ms} ms**

---

## Hotspot 1 — `{h1_name}` ({h1_ms} ms, {h1_calls} calls)

**Problem**: The function performs an O(n×m) nested scan over two lists,
executing one linear search per {noun}.  For large inputs this dominates
runtime.

**Required fix**: {h1_strategy}.

Correct approach — replace the inner loop with a set/dict built once from
*reference*:
```python
def {h1_name}(
    {plural},
    reference,
):
    ref_keys = {{r["{key}"] for r in reference}}   # O(m) once
    return [{noun} for {noun} in {plural} if {noun}["{key}"] in ref_keys]  # O(n)
```

The return type must remain `List[Dict[str, Any]]`.

---

## Hotspot 2 — `{h2_name}` ({h2_ms} ms, {h2_calls} calls)

**Problem**: The function recomputes an expensive result every call even
when called with the same *value* thousands of times.  The computation is
pure (deterministic, no side-effects).

**Required fix**: {h2_strategy}.

Correct approach — add a module-level cache dict:
```python
_cache: dict = {{}}

def {h2_name}(value: float) -> float:
    if value in _cache:
        return _cache[value]
    # ... existing computation ...
    _cache[value] = result
    return result
```

`functools.lru_cache` is also acceptable.

---

## Hotspot 3 — `{h3_name}` ({h3_ms} ms, {h3_calls} calls)

**Problem**: The function builds a complete `list` in memory before
returning it.  All callers iterate the result exactly once, so a generator
avoids the allocation cost.

**Required fix**: {h3_strategy}.

Correct approach — convert to a generator function:
```python
def {h3_name}(
    {plural},
    threshold: float,
):
    for {noun} in {plural}:
        v = float({noun}["{val}"])
        if v > threshold:
            yield v
```

The return annotation may change to `Generator[float, None, None]` or
`Iterable[float]`.  Callers that call `list()` on the result continue to
work correctly.

---

## Constraints
- Optimize ALL three hotspot functions — do not skip any.
- Do NOT modify `tests/test_module.py`.
- Do NOT change the public function signatures beyond the return annotation
  of Hotspot 3.
- Do NOT alter `load_{plural}`, `run_benchmark`, or any helper functions.
- Correctness must be preserved: the tests are the ground-truth.
- After optimization the benchmark (`run_benchmark()`) should complete well
  under {budget_ms} ms for a 500-{noun} dataset.

## Deliverables
1. `{module_file}` with all three hotspots optimized.
2. `tests/test_module.py` must pass without modification.
3. Verifier writes `attestation.json` with `verdict: pass` once all checks pass.
"""

    def _generate_brief(self, domain: dict, module_file: str) -> str:
        return f"""# CR3: Performance Optimization (Brief)

## Your Task
The **{domain["title"]}** (`{module_file}`) is too slow and must be
optimized before it can ship.

A profiler has identified the slow functions.  The profiler report is in
`profiler_report.txt` in your workspace — it shows which functions are slow
and how many times they are called, but **not** the fix strategies.

The Planner has the full profiler analysis including the required
optimization strategies.  Follow the Planner's instructions precisely.

## What You Know
- The module is in `{module_file}`.
- There are exactly **3 hotspot functions** to optimize.
- `profiler_report.txt` names the slow functions and their call counts.
- The detailed fix strategies have been provided to the Planner.
- `tests/test_module.py` must continue to pass without any modification.
- Do NOT modify `tests/test_module.py`.
- Do NOT change function signatures or helper functions.
"""
