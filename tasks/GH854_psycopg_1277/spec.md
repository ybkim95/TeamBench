# GH854_psycopg_1277: Fix async pool cancellation handoff race — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/1275
- Repo: https://github.com/psycopg/psycopg

## Issue Description

# TL;DR

- This looks like a residual async queue cancellation race after [#509](https://github.com/psycopg/psycopg/issues/509), not the same issue as [#1208](https://github.com/psycopg/psycopg/issues/1208) / [#1214]((withheld: the upstream fix is not part of the task)).
- On `psycopg-pool==3.3.0` (the latest release on PyPI as of March 6, 2026), `WaitingClient.wait()` can still catch `CancelledError` and then return `self.conn` if the connection is delivered in the same race window.
- I have a deterministic self-contained repro with no PostgreSQL dependency.
- The core issue seems to be that `self.conn` still wins over a previously observed cancellation.

# Environment

- Python 3.13
- `psycopg==3.3.3`
- `psycopg-pool==3.3.0`

# Problem

`WaitingClient.wait()` can catch `CancelledError`, store it in `self.error`, and still return a connection if `self.conn` is set concurrently.

The race is:

1. a task is blocked in `WaitingClient.wait()`
2. another task sets `self.conn`
3. the waiting task is cancelled around the same time
4. `wait()` catches `CancelledError` and stores it in `self.error`
5. after leaving the condition, `wait()` checks `if self.conn` first and returns the connection anyway

So the cancellation is effectively consumed and the task continues as if acquire succeeded.

# Expected behavior

If `WaitingClient.wait()` observes `CancelledError` while waiting, it should not return a connection to the caller, even if `self.conn` is set in the same race window.

# Minimal self-contained repro

The script below is self-contained, requires no PostgreSQL server, and reproduces the behavior deterministically for me.

It uses the private `WaitingClient` type directly only to isolate the race without involving the rest of the pool machinery. This is deterministic because connection assignment, cancellation, and `notify_all()` happen under the same condition lock, so the waiter resumes only after both `self.conn` and the cancellation request have been recorded.

Run with either:

```bash
uv run psycopg_pool_waiting_client_repro.py
```

or, if saved as an executable file with the uv shebang:

```bash
./psycopg_pool_waiting_client_repro.py
```

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "psycopg==3.3.3",
#   "psycopg-pool==3.3.0",
# ]
# ///

import asyncio
import sys

import psycopg_pool
from psycopg_pool.pool_async import WaitingClient

async def reproduce_once() -> bool:
    waiting_client: WaitingClient[object] = WaitingClient()
    marker = object()
    waiter = asyncio.create_task(
        waiting_client.wait(timeout=60.0),
        name="waiting-client-repro",
    )
    try:
        await wait_until_blocked(waiting_client)
        async with waiting_client._cond:
            waiting_client.conn = marker
            waiter.cancel()
            waiting_client._cond.notify_all()
        try:
            result = await waiter
        except asyncio.CancelledError:
            return False
        return result is marker
    finally:
        if not waiter.done():
            waiter.cancel()
            try:
                await waiter
            except asyncio.CancelledError:
                pass

async def wait_until_blocked(waiting_client: WaitingClient[object]) -> None:
    for _ in range(1000):
        if getattr(waiting_client._cond, "_waiters", ()):  # private, repro only
            return
        await asyncio.sleep(0)
    raise RuntimeError("WaitingClient did not start waiting on its condition")

async def main() -> int:
    reproduced = await reproduce_once()
    print(f"python={sys.version.split()[0]}")
    print(f"psycopg_pool={psycopg_pool.__version__}")
    print(f"reproduced={reproduced}")
    if reproduced:
        print("BUG: WaitingClient.wait() returned a connection after cancel()")
        return 0
    print("No reproduction")
    return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

Actual output

```text
python=3.13.9
psycopg_pool=3.3.0
reproduced=True
BUG: WaitingClient.wait() returned a connection after cancel()
```

# Relevant code path

Current `WaitingClient.wait()` appears to do the equivalent of:

```python
try:
    if not await self._cond.wait_timeout(timeout):
        self.error = PoolTimeout(...)
except CLIENT_EXCEPTIONS as ex:
    self.error = ex

if self.conn:
    return self.conn
else:
    raise self.error
```

So if both happen in the same race window:

- `self.error = CancelledError(...)`
- `self.conn = ...`

then `self.conn` wins and the cancellation is lost.

# Relation to previous fixes

- [#509](https://github.com/psycopg/psycopg/issues/509) fixed the broader "cancelled task in async pool queue can consume a connection" problem by teaching the waiter to record `BaseException`.
- This looks like a narrower residual race in the same area: the waiter now records the cancellation, but still prefers `self.conn` over `self.error` afterward.
- [#1208](https://github.com/psycopg/psycopg/issues/1208) / [#1214]((withheld: the upstream fix is not part of the task)) seem to address other `CancelledError` paths such as check / rollback / lifecycle handling. Unless I missed something, they do not change `WaitingClient.wait()` itself.

# Possible fix direction

One possible direction would be to avoid preferring `self.conn` over an already recorded `CancelledError`.

However, I suspect that cannot be fixed in `wait()` alone without also considering the connection handoff / return-to-pool path, because by the time `wait()` returns, the pool may already consider that connection assigned to this waiter.

# Notes

This repro uses private internals only to make the race deterministic and self-contained.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hello,

thank you for the in-depth analysis.

Sounds like we can reverse the checks as you suggest in

https://github.com/psycopg/psycopg/blob/811f23fb54c2af4b56be0ba2aaecea932b8e20fe/psycopg_pool/psycopg_pool/pool_async.py#L960-L964

And replace it with:

```python
        if self.error:
            raise self.error
        else:
            assert self.conn
            return self.conn
```

and then we need to deal with the possible case of both connection and error set in:

https://github.com/psycopg/psycopg/blob/811f23fb54c2af4b56be0ba2aaecea932b8e20fe/psycopg_pool/psycopg_pool/pool_async.py#L298-L302

I think in the except we may run before raising:

```python
if pos.conn:
    self.run_task(ReturnConnection(self, pos.conn, from_getconn=True))
```

so that even if we are in the client task which has been cancelled this will have a chance of running in a task of its own.

What do you think?

It might be useful to set up a repro for this case, even by instrumenting the pool code for example by setting an Event to make a pause and making the race reproducible.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
