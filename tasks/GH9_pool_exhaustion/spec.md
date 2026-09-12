# GH9: Connection Pool Exhaustion — Full Specification

## Issue Description

After approximately `pool_size` failed queries, the application hangs indefinitely
on new database operations. The connection pool is silently exhausted because
connections are never returned to the pool when exceptions occur during query
execution.

Reference: https://github.com/sqlalchemy/sqlalchemy/issues/5765

## Root Cause

In `Session.execute(sql)`, the current implementation is:

```python
conn = self.pool.acquire()
result = conn.execute(sql)  # If this raises, release() never called!
self.pool.release(conn)
return result
```

There is no `try/finally` block. When `conn.execute(sql)` raises a `QueryError`
(e.g., querying a nonexistent table), the exception propagates immediately and
`self.pool.release(conn)` is never reached. The connection remains marked as
"in use" in the pool forever.

After `pool_size` such failures, all connections are "in use" but none are
actually doing work. Any subsequent `pool.acquire()` call blocks until the
timeout expires, then raises `PoolExhaustedError`.

## The Fix

Wrap the execute call in a `try/finally` block to guarantee release:

```python
conn = self.pool.acquire()
try:
    result = conn.execute(sql)
    return result
finally:
    self.pool.release(conn)
```

The `finally` block runs whether the call succeeds or raises, ensuring the
connection is always returned to the pool.

## Scope of the Fix

The fix is confined to `Session.execute()` in `db_pool.py`. Approximately
3-5 lines change (adding `try:`, indenting the body, and adding `finally:`
with the `release()` call moved inside).

**Do NOT change:**

- `ConnectionPool.acquire()` — the acquire logic (semaphore + tracking) is correct.
- `ConnectionPool.release()` — the release logic is correct.
- `Connection.execute()` — it is correct that bad SQL raises `QueryError`.
- Pool size configuration (`max_size`) and timeout logic — these are correct.
- `Session.execute_many()` — check if it has the same bug and fix if so.
- Any test file.

## Verification

After the fix:

1. `test_basic_query` — still passes (no regression).
2. `test_query_error_handling` — `QueryError` is still raised for bad SQL.
3. `test_pool_exhaustion_on_errors` — pool_size=3 failures no longer exhaust
   the pool; a subsequent valid query succeeds.
4. `test_pool_status_after_errors` — `pool.status()` shows `available == pool_size`
   and `in_use == 0` after all failed queries return.
5. `test_concurrent_after_errors` — multiple sessions remain usable after errors.
6. `test_successful_queries_release` — pool_size=1 still handles sequential queries
   (regression check).
7. `test_pool_size_respected` — pool does not exceed `max_size`.
