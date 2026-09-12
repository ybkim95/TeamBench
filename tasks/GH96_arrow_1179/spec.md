# GH96_arrow_1179: Use zoneinfo for timezone handling instead of pytz — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/arrow-py/arrow/issues/1175
- Repo: https://github.com/arrow-py/arrow

## Issue Description

Switch to standard `zoneinfo` module.
Below may help  (withheld: the upstream fix is not part of the task)

```console
[tkloczko@pers-jacek arrow-1.3.0]$ grep -r pytz
CHANGELOG.rst:- [FIX] Fixed a bug that occurred when ``arrow.Arrow()`` was instantiated with a ``pytz`` tzinfo object.
CHANGELOG.rst:- [FIX] Fix pytz conversion error (Kudo)
README.rst:- Too many modules: datetime, time, calendar, dateutil, pytz and more
README.rst:- Support for ``dateutil``, ``pytz``, and ``ZoneInfo`` tzinfo objects
arrow/arrow.py:        # detect that tzinfo is a pytz object (issue #626)
requirements/requirements-tests.txt:pytz==2021.1
tests/test_arrow.py:import pytz
tests/test_arrow.py:    def test_init_pytz_timezone(self):
tests/test_arrow.py:            2013, 2, 2, 12, 30, 45, 999999, tzinfo=pytz.timezone("Europe/Paris")
tests/test_formatter.py:import pytz
tests/test_formatter.py:        dt = datetime(1986, 2, 14, tzinfo=pytz.timezone("UTC")).replace(
tests/utils.py:import pytz
tests/utils.py:    pytz_zones = set(pytz.all_timezones)
tests/utils.py:    return dateutil_zones.union(pytz_zones)
pyproject.toml:    "pytz==2021.1",
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] thanks for raising the issue. Contributions are welcome to add this functionality to Arrow :)

## PR Review Comments

**[user]** on `pyproject.toml`:

we need to add a dependency on the backport like this:
```
backports.zoneinfo = {version = "0.2.1", markers = "python_version < '3.9'"}
```

**[user]** on `tests/utils.py`:

Does this have the proper coverage for all timezones? We primarily used pytz to get greater coverage of time zones for the sake of tests

**[user]** on `tests/test_arrow.py`:

Can we add a separate test for pytz and another for zoneinfo? I don't think we should be removing pytz and closing the open issue for the sake of the tests. There is still a use-case for passing in a pytz timezone into Arrow, especially if someone has not yet adopted zoneinfo.

If pytz is not used in the core arrow code and only in the test code (it is only pulled in via `requirements-tests.txt`, I think we need another CR that focuses on adding support for Zoneinfo natively throughout rather than using dateutil, which is our primary means of doing timezones.

**[user]** on `tests/utils.py`:

I just compared them and it does have the same coverage as pytz (Windows 11). However, from the [zoneinfo docs](https://docs.python.org/3/library/zoneinfo.html#data-sources):

> The zoneinfo module does not directly provide time zone data, and instead pulls time zone information from the system time zone database or the first-party PyPI package [tzdata](https://pypi.org/project/tzdata/), if available. Some systems, including notably Windows systems, do not have an IANA database available, and so for projects targeting cross-platform compatibility that require time zone data, it is recommended to declare a dependency on tzdata. If neither system data nor tzdata are available, all calls to [ZoneInfo](https://docs.python.org/3/library/zoneinfo.html#zoneinfo.ZoneInfo) will raise [ZoneInfoNotFoundError](https://docs.python.org/3/library/zoneinfo.html#zoneinfo.ZoneInfoNotFoundError).

**[user]** on `tests/test_arrow.py`:

Sure

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
