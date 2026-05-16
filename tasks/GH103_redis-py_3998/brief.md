# Redis-Py 3998 — Bug Fix

- PR: https://github.com/redis/redis-py/pull/3998

The Planner will analyze the root cause and provide guidance.
Follow the Planner's instructions to fix the issue.

## Files That May Need Changes

        - `redis/asyncio/connection.py`
- `redis/connection.py`

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/test_asyncio/test_connection_pool.py tests/test_connection_pool.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.

## Verification
Run the test suite to verify your fix.
Do NOT modify test files.
