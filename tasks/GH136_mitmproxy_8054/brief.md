# Mitmproxy 8054 — Bug Fix

- PR: https://github.com/mitmproxy/mitmproxy/pull/8054

The Planner will analyze the root cause and provide guidance.
Follow the Planner's instructions to fix the issue.

## Files That May Need Changes

        - `mitmproxy/contentviews/__init__.py`
- `mitmproxy/contentviews/_view_zip.py`

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest test/mitmproxy/contentviews/test__view_zip.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.

## Verification
Run the test suite to verify your fix.
Do NOT modify test files.
