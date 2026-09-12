        # GH931_mlflow_21721: Fix trace export DB contention by disabling incremental span export for gateway (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/gateway/test_tracing_utils.py tests/server/test_init.py tests/tracing/export/test_mlflow_v3_attachments.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
