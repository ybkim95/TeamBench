# GH736_AQUA_2170: Show a logging error instead a raise for empty data reader retrival — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/DestinE-Climate-DT/AQUA/issues/2168
- Repo: https://github.com/DestinE-Climate-DT/AQUA

## Issue Description

In working with  EC-Earth data I have realized that #2141  actually does more harm than good. It breaks the aqua-analysis workflow if a variable happens not to exist. Sometimes (at least this is what I do with EC-Earth data because of how the sources are defined) I launch an analysis not expecting all figures to be produced. With this change instead an exception is raised and the analysis stops.
I would simply log an error which complains that data are missing but then simply let the code continue!

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I see the issue, I also think the diagnostics should have a try except structure that allows one analysis to fail while keeping the others (e.g. one timeseries is failing should not make all the timeseries fail). If some diagnostics does not handle this properly let's open an issue about it.

## PR Review Comments

**[user]** on `src/aqua/reader/reader.py`:

It would be helpful to print th in the log message WHICH varname it tried to read

**[user]** on `src/aqua/reader/reader.py`:

Do you still need the `
from aqua.exceptions import NoDataError`
at the top?

**[user]** on `src/aqua/reader/reader.py`:

(withheld: the upstream fix is not part of the task)#discussion_r2300125792 -> done

**[user]** on `src/aqua/reader/reader.py`:

About `NoDataError`, it is also used in line 162: `raise NoDataError(f"No NetCDF files available for ....`

**[user]** on `src/aqua/reader/reader.py`:

Access to data.coords will trigger a raise if data is None.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
