        # GH903_transformers_33200: 🚨🚨🚨 [SuperPoint] Fix keypoint coordinate output and add post processing (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest tests/models/superpoint/test_image_processing_superpoint.py tests/models/superpoint/test_modeling_superpoint.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
