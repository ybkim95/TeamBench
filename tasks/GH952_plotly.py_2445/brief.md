        # GH952_plotly.py_2445: Fix FigureWidget attribute error on wildcard import with ipywidgets not installed (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Verification

        Run the test suite to confirm your fix:

        ```
        pytest packages/python/plotly/plotly/tests/test_core/test_figure_widget_backend/test_missing_ipywigets.py packages/python/plotly/plotly/tests/test_core/test_figure_widget_backend/test_validate_no_frames.py -x -q
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
