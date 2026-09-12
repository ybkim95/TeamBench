# GH1166_featuretools_2644: Fix for latest deps for woodwork 0.28.0 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2650
- Repo: https://github.com/alteryx/featuretools

## PR Description

Closes #2650

Updates to work with latest deps

## PR Review Comments

**[user]** on `.github/workflows/tests_with_latest_deps.yaml`:

The windows tests were erroring with `Miniconda3-latest-Windows-x86_64.exe hashes do not match`m so I updated the hash with the 3.11 windowns installer hash at https://docs.anaconda.com/free/miniconda/miniconda-other-installer-links/

**[user]** on `featuretools/primitives/standard/transform/datetime/date_to_holiday.py`:

The latest release of `holidays` changed how Canadian labor day holiday is spelled to no longer use the Canadian `Labour` spelling. Rather than update the min version of holidays, I just changed the holiday we're checking here.

**[user]** on `featuretools/tests/entityset_tests/test_serialization.py`:

Break change to moto for which we had to update the min moto version to `5.0.0`

**[user]** on `pyproject.toml`:

With pandas `2.2.0`, the test `test_entry_point` is failing with `TypeError: category dtype does not support aggregation 'mean'` ([link](https://github.com/alteryx/featuretools/actions/runs/7803132816/job/21282196680#step:10:1310)). I did a bit of testing to confirm that this happens with `dfs(entityset=pd_es, target_dataframe_name="customers")` and isn't something specific to that test. I haven't figure out why this doesn't occur in other tests.

**[user]** on `pyproject.toml`:

Preemptively pinning numpy below version 2.0, which hasn't come out yet but which will have breaking changes

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
