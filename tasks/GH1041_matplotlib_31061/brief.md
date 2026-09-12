        # GH1041_matplotlib_31061: BUG: Fix text appearing far outside valid axis scale range (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest lib/matplotlib/tests/test_text.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
