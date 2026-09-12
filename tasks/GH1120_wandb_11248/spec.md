# GH1120_wandb_11248: fix: rewrite Api._parse_path and handle invalid paths — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Rewrites `Api._parse_path` to raise a `ValueError` for incorrect paths instead of succeeding or in some cases raising an `UnboundLocalError`.

Fixes WB-30289. Alternative to PR #11206.

One strange behavior of `_parse_path` was that it would sometimes set `project` to `id`:

```python
api = wandb.Api(overrides={"entity": "test-entity"})
api._parse_path("run")   # "test-entity", "run", "run"
```

There was even a test for this, `test_parse_path_proj`, but based on the description of PR #6858, I think this was unintentional. `_parse_path` is used in three places, none of which benefit from this behavior: `api.reports()`, `api.run()`, `api.sweep()`. I changed this case to raise a `ValueError` instead.

I chose to completely rewrite `_parse_path` and realized this was the right choice when it took me over an hour instead of 10 minutes. The longer you look at the original code, the more messed up it is.

I started with an early-return pattern that avoided `else` and `elif` but switched to an if-else pattern with a single return to consolidate validations at the end. The original code has some hidden `if`s in the middle of what look like `if-else` chains.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
