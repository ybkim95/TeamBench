# GH444_arrow_1184: Improve "ago" translation to Greek — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/arrow-py/arrow

## PR Description

## Pull Request Checklist

<!-- Check boxes by placing an x in the brackets like this: [x] -->
- [x] 🧪  Added **tests** for changed code.
- [x] 🛠️  All tests **pass** when run locally (run `tox` or `make test` to find out!).
- [x] 🧹  All linting checks **pass** when run locally (run `tox -e lint` or `make lint` to find out!).
- [ ] 📚  Updated **documentation** for changed code.
- [x] ⏩  Code is **up-to-date** with the `master` branch.

## Description of Changes

Hello and thanks for this library! While trying to migrate from `humanize` package to `arrow`, I executed

```
>>> arrow.get('2013-05-11T21:23:58.970460+07:00').humanize()
'11 years ago'
>>> arrow.get('2013-05-11T21:23:58.970460+07:00').humanize(locale='el')
'11 χρόνια πριν'
```

The later is printed by `humanize` as
```
'πριν από 11 χρόνια'
```
which is more natural/correct in Greek.

https://github.com/python-humanize/humanize/blob/4da8299fdcf9ad0c56be082b42ee7bee14ee4c4e/src/humanize/locale/el_GR/LC_MESSAGES/humanize.po#L344

Other than that, I fixed Greek abbreviated May accent, so as to be aligned with the full name 15 lines above.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
