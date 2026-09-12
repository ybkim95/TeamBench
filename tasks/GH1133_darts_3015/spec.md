# GH1133_darts_3015: Fix timezone type hint — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2926
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**

`TimeSeries.add_datetime_attribute` takes a tz parameter with typing `str | None`. However, this argument is simply passed to `tz_convert`, which can take the following type: `TimeZones: TypeAlias = str | tzinfo | None | int` (according to Pandas-Stubs [here](https://github.com/pandas-dev/pandas-stubs/blob/8ec49016cdb89b0e42d26c76e2eb964aaca61e70/pandas-stubs/core/indexes/accessors.pyi#L236) and [here](https://github.com/pandas-dev/pandas-stubs/blob/8ec49016cdb89b0e42d26c76e2eb964aaca61e70/pandas-stubs/_typing.pyi#L1052)). The chain is `TimeSeries.add_datetime_attribute` -> `darts.utils.timeseries_generation.datetime_attribute_timeseries` -> `darts.utils.timeseries_generation._process_time_index` -> `DatetimeIndex.tz_convert` (ending in the following snippet):

https://github.com/unit8co/darts/blob/97f986a1ac60c3c69617296545099b971edad085/darts/utils/timeseries_generation.py#L966

In my opinion, all of those darts methods in the chain should take `str | tzinfo | None | int` or the `TimeZones` alias.

**To Reproduce**
The following works but pyright complains about a typing mismatch since `tz` supposedly only takes `str`.

```python
import pytz
from darts.utils.timeseries_generation import random_walk_timeseries

random_walk_timeseries(length=100, freq="1h").add_datetime_attribute("day", tz=pytz.timezone("Europe/Zurich"))
```

**Expected behavior**
It works and is correctly type-checked.

**System (please complete the following information):**
 - Python version: 3.12
 - darts version 0.38.0

**Additional context**

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] and thanks for raising this issue. Yes, that sounds reasonable, would you like to contribute to this? It would also be great to find and fix other occurrences of `tz` usage in Darts. What do you think?

### Comment 2 ([user]):

Agree. A few test cases using tzinfo instead of str would probably also make sense.  
Unfortunately, I'm a bit strapped for time at the moment, so I don't think I'll be able to contribute it myself. If I do start, I will write a comment here, but I'm fine with someone else doing it.

### Comment 3 ([user]):

As written [here](already), please do not use Any for the typing :/ tz_convert clearly states which types are supported and I also outlined that in my issue.

str, zoneinfo.ZoneInfo, pytz.timezone, dateutil.tz.tzfile, datetime.tzinfo or None

Using Any only further contributes to the inconsistent typing in this library and most static type checkers like pyright will complain!

I think it's worth reopening this issue as it's not solved completely.

### Comment 4 ([user]):

[user], I opened #3035 which prepares everything for the new release, and also should fix the time zone issue.

I created a new type alias that should cover the pandas cases. Note that `zoneinfo.ZoneInfo`, `pytz.timezone`, `dateutil.tz.tzfile` are all sub cases of `datetime.tzinfo`. Therefore, I only added datetime.tzinfo. Also, pytz.timezone is a function and not a correct type. Adding a type alias for that will complain.

```
TimeZone: TypeAlias = str | datetime.tzinfo | None
```

### Comment 5 ([user]):

Amazing, thank you!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
