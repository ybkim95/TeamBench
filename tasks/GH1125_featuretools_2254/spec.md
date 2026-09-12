# GH1125_featuretools_2254: Fix holidays library failure with lookups — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2253
- Repo: https://github.com/alteryx/featuretools

## Issue Description

The holidays library recently updated (0.15) and in doing so moved the countries of the UK into subdivisions.  There was also a fix wrt Canadian Boxing day.  These changes are causing the federal holiday and days to holiday tests to fail.

#### Code Sample, a copy-pastable example to reproduce your bug.

```python
def test_holiday_out_of_range():
    date_to_holiday = DistanceToHoliday("Boxing Day", country="Canada")

    array = pd.Series(
        [
            datetime(2010, 1, 1),
            datetime(2012, 5, 31),
            datetime(2017, 7, 31),
            datetime(2020, 12, 31),
        ],
    )
    answer = pd.Series([np.nan, 209, 148, np.nan])    # 209 should be -157 with the update
    pd.testing.assert_series_equal(date_to_holiday(array), answer, check_names=False)
```
and
```python
def test_multiple_countries():
    dth_mexico = DateToHoliday(country="Mexico")

    case = pd.Series([datetime(2000, 9, 16), datetime(2005, 1, 1)])
    assert len(dth_mexico(case)) > 1

    dth_india = DateToHoliday(country="IND")
    case = pd.Series([datetime(2048, 1, 1), datetime(2048, 10, 2)])
    assert len(dth_india(case)) > 1

    dth_uk = DateToHoliday(country="UK")
    case = pd.Series([datetime(2048, 3, 17), datetime(2048, 4, 6)])
    assert len(dth_uk(case)) > 1

    countries = [
        "Argentina",
        "AU",
        "Austria",
        "BY",
        "Belgium",
        "Brazil",
        "Canada",
        "Colombia",
        "Croatia",
        "England",
        "Finland",
        "FRA",
        "Germany",
        "Germany",
        "Italy",
        "NewZealand",
        "PortugalExt",
        "PTE",
        "Spain",
        "ES",
        "Switzerland",
        "UnitedStates",
        "US",
        "UK",
        "UA",
        "CH",
        "SE",
        "ZA",
    ]
    for x in countries:
        DateToHoliday(country=x)
```

Output:

```
featuretools/tests/primitive_tests/test_datetoholiday_primitive.py:111: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
featuretools/primitives/standard/datetime_transform_primitives.py:93: in __init__
    self.holidayUtil = HolidayUtil(country)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <featuretools.primitives.utils.HolidayUtil object at 0x7f1b10ec0fa0>
country = 'England'

    def __init__(self, country="US"):
        try:
            holidays.country_holidays(country=country)
        except NotImplementedError:
            available_countries = (
                "https://github.com/dr-prodigy/python-holidays#available-countries"
            )
            error = "must be one of the available countries:\n%s" % available_countries
>           raise ValueError(error)
E           ValueError: must be one of the available countries:
E           https://github.com/dr-prodigy/python-holidays#available-countries
```

## PR Review Comments

**[user]** on `docs/source/release_notes.rst`:

```suggestion
        * Fix compatibility issues with holidays 0.15 (:pr:`2254`)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
