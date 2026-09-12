# GH294_sktime_7844: [BUG] Fix failing tests for pytorch forecasting models. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/1234
- Repo: https://github.com/sktime/sktime

## Issue Description

Fixes #1043 

Removed methods load_UCR_UEA_dataset & _load_dataset from datasets/base.py and moved them to utils/data_io.py

## PR Review Comments

**[user]** on `sktime/forecasting/tests/test_all_forecasters.py`:

changing the *default* is not a good idea due to downwards compatibility. Better: change the value in the *call*.

Alternatively, should we change `get_test_params` of the impacted estimators, to avoid changing tests for all other forecasters?

**[user]** on `.all-contributorsrc`:

can you order by alphabet?

**[user]** on `sktime/forecasting/tests/test_all_forecasters.py`:

> Alternatively, should we change `get_test_params` of the impacted estimators, to avoid changing tests for all other forecasters?

In pytorch forecasting models, with current test cases, `prediction length` is coming from `TEST_OOS_FHS` in https://github.com/sktime/sktime/forecasting/tests/_config.py and test cases cannot pass even with `context length=1` given in test_params. So imo this needs to be increased in tests file as done now.

**[user]** on `sktime/forecasting/tests/test_all_forecasters.py`:

could you explain to me the three integers (or more) that are clashing, and where exactly they are coming from?

**[user]** on `sktime/forecasting/tests/test_all_forecasters.py`:

**context_length**, **prediction_length** and **data_length** are clashing.
 
In **PyTorch Forecasting models**, **context_length** is set via `test_params`, while **prediction_length** and **data_length** come from test cases. If `context_length` is **1**, **training_data_length** still exceeds `context_length + prediction_length`, causing failures. Proper alignment is needed to resolve this issue.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
