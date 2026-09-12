        # GH1057_ray_28511: [Tune] [PBT] Maintain consistent `Trial`/`TrialRunner` state when pausing and resuming trial (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest python/ray/tune/tests/test_trial_scheduler.py python/ray/tune/tests/test_trial_scheduler_pbt.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
