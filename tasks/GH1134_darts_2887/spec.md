# GH1134_darts_2887: Fix/Quantile_Label_Name — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2879
- Repo: https://github.com/unit8co/darts

## Issue Description

Hi there,
just a small note: when using `TimeSeries.quantile()`, the generated component names round quantile levels to 2 decimals (e.g., `0.025 → q0.03`, `0.975 → q0.97`). This is a bit inconvenient in cases where the exact quantile values matter (e.g., 95% CI bounds). Not a big issue - just wanted to flag it because I ran into it today :)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] and thanks for raising this issue. Indeed we could increase the decimal places to 3 (e.g. 0.975). 
We do need to fix the number of decimals though since we rely on the generated quantile component names to follow a specific naming convention:
- quantile models (e.g. models that use a quantile likelihood) give quantile component names to the forecast (e.g. f`component_name_q{0.50}`
- metrics expect the quantile component names with `*_q{0.50}`
- ...

I believe 3 decimals should cover most use cases. What do you think?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
