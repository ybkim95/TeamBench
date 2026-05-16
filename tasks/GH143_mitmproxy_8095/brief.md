# Mitmproxy 8095 — Bug Fix

- PR: https://github.com/mitmproxy/mitmproxy/pull/8095

The Planner will analyze the root cause and provide guidance.
Follow the Planner's instructions to fix the issue.

## Files That May Need Changes

        - `mitmproxy/tools/console/consoleaddons.py`
- `mitmproxy/tools/console/defaultkeys.py`
- `mitmproxy/tools/console/statusbar.py`

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest test/mitmproxy/tools/console/test_statusbar.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.

## Verification
Run the test suite to verify your fix.
Do NOT modify test files.
