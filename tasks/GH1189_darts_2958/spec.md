# GH1189_darts_2958: fix PLForecastingModel.configure_torch_metrics() with updated args — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/unit8co/darts

## PR Description

Checklist before merging this PR:
- [x] Mentioned all issues that this PR fixes or addresses.
- [x] Summarized the updates of this PR under **Summary**.
- [x] Added an entry under **Unreleased** in the [Changelog](../CHANGELOG.md).

### Summary

simplify our wrapper method configure_torch_metrics(), delegate the init and error handling to the torchmetrics.MetricCollection().

The problem was that our if-elif handling got obsolete wrt the MetricCollection capabilities.

Fixed: now we support eg. Dict[str, Metric].

## PR Review Comments

**[user]** on `darts/models/forecasting/pl_forecasting_module.py`:

MetricsCollection() handles all the supported cases, and tells us correctly if it does not handle some format.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
