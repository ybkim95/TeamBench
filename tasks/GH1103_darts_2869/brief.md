        # GH1103_darts_2869: Fix/hfc retrain with tfm and ocs (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest darts/tests/utils/historical_forecasts/test_historical_forecasts.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
