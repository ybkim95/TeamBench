        # GH943_great_expectati_7881: [BUGFIX] Delete ExpectationSuite by name in GX Cloud (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/data_context/cloud_data_context/test_expectation_suite_crud.py tests/data_context/store/test_gx_cloud_store_backend.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
