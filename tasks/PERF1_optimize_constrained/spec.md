# PERF1_optimize_constrained: Optimize Constrained Module (Planner Only)

## Goal

The workspace module has 4 real performance bottlenecks that must be fixed so
the benchmark passes, plus 2 intentional slow patterns that must be preserved.
The Planner reads this spec and `profiling_notes.md`; the Executor only receives
the brief and must follow the Planner's guidance.

## Bottlenecks to Fix

1. **B1 o2n_scan** — `self._blocked` is a `list`; convert to `set` in `__init__` for O(1) membership
2. **B2 needless_copy** — `copy.deepcopy(dataset)` on every call; remove it, iterate original
3. **B3 missing_cache** — pure function called repeatedly; add `@lru_cache(maxsize=512)`
4. **B4 redundant_io** — config file read on every call; cache result in `__init__`

## Intentional Patterns (DO NOT CHANGE)

- **S1 rate_limit_sleep** — `time.sleep(...)` in `export_results` is a compliance constraint
- **S2 stable_sort** — `sorted(..., key=...)` in `sorted_results` must preserve its sort key

## Supporting Documents

- `profiling_notes.md` — profiling analysis with exact fix instructions
- `benchmark.py` — benchmark harness (run to verify performance)
- `tests/test_correctness.py` — correctness suite (must keep passing)

## Contradiction / Hidden Complexity

A naive agent will see all sleeps and sorts as optimization opportunities and
remove or simplify them. The profiling report and spec are the authoritative
sources distinguishing real bottlenecks from intentional constraints.

## Important Notes

- Only the main module file (e.g. `processor.py`) may be modified
- `profiling_notes.md` is the authoritative source for what is a bottleneck vs constraint
- The benchmark and tests must both pass after changes
