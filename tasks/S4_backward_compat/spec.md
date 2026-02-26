# S4: Backward Compatibility Trap

## Goal

Add the `strict_mode` feature to the `textparser` library while preserving
**all** existing v1 backward-compatibility guarantees.

## Library Overview

`textparser` is a stable v1 text parsing library currently at version `1.8.3`.
Its public API is:

- `TextParser(config=None)` — constructor, accepts `None`, `str`, or `dict`
- `.process(data)` — processes data, returns a plain `dict` with keys `result`, `status`, `version`
- `.run(data)` — deprecated alias for `.process()` (emits `DeprecationWarning`)
- `.get_config()` — returns a copy of current config dict
- `.reset()` — resets config to defaults
- `TextParser.__version__` — version string, currently `1.8.3`

## New Feature Requirements

Implement `enable_strict_mode(instance)` in `new_feature.py`:

1. The function accepts an existing `TextParser` instance.
2. It enhances the instance in-place with strict validation that raises on any anomaly capability.
3. It returns the same instance (not a new object).
4. At least one new attribute or method must be added to the instance.
5. Calling `enable_strict_mode()` twice on the same instance must be idempotent.
6. The enhancement must be instance-scoped (not affect other instances).

## Backward-Compatibility Constraints

The following constraints MUST be satisfied after your changes. Violating any
one of them constitutes a breaking change and will fail the grade.

   1. **sig_unchanged**: Original constructor signature `__init__(self, config=None)` must not change
   2. **v1_output**: The `process()` method must still return a plain dict for v1 clients
   3. **deprecated_ok**: Deprecated `run()` alias must still be callable and return same result as `process()`
   4. **config_str_ok**: Passing `config` as a plain string (legacy format) must still work
   5. **error_msg_stable**: ValueError message for invalid input must still start with 'Invalid input:'

## Deliverables

1. `new_feature.py` with `enable_strict_mode` fully implemented (no `NotImplementedError`).
2. All tests in `tests/test_legacy.py` must pass (zero modifications to that file).
3. All tests in `tests/test_new_feature.py` must pass.
4. `textparser/core.py` must NOT be modified (API signature preservation).

## Grading

The grader runs:
```
python -m pytest tests/ -q
```
and independently checks each backward-compatibility constraint.
All 10+ checks must pass for full credit.
