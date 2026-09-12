        # GH923_pandas_64643: BUG: fix float-to-int64 OOB handling on ARM in to_datetime/to_timedelta (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest pandas/tests/tools/test_to_timedelta.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
