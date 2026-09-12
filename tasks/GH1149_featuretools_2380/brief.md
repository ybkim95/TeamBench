        # GH1149_featuretools_2380: Fix `base_of_exclude` handling (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest featuretools/tests/conftest.py featuretools/tests/primitive_tests/test_agg_feats.py featuretools/tests/primitive_tests/test_feature_base.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
