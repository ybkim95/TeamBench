# GH509_django_20028: Refs #28877 -- Added special ordinal context when humanizing value 1. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

In french we need to specialize 1st which does not work like 81st, it's 1<sup>er</sup> and 81<sup>ième</sup>. For zero is tricky but it's attested that some use 0<sup>ième</sup>.

Also fixed 101 that was tested to be `101er` while in french it's `101e` (sourced in my commit).

#### Checklist
- [x] This PR targets the `main` branch. <!-- Backports will be evaluated and done by mergers, when necessary. -->
- [x] The commit message is written in past tense, mentions the ticket number, and ends with a period.
- [ ] I have checked the "Has patch" ticket flag in the Trac system.
- [x] I have added or updated relevant tests.
- [ ] I have added or updated relevant docs, including release notes if applicable.
- [ ] I have attached screenshots in both light and dark modes for any UI changes.

## PR Review Comments

**[user]** on `django/contrib/humanize/templatetags/humanize.py`:

This needs an ending dot:

```suggestion
        # Translators: Ordinal format when value is 1 (1st).
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
