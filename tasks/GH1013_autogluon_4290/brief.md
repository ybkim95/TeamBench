        # GH1013_autogluon_4290: [tabular] Fix Stacker max_models logic (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest features/tests/features/test_feature_metadata.py tabular/tests/unittests/models/advanced/test_stack_feature_usage.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
