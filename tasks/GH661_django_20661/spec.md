# GH661_django_20661: Refs #36883 -- Split monolithic aggregation/lookup/queries tests. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

Motivation: test_ordering_with_extra isn't supported by MongoDB because of QuerySet.extra(), but the part before it is.

And incidentally, I noticed the additional test in aggregation_regress after 229d026207dddd5b184e9569f104d315f1c79c81 was merged.

todo: many_to_one.tests.ManyToOneTests.test_selects, test_reverse_selects

## PR Review Comments

**[user]** on `tests/many_to_one/tests.py`:

This was previously: `where=["many_to_one_reporter.last_name='%s'" % "Smith"]` (no `params`) which amounts to the same as the previous assertion.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
