# GH14: Chain-of-Groups Failure Propagation

## Goal

Fix `pipeline.py` so failures in any pipeline stage propagate as exceptions
rather than being silently converted to error dicts and passed to subsequent
stages.

## Requirements

1. `pipeline.run(["POISON_PILL"])` (or `CORRUPT_IMAGE` / `INVALID_DATA`) must
   raise `StageError` (or a subclass of `Exception`)
2. A mix of good and bad items must also raise when any item fails
3. A list of only good items must return all-ok result dicts
4. All tests in `test_pipeline.py` pass: `pytest test_pipeline.py -v`

## Supporting Documents

- `pipeline.py` — contains the buggy `_run_group()` and `_chain_groups()`
- `tasks.py` — individual stage functions (correct, do not modify)
- `test_pipeline.py` — tests

## Contradiction / Hidden Complexity

This mirrors Celery's chain-of-groups bug: when Celery converts a
`group | chain` into internal chords, intermediate chord failures are not
automatically propagated to subsequent chord callbacks. The naive fix of just
re-raising in `_run_group` will break the concurrent fanout semantics; the
correct fix is to inspect results after each stage and raise if any error
dicts are present.

## Important Notes

- Fix is in `pipeline.py` — `_run_group` and/or `_chain_groups`
- Do NOT modify `tasks.py` or `test_pipeline.py`
- Add a helper that checks for error dicts and raises `StageError`
