# GH674_psycopg_1158: respect set_types in c-version in text format — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/psycopg/psycopg

## PR Description

`set_types` is currently ignored in the c version in text format. This PR harmonizes the behavior with the binary version:
- respect `set_types`
- if no `set_types` was specified, set fixed col dumper from first non-None value

Should fix https://github.com/psycopg/psycopg/discussions/1153

## PR Review Comments

**[user]** on `tests/test_copy_async.py`:

It would be wise to fetch back the data to verify it was written correctly (sorry, I missed doing it in my initial MR). Can you add it please?

**[user]** on `tests/test_copy_async.py`:

Yupp, done.

**[user]** on `psycopg_c/psycopg_c/_psycopg/copy.pyx`:

The `len` call here costs ~10% additional conversion runtime. If we can ensure, that `tx._row_dumpers` is always of a list type, we get the length check with `PyList_GET_SIZE` almost for free.

**[user]** on `psycopg_c/psycopg_c/_psycopg/copy.pyx`:

Same here, should be `PyList_GET_SIZE`.

**[user]** on `psycopg_c/psycopg_c/_psycopg/copy.pyx`:

Do we have this certainty?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
