# GH605_psycopg_1280: fix: premature ConnectionTimeout — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/psycopg/psycopg

## PR Description

The C extension stored the connection deadline as a C float (32-bit). At large monotonic() values, float32 precision loss causes timeouts shorter than the ULP to be silently rounded away, firing ConnectionTimeout immediately. For example, a 1-second timeout hits this after ~97 days of uptime. The pure Python implementation is unaffected since Python floats are always 64-bit. Fixed by changing deadline to double in generators.pyx for both connect() and cancel().

## PR Review Comments

**[user]** on `tests/test_c_extension_float32_deadline.py`:

This test doesn't test anything if not a constant. I get the point but I don't think it's needed.

**[user]** on `tests/test_c_extension_float32_deadline.py`:

Please put this test in an existing module to test connection, we don't need a module specific for a single test.

**[user]** on `tests/test_c_extension_float32_deadline.py`:

This issue affets the `binary` package too, we can skip it on Python only:

```suggestion
@pytest.mark.skipif(pq.__impl__ == "python", reason="only affects C extension")
```

**[user]** on `tests/test_c_extension_float32_deadline.py`:

Can't you just test that `psycopg.AsyncConnection.connect()` behaves as expected? Is it necessary to test internal functions?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
