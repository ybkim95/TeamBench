# GH610_sktime_7872: [BUG] MAPA forecaster - missing clone, using exogenous data — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/7822
- Repo: https://github.com/sktime/sktime

## Issue Description

There are two bugs in the `MAPAforecaster` that should be fixed:

* if a `base_forecaster` is passed, it should be cloned and not used directly
* `base_forecaster` should be passed the `X`, exogenous data

FYI [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I will take this up after I am done with another issue, until then if anyone else wants to go for it feel free!

## PR Review Comments

**[user]** on `sktime/forecasting/mapa.py`:

You cannot change the `self.params`, See the extension template

https://github.com/sktime/sktime/blob/cc92e8053da45b20ce673aaf2e3bbc4ed5bbcf2c/extension_templates/forecasting_simple.py#L137-L138

**[user]** on `sktime/forecasting/mapa.py`:

Will change that! Had asked you this on discord and made the change based on that but it was probably miscommunication.

**[user]** on `sktime/forecasting/mapa.py`:

A doubt: why are we removing this? is this also causing the issue? changing series to df?

**[user]** on `sktime/forecasting/mapa.py`:

why are we removing the `forecast_values`?

**[user]** on `sktime/forecasting/mapa.py`:

Not a needed variable, though it's not a bug so I'll revert it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
