        # GH1000_numpy_19869: BUG: ensure np.median does not drop subclass for NaN result. (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest numpy/lib/tests/test_function_base.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
