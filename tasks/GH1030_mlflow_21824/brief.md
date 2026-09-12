        # GH1030_mlflow_21824: Fix tar path traversal vulnerability in `extract_archive_to_dir` (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/utils/test_file_utils.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
