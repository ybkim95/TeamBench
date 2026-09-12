# GH740_psycopg_1207: Fix/improve dns error message — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/1205
- Repo: https://github.com/psycopg/psycopg

## Issue Description

Hey team, thought I should surface this issue: 
First of all I made a mistake by not prepanding `$` to an ENV variable, so the database host is not valid, in psycopg(3.2.5) it complains:

`psycopg.OperationalError: [Errno -2] Name or service not known`

but I was at a loss as to what [Errno -2] means, in contrast psycopg2 showed what exactly went wrong:

`psycopg2.OperationalError: could not translate host name "{postgresHost}" to address: Name or service not known`

I wish the error msg would have been more clear.

P.S. the traces for both cases:

psycopg (3.2.5)
```
Traceback (most recent call last):
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/base.py", line 143, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/base.py", line 3301, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 447, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 1264, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 711, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/impl.py", line 177, in _do_get
    with util.safe_reraise():
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/impl.py", line 175, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 388, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 673, in __init__
    self.__connect()
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 899, in __connect
    with util.safe_reraise():
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 895, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/create.py", line 661, in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/default.py", line 629, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/psycopg/connection.py", line 96, in connect
    attempts = conninfo_attempts(params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/psycopg/_conninfo_attempts.py", line 48, in conninfo_attempts
    raise e.OperationalError(str(last_exc))
psycopg.OperationalError: [Errno -2] Name or service not known
```

psycopg2 (2.9.11): 
```
Traceback (most recent call last):
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/base.py", line 143, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/base.py", line 3301, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 447, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 1264, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 711, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/impl.py", line 177, in _do_get
    with util.safe_reraise():
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/impl.py", line 175, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 388, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 673, in __init__
    self.__connect()
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 899, in __connect
    with util.safe_reraise():
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/util/langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/pool/base.py", line 895, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/create.py", line 661, in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/sqlalchemy/engine/default.py", line 629, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/app-root/lib64/python3.11/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: could not translate host name "{postgresHost}" to address: Name or service not known
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thank you for the report: good spot 👍 

In pg2 we relied on the libpq for the name resolution; in pg3 we do it ourselves to allow for async resolution. It looks like the libpq does a better job at decorating the OSError with the right info but we can totally do the same.

It should be easy to fix, here

https://github.com/psycopg/psycopg/blob/b9d533beb5d847ef6837fbd4a011f67730225ffd/psycopg/psycopg/_conninfo_attempts.py#L43-L53

Curiously we log a better debug error than the message we raise. I would convert the above into:

```python
     except OSError as ex: 
         last_ex = e.OperationalError(f"failed to resolve host {attempt.get("host")!r}: {ex}")
         logger.debug("%s", last_ex)
```

If you want to try a PR yourself be my guest, otherwise I will solve the issue in the next days.

### Comment 2 ([user]):

Hi

This PR addresses the issue by improving the error message when host resolution fails.
It’s ready for review and merge — please let me know if any other changes are required.

#1206

### Comment 3 ([user]):

Thank you very much [user]! Write you on the PR!

### Comment 4 ([user]):

[user] thanks so much for the quick response! which I totally didn't expect and thererfore missed the chance to create my first PR...
thanks [user] for the quick fix as well!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
