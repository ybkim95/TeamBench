        # GH989_great_expectati_8084: [BUGFIX] Fix Update Checkpoint for Cloud (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/data_context/cloud_data_context/test_checkpoint_crud.py tests/data_context/cloud_data_context/test_expectation_suite_crud.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
