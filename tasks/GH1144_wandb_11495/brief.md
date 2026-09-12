        # GH1144_wandb_11495: chore: clean up dev requirements and fix bokeh 3.9 serialization issue (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/system_tests/test_core/test_data_types_full.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
