# GH1170_FLAML_1520: Fix CatBoost.get_params() TypeError in test_regression — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

Recent CatBoost versions removed the `deep` parameter from `get_params()`, causing `test_regression` to fail when CatBoost is selected as the best model.

The test was calling `get_params("n_estimators")` where the string was silently consumed as the `deep` positional arg on sklearn-compatible models, but CatBoost now rejects it outright.

- Changed `automl.model.estimator.get_params("n_estimators")` → `automl.model.estimator.get_params().get("n_estimators")` on lines 57 and 89, which also corrects the original intent (variable is named `n_iter` but was storing the full params dict)

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>CatBoost.get_params() takes 1 positional argument but 2 were given</issue_title>
> <issue_description>Action failed links:
> https://github.com/microsoft/FLAML/actions/runs/22291488578/job/64479481448
> 
> https://github.com/microsoft/FLAML/actions/runs/22291488578/job/64479481495
> 
> https://github.com/microsoft/FLAML/actions/runs/22291488578/job/64479481548
> 
> FAILED test/automl/test_regression.py::TestRegression::test_regression - TypeError: CatBoost.get_params() takes 1 positional argument but 2 were given</issue_description>
> 
> <agent_instructions>Fix the test errors.</agent_instructions>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes microsoft/FLAML#1519

<!-- START COPILOT CODING AGENT TIPS -->
---

✨ Let Copilot coding agent [set things up for you](https://github.com/microsoft/FLAML/issues/new?title=✨+Set+up+Copilot+instructions&body=Configure%20instructions%20for%20this%20repository%20as%20documented%20in%20%5BBest%20practices%20for%20Copilot%20coding%20agent%20in%20your%20repository%5D%28https://gh.io/copilot-coding-agent-tips%29%2E%0A%0A%3COnboard%20this%20repo%3E&assignees=copilot) — coding agent works faster and does higher quality work when set up for your repo.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
