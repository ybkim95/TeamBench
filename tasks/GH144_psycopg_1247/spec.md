# GH144_psycopg_1247: fix: retain pgconn on OperationalError — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/1246
- Repo: https://github.com/psycopg/psycopg

## Issue Description

I use `OperationalError.pgconn.needs_password` in a script to prompt the user for his password if needed.  This no longer works as of 3.2.8 (specifically #1076) because attribute `pgconn` is always None.

Here's my reproducer:

```py
import psycopg

try:
    with psycopg.connect():
        pass
except psycopg.OperationalError as e:
    assert e.pgconn
    assert e.pgconn.needs_password
```

Running that script with a Postgres user who requires a password, but without providing that password, gives me this:

```
$ PGHOST=localhost PGPORT=5434 PGUSER=postgres python needs_password.py
Traceback (most recent call last):
  File "/home/ewie/src/psycopg-regress/needs_password.py", line 4, in <module>
    with psycopg.connect():
         ~~~~~~~~~~~~~~~^^
  File "/home/ewie/src/psycopg/psycopg/psycopg/connection.py", line 133, in connect
    raise enhanced_exception.with_traceback(None)
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5434 failed: fe_sendauth: no password supplied
Multiple connection attempts failed. All failures were:
- host: None, port: None, hostaddr: '::1': connection failed: connection to server at "::1", port 5434 failed: fe_sendauth: no password supplied
- host: None, port: None, hostaddr: '127.0.0.1': connection failed: connection to server at "127.0.0.1", port 5434 failed: fe_sendauth: no password supplied

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/ewie/src/psycopg-regress/needs_password.py", line 7, in <module>
    assert e.pgconn
           ^^^^^^^^
AssertionError
```

## PR Review Comments

**[user]** on `psycopg/psycopg/connection_async.py`:

Nit: it would be nicer on two lines:

```suggestion
            new_ex = type(last_ex)("\n".join(lines), pgconn=last_ex.pgconn)
            raise new_ex.with_traceback(None)
```

**[user]** on `tests/test_connection_async.py`:

Good idea, but we need to make it a failing multi-attempt connection. We don't need to handle an explicit monkeypatch context because we don't need to access the pristine environment in the test after the block.

So my proposal is to drop the password and to specify the host twice:

```suggestion
    monkeypatch.delenv("PGPASSWORD", raising=False)
    info = conninfo_to_dict(dsn)
    info.pop("password", None)
    info["host"] = ",".join([str(info.get("host", os.environ.get("PGHOST", "")))] * 2)
    dsn = make_conninfo("", **info)
```

**[user]** on `tests/test_connection_async.py`:

The point of this test is to test with multiple attempts:

```suggestion
async def test_multi_attempt_error_pgconn(aconn_cls, dsn, monkeypatch):
```

**[user]** on `psycopg/psycopg/connection_async.py`:

Done. Looks much nicer now.

**[user]** on `tests/test_connection_async.py`:

Ah, it never occurred to me that I can specify the **same** host twice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
