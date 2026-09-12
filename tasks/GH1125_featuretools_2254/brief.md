        # GH1125_featuretools_2254: Fix holidays library failure with lookups (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest featuretools/tests/primitive_tests/test_distancetoholiday_primitive.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
