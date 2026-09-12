        # GH1117_dask_10043: Avoid using `dd.shuffle` in groupby-apply (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest dask/dataframe/tests/test_groupby.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
