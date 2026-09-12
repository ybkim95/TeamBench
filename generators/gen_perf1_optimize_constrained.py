"""
Parameterized generator for PERF1: Optimize Constrained Module.

Each seed produces a different data processing domain
(data_processor / report_generator / search_engine / event_aggregator / log_analyzer)
with:

  4 real performance bottlenecks (must be fixed):
    B1. o2n_scan:      O(n^2) list membership check inside loop (use set for O(1))
    B2. needless_copy: deep-copies entire dataset on every call (remove deepcopy)
    B3. missing_cache: expensive pure function called repeatedly with same args (lru_cache)
    B4. redundant_io:  reads the same config file on every call (read once at init)

  2 intentional slow patterns (must NOT be changed):
    S1. rate_limit_sleep: throttle sleep between API-style exports (compliance)
    S2. stable_sort:      timsort with key= for deterministic ordering requirement

Information asymmetry (TNI pattern A):
  spec.md   — profiling report identifying bottlenecks vs constraints with exact fixes
  brief.md  — "optimize the slow module to meet the performance target" (no specifics)

Grade: run benchmark harness; module must complete under time limit AND produce
       correct output AND preserve both intentional patterns.
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "data_processor",
        "class_name": "DataProcessor",
        "module": "processor",
        "item_type": "record",
        "item_plural": "records",
        "collection": "dataset",
        "id_field": "record_id",
        "value_field": "amount",
        "category_field": "category",
        "config_file": "processor.cfg",
        "config_key": "precision",
        "config_default": "2",
        "expensive_fn": "normalize_value",
        "expensive_desc": "normalizes a value against a reference scale",
        "rate_limit_desc": "regulatory: max 50 writes/sec",
        "rate_limit_sleep": 0.02,
        "sort_field": "record_id",
        "sort_desc": "stable sort by record_id for deterministic downstream join",
        "primary_fn": "process_batch",
        "primary_desc": "processes a batch of records and returns aggregated results",
        "filter_fn": "filter_active",
        "filter_desc": "filters to only active records",
    },
    {
        "name": "report_generator",
        "class_name": "ReportGenerator",
        "module": "reporter",
        "item_type": "entry",
        "item_plural": "entries",
        "collection": "entries",
        "id_field": "entry_id",
        "value_field": "score",
        "category_field": "department",
        "config_file": "report.cfg",
        "config_key": "decimal_places",
        "config_default": "3",
        "expensive_fn": "compute_percentile",
        "expensive_desc": "computes percentile rank for a score in a reference distribution",
        "rate_limit_desc": "compliance: max 30 submits/sec",
        "rate_limit_sleep": 0.033,
        "sort_field": "entry_id",
        "sort_desc": "stable sort by entry_id for audit trail reproducibility",
        "primary_fn": "generate_report",
        "primary_desc": "generates a summary report from a list of entries",
        "filter_fn": "filter_complete",
        "filter_desc": "filters to only completed entries",
    },
    {
        "name": "search_engine",
        "class_name": "SearchEngine",
        "module": "search",
        "item_type": "document",
        "item_plural": "documents",
        "collection": "corpus",
        "id_field": "doc_id",
        "value_field": "relevance",
        "category_field": "source",
        "config_file": "search.cfg",
        "config_key": "min_score",
        "config_default": "0",
        "expensive_fn": "compute_tfidf",
        "expensive_desc": "computes TF-IDF weight for a term against a reference corpus",
        "rate_limit_desc": "SLA: max 100 index updates/sec to avoid corruption",
        "rate_limit_sleep": 0.01,
        "sort_field": "doc_id",
        "sort_desc": "stable sort by doc_id for deterministic result ordering",
        "primary_fn": "search_corpus",
        "primary_desc": "searches the corpus and returns ranked documents",
        "filter_fn": "filter_indexed",
        "filter_desc": "filters to only indexed documents",
    },
    {
        "name": "event_aggregator",
        "class_name": "EventAggregator",
        "module": "aggregator",
        "item_type": "event",
        "item_plural": "events",
        "collection": "event_stream",
        "id_field": "event_id",
        "value_field": "magnitude",
        "category_field": "event_type",
        "config_file": "aggregator.cfg",
        "config_key": "window_size",
        "config_default": "60",
        "expensive_fn": "compute_entropy",
        "expensive_desc": "computes Shannon entropy for an event distribution",
        "rate_limit_desc": "ops policy: max 20 alerts/sec to avoid alert storm",
        "rate_limit_sleep": 0.05,
        "sort_field": "event_id",
        "sort_desc": "stable sort by event_id for deterministic replay ordering",
        "primary_fn": "aggregate_events",
        "primary_desc": "aggregates events by type and computes statistics",
        "filter_fn": "filter_valid",
        "filter_desc": "filters to only valid (non-corrupted) events",
    },
    {
        "name": "log_analyzer",
        "class_name": "LogAnalyzer",
        "module": "analyzer",
        "item_type": "log_entry",
        "item_plural": "log entries",
        "collection": "log_lines",
        "id_field": "line_id",
        "value_field": "latency_ms",
        "category_field": "service",
        "config_file": "analyzer.cfg",
        "config_key": "threshold_ms",
        "config_default": "500",
        "expensive_fn": "parse_stack_trace",
        "expensive_desc": "parses a stack trace pattern from a log line signature",
        "rate_limit_desc": "infra policy: max 25 metric exports/sec to protect Prometheus",
        "rate_limit_sleep": 0.04,
        "sort_field": "line_id",
        "sort_desc": "stable sort by line_id for chronological ordering required by SIEM",
        "primary_fn": "analyze_logs",
        "primary_desc": "analyzes log entries and returns per-service statistics",
        "filter_fn": "filter_errors",
        "filter_desc": "filters to only error-level log entries",
    },
]


class Generator(TaskGenerator):
    task_id = "PERF1_optimize_constrained"
    domain = "Performance"
    difficulty = "expert"
    languages = ["python"]

    @staticmethod
    def _clean(s: str) -> str:
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        cfg = DOMAINS[domain_idx]

        # Seed-parameterized variant values
        n_items = rng.choice([800, 1000, 1200, 1500])
        time_limit_ms = rng.choice([2000, 2500, 3000])
        blocked_list_size = rng.choice([200, 300, 400])

        workspace_files = self._make_workspace(cfg, blocked_list_size, n_items)
        spec_md = self._clean(self._make_spec(cfg, n_items, time_limit_ms, blocked_list_size))
        brief_md = self._clean(self._make_brief(cfg, time_limit_ms))

        return GeneratedTask(
            task_id="PERF1_optimize_constrained",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "n_items": n_items,
                "time_limit_ms": time_limit_ms,
                "blocked_list_size": blocked_list_size,
                "bottlenecks": ["o2n_scan", "needless_copy", "missing_cache", "redundant_io"],
                "constraints": ["rate_limit_sleep", "stable_sort"],
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "expert", "category": "Performance"},
        )

    # ── Workspace file generators ──────────────────────────────────────────────

    def _make_workspace(self, cfg: dict, blocked_list_size: int, n_items: int) -> dict:
        files: dict = {}
        files[f"{cfg['module']}.py"] = self._make_module(cfg, blocked_list_size)
        files[cfg["config_file"]] = self._make_config(cfg)
        files["benchmark.py"] = self._make_benchmark(cfg, n_items)
        files["tests/test_correctness.py"] = self._make_tests(cfg)
        files["profiling_notes.md"] = self._make_profiling_notes(cfg, n_items, blocked_list_size)
        files["README.md"] = self._make_readme(cfg)
        return files

    def _make_module(self, cfg: dict, blocked_list_size: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"
            {c['name']}: core processing module.

            This module {c['primary_desc']}.
            It contains performance bottlenecks to optimize and intentional
            slow patterns that must be preserved.
            \"\"\"
            from __future__ import annotations

            import copy
            import time
            from typing import Any


            def _read_config(config_file: str, key: str, default: str = "0") -> str:
                \"\"\"Read a single key from a config file.\"\"\"
                try:
                    with open(config_file) as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith(key + "="):
                                return line.split("=", 1)[1].strip()
                except (FileNotFoundError, IOError):
                    pass
                return default


            def {c['expensive_fn']}(value: float, reference: float) -> float:
                \"\"\"
                {c['expensive_desc'].capitalize()}.

                This is a pure function — same inputs always produce the same output.
                It is computationally expensive (iterative calculation).
                \"\"\"
                if reference == 0:
                    return 0.0
                result = value / reference
                for _ in range(200):
                    result = (result + value / (reference * result + 1e-9)) / 2.0
                return round(result, 6)


            class {c['class_name']}:
                \"\"\"
                {c['primary_desc'].capitalize()}.
                \"\"\"

                def __init__(self, config_file: str = "{c['config_file']}"):
                    self.config_file = config_file
                    # B1: blocked list stored as a list — O(n) membership checks
                    self._blocked: list[str] = [
                        f"blocked_{c['id_field']}_{{i}}" for i in range({blocked_list_size})
                    ]

                def {c['filter_fn']}(self, {c['collection']}: list[dict]) -> list[dict]:
                    \"\"\"
                    {c['filter_desc'].capitalize()}.

                    Bottleneck B1: O(n^2) membership check.
                    self._blocked is a list — `in` is O(n) per item.
                    \"\"\"
                    result = []
                    for item in {c['collection']}:
                        # B1: list membership — O(n) per lookup
                        if item["{c['id_field']}"] not in self._blocked:
                            result.append(item)
                    return result

                def {c['primary_fn']}(self, {c['collection']}: list[dict]) -> Any:
                    \"\"\"
                    {c['primary_desc'].capitalize()}.

                    Bottleneck B2: copies entire dataset with copy.deepcopy on every call.
                    Bottleneck B4: reads config file from disk on every call.
                    Bottleneck B3: calls {c['expensive_fn']} repeatedly without caching.
                    \"\"\"
                    # B2: unnecessary deep copy of entire dataset on every call
                    working = copy.deepcopy({c['collection']})

                    # B4: reads config file from disk on every call
                    precision = int(_read_config(self.config_file, "{c['config_key']}", "{c['config_default']}"))

                    reference = max((item["{c['value_field']}"] for item in working), default=1.0)

                    aggregated: dict = {{}}
                    for item in working:
                        cat = item.get("{c['category_field']}", "unknown")
                        val = float(item.get("{c['value_field']}", 0.0))

                        # B3: pure function called with repeated args, no memoization
                        normalized = {c['expensive_fn']}(val, reference)

                        if cat not in aggregated:
                            aggregated[cat] = {{"count": 0, "total": 0.0, "normalized_total": 0.0}}
                        aggregated[cat]["count"] += 1
                        aggregated[cat]["total"] = round(aggregated[cat]["total"] + val, precision)
                        aggregated[cat]["normalized_total"] = round(
                            aggregated[cat]["normalized_total"] + normalized, 6
                        )
                    return aggregated

                def export_results(self, results: Any, destination: str = "api") -> None:
                    \"\"\"
                    Export results to destination.

                    INTENTIONAL S1 — rate_limit_sleep:
                    Sleeps {c['rate_limit_sleep']}s between exports ({c['rate_limit_desc']}).
                    DO NOT remove or reduce this sleep.
                    \"\"\"
                    for key in sorted(results.keys()):
                        # S1: INTENTIONAL rate-limit sleep — do not remove
                        time.sleep({c['rate_limit_sleep']})
                        _ = (destination, key, results[key])

                def sorted_results(self, {c['collection']}: list[dict]) -> list[dict]:
                    \"\"\"
                    Return {c['item_plural']} in deterministic order.

                    INTENTIONAL S2 — stable_sort:
                    {c['sort_desc'].capitalize()}.
                    DO NOT change the sort key or use an unstable sort.
                    \"\"\"
                    # S2: INTENTIONAL stable sort by {c['sort_field']} — do not change
                    return sorted({c['collection']}, key=lambda x: x["{c['sort_field']}"])
            """)

    def _make_config(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # {cfg['name']} configuration
            {cfg['config_key']}={cfg['config_default']}
            version=1.0
            debug=false
            """)

    def _make_benchmark(self, cfg: dict, n_items: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"
            Benchmark harness for {c['name']}.

            Measures wall-clock time for {c['filter_fn']} + {c['primary_fn']}
            on {n_items} {c['item_plural']}.
            \"\"\"
            import sys
            import os
            import time

            sys.path.insert(0, os.path.dirname(__file__))

            from {c['module']} import {c['class_name']}

            N = {n_items}


            def make_dataset(n: int) -> list[dict]:
                import random
                rng = random.Random(42)
                cats = ["cat_a", "cat_b", "cat_c", "cat_d"]
                return [
                    {{
                        "{c['id_field']}": f"item_{{i}}",
                        "{c['value_field']}": round(rng.uniform(0.1, 100.0), 2),
                        "{c['category_field']}": rng.choice(cats),
                    }}
                    for i in range(n)
                ]


            def run_benchmark() -> float:
                processor = {c['class_name']}()
                dataset = make_dataset(N)
                start = time.perf_counter()
                filtered = processor.{c['filter_fn']}(dataset)
                result = processor.{c['primary_fn']}(filtered)
                elapsed_ms = (time.perf_counter() - start) * 1000
                assert result, "process result must be non-empty"
                assert isinstance(result, dict), "result must be a dict"
                return elapsed_ms


            if __name__ == "__main__":
                import argparse
                parser = argparse.ArgumentParser()
                parser.add_argument("--time-limit-ms", type=float, default=2500)
                args = parser.parse_args()
                elapsed = run_benchmark()
                print(f"elapsed_ms={{elapsed:.1f}}")
                if elapsed <= args.time_limit_ms:
                    print("BENCHMARK: PASS")
                    sys.exit(0)
                else:
                    print(f"BENCHMARK: FAIL ({{elapsed:.1f}}ms > {{args.time_limit_ms:.0f}}ms limit)")
                    sys.exit(1)
            """)

    def _make_tests(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"Correctness tests for {c['name']}.\"\"\";
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

            import inspect
            import pytest
            from {c['module']} import {c['class_name']}, {c['expensive_fn']}


            def make_dataset(n: int = 20, seed: int = 99) -> list[dict]:
                import random
                rng = random.Random(seed)
                cats = ["cat_a", "cat_b", "cat_c"]
                return [
                    {{
                        "{c['id_field']}": f"item_{{i}}",
                        "{c['value_field']}": round(rng.uniform(1.0, 50.0), 2),
                        "{c['category_field']}": rng.choice(cats),
                    }}
                    for i in range(n)
                ]


            class Test{c['class_name']}:
                def test_filter_removes_blocked(self):
                    proc = {c['class_name']}()
                    ds = make_dataset(10)
                    ds[0]["{c['id_field']}"] = "blocked_{c['id_field']}_0"
                    result = proc.{c['filter_fn']}(ds)
                    ids = {{r["{c['id_field']}"] for r in result}}
                    assert "blocked_{c['id_field']}_0" not in ids

                def test_primary_fn_returns_dict(self):
                    proc = {c['class_name']}()
                    ds = make_dataset(20)
                    result = proc.{c['primary_fn']}(ds)
                    assert isinstance(result, dict)
                    assert len(result) > 0

                def test_primary_fn_counts_correct(self):
                    proc = {c['class_name']}()
                    ds = make_dataset(30)
                    result = proc.{c['primary_fn']}(ds)
                    total = sum(v["count"] for v in result.values())
                    assert total == 30

                def test_sorted_results_deterministic(self):
                    proc = {c['class_name']}()
                    ds = make_dataset(20)
                    ds_rev = list(reversed(ds))
                    ids1 = [r["{c['id_field']}"] for r in proc.sorted_results(ds)]
                    ids2 = [r["{c['id_field']}"] for r in proc.sorted_results(ds_rev)]
                    assert ids1 == ids2

                def test_expensive_fn_pure(self):
                    v1 = {c['expensive_fn']}(5.0, 10.0)
                    v2 = {c['expensive_fn']}(5.0, 10.0)
                    assert v1 == v2

                def test_rate_limit_sleep_preserved(self):
                    proc = {c['class_name']}()
                    src = inspect.getsource(proc.export_results)
                    assert "time.sleep" in src, "rate-limit sleep must be preserved"

                def test_stable_sort_key_preserved(self):
                    proc = {c['class_name']}()
                    src = inspect.getsource(proc.sorted_results)
                    assert "{c['sort_field']}" in src, "sort key must be preserved"
            """)

    def _make_profiling_notes(self, cfg: dict, n_items: int, blocked_list_size: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # Profiling Notes — {c['name']}

            ## Summary

            Profiled with `cProfile` on a dataset of {n_items} {c['item_plural']}.
            Four genuine bottlenecks identified; two patterns are operational constraints.

            ## Bottlenecks (Fix These)

            ### B1 — O(n^2) List Scan in `{c['filter_fn']}`

            `self._blocked` is a `list` of {blocked_list_size} entries. The `in` operator
            performs a linear scan: O(n) per lookup. With {n_items} {c['item_plural']}:
            {n_items} x {blocked_list_size} = {n_items * blocked_list_size:,} comparisons.

            Fix: In `__init__`, convert `self._blocked` from `list` to `set`.

            ### B2 — Unnecessary Deep Copy in `{c['primary_fn']}`

            `copy.deepcopy({c['collection']})` allocates a full copy of all {n_items}
            {c['item_plural']} on every call. The copy is never mutated in-place.

            Fix: Remove the `copy.deepcopy(...)` call and iterate `{c['collection']}` directly.
            Remove `import copy` if it becomes unused.

            ### B3 — Missing Cache on `{c['expensive_fn']}`

            `{c['expensive_fn']}` is a pure function (same inputs -> same output).
            Called once per {c['item_type']} in `{c['primary_fn']}`. Many {c['item_plural']}
            share the same `{c['value_field']}`, so identical computations repeat many times.

            Fix: Add `from functools import lru_cache` and decorate with
            `@lru_cache(maxsize=512)`.

            ### B4 — Config File Read on Every Call in `{c['primary_fn']}`

            `_read_config(self.config_file, "{c['config_key']}", ...)` opens and reads
            `{c['config_file']}` on every invocation of `{c['primary_fn']}`. The config
            is immutable at runtime — reading it repeatedly is pure I/O waste.

            Fix: In `__init__`, cache the value:
                self._{c['config_key']} = int(_read_config(self.config_file, "{c['config_key']}", "{c['config_default']}"))
            Replace the call in `{c['primary_fn']}` with `self._{c['config_key']}`.

            ## Intentional Constraints (Do NOT Change)

            ### S1 — Rate-Limit Sleep in `export_results`

            `time.sleep({c['rate_limit_sleep']})` between exports is intentional.
            Reason: {c['rate_limit_desc']}.
            This sleep must not be removed, reduced, or moved outside the loop.

            ### S2 — Stable Sort in `sorted_results`

            `sorted(..., key=lambda x: x["{c['sort_field']}"])` is intentional.
            Reason: {c['sort_desc']}.
            The sort key and Python's stable timsort must be preserved.
            """)

    def _make_readme(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # {c['name']} — README

            This module {c['primary_desc']}.

            ## Files

            - `{c['module']}.py` — core processing module (the file to optimize)
            - `{c['config_file']}` — runtime configuration
            - `benchmark.py` — performance benchmark harness
            - `tests/test_correctness.py` — correctness tests
            - `profiling_notes.md` — profiling analysis

            ## Running

            ```bash
            python -m pytest tests/ -v
            python benchmark.py --time-limit-ms 2500
            ```

            ## Notes

            - Only modify `{c['module']}.py`
            - All correctness tests must continue to pass after changes
            - The benchmark must complete under the time limit
            """)

    # ── Spec / Brief generators ────────────────────────────────────────────────

    def _make_spec(self, cfg: dict, n_items: int, time_limit_ms: int, blocked_list_size: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # PERF1_optimize_constrained: Optimize Constrained Module — Full Specification (Planner Only)

            ## Overview

            The workspace contains `{c['module']}.py` — a {c['name']} module with
            **4 real performance bottlenecks** and **2 intentional slow patterns** that
            must be preserved.

            The executor only receives the brief. This spec provides the full profiling analysis.

            ## File Structure

            - `{c['module']}.py` — the ONLY file to modify
            - `{c['config_file']}` — runtime config (do not modify)
            - `benchmark.py` — benchmark harness (do not modify)
            - `tests/test_correctness.py` — correctness suite (do not modify)
            - `profiling_notes.md` — same analysis as this spec (readable by all agents)

            ## Performance Target

            `{c['filter_fn']}` + `{c['primary_fn']}` on {n_items} {c['item_plural']} must
            complete within **{time_limit_ms} ms** (measured by `benchmark.py`).

            ## Bottlenecks (Must Fix)

            | # | Name | Location | Root Cause | Fix |
            |---|------|----------|------------|-----|
            | B1 | o2n_scan | `{c['filter_fn']}` | `self._blocked` is `list` — O(n) lookup per item | Convert to `set` in `__init__` |
            | B2 | needless_copy | `{c['primary_fn']}` | `copy.deepcopy` on every call | Remove deepcopy; iterate original |
            | B3 | missing_cache | `{c['expensive_fn']}` | Pure fn called repeatedly, no memo | `@lru_cache(maxsize=512)` |
            | B4 | redundant_io | `{c['primary_fn']}` | Config file read on every call | Cache in `__init__` as `self._{c['config_key']}` |

            ### B1 — O(n^2) List Scan

            `self._blocked` has {blocked_list_size} entries as a `list`. `in` is O(n) per lookup.
            With {n_items} {c['item_plural']}: {n_items} x {blocked_list_size} = {n_items * blocked_list_size:,} comparisons total.

            Fix: change `self._blocked = [...]` to `self._blocked = set([...])` (or set comprehension).

            ### B2 — Unnecessary Deep Copy

            `working = copy.deepcopy({c['collection']})` allocates a copy of all {n_items}
            {c['item_plural']} on every call. The copy is only iterated, never mutated.

            Fix: remove `copy.deepcopy(...)` and iterate `{c['collection']}` directly.
            Remove `import copy` if it becomes unused.

            ### B3 — Missing Cache

            `{c['expensive_fn']}` is pure. Many {c['item_plural']} share the same
            `{c['value_field']}` value — identical computations repeat without memoization.

            Fix: add `from functools import lru_cache` and decorate `{c['expensive_fn']}`
            with `@lru_cache(maxsize=512)`.

            ### B4 — Redundant I/O

            `_read_config(self.config_file, "{c['config_key']}", ...)` opens `{c['config_file']}`
            on every call to `{c['primary_fn']}`. The file is immutable at runtime.

            Fix: in `__init__` add:
                self._{c['config_key']} = int(_read_config(self.config_file, "{c['config_key']}", "{c['config_default']}"))
            Replace the call in `{c['primary_fn']}` with `self._{c['config_key']}`.

            ## Intentional Patterns (DO NOT CHANGE)

            ### S1 — Rate-Limit Sleep in `export_results`

            ```python
            time.sleep({c['rate_limit_sleep']})  # inside the export loop
            ```

            **Must be preserved.** Reason: {c['rate_limit_desc']}.
            Removing or reducing this sleep violates operational requirements.

            ### S2 — Stable Sort in `sorted_results`

            ```python
            sorted({c['collection']}, key=lambda x: x["{c['sort_field']}"])
            ```

            **Must be preserved.** Reason: {c['sort_desc']}.
            The sort key and Python's stable sort guarantee must be maintained.

            ## Acceptance Criteria

            1. `python benchmark.py --time-limit-ms {time_limit_ms}` exits 0
            2. All tests in `tests/test_correctness.py` pass
            3. `export_results` still contains `time.sleep({c['rate_limit_sleep']})` inside the loop
            4. `sorted_results` still sorts by `"{c['sort_field']}"` key
            5. Only `{c['module']}.py` is modified

            ## Authoritative Sources

            - This spec is the authoritative analysis of bottlenecks vs intentional patterns
            - `profiling_notes.md` in the workspace provides the same information
            """)

    def _make_brief(self, cfg: dict, time_limit_ms: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # PERF1_optimize_constrained (Brief)

            The `{c['module']}.py` module is too slow and failing the performance benchmark.
            Optimize it so the benchmark completes under the time limit.

            **File to optimize:** `{c['module']}.py`
            **Benchmark:** `python benchmark.py --time-limit-ms {time_limit_ms}`
            **Tests:** `python -m pytest tests/ -v` (must still pass after changes)
            **Reference:** `profiling_notes.md` contains profiling analysis that may help.

            **Do NOT modify:** `benchmark.py`, `tests/`, `{c['config_file']}`, or any other file.

            Follow the Planner's guidance precisely.
            """)
