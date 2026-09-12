        # GH976_scikit_learn_16849: BUG Fix instability issue of ARDRegression (with speedup) (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest sklearn/linear_model/tests/test_bayes.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
