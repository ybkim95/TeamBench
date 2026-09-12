        # GH1101_darts_2811: Fix SKLearn Multioutput string representation (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest darts/tests/models/forecasting/test_sklearn_models.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
