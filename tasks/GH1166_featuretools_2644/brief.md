        # GH1166_featuretools_2644: Fix for latest deps for woodwork 0.28.0 (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest featuretools/tests/entityset_tests/test_serialization.py featuretools/tests/primitive_tests/test_feature_serialization.py featuretools/tests/primitive_tests/transform_primitive_tests/test_datetoholiday_primitive.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
