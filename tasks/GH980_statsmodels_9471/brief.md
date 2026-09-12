        # GH980_statsmodels_9471: Fix formula eval depth in select models (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest statsmodels/discrete/tests/test_conditional.py statsmodels/duration/tests/test_phreg.py statsmodels/genmod/tests/test_gee.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
