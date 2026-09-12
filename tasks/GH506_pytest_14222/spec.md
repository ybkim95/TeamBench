# GH506_pytest_14222: raises: add missing | metacharacter to is_fully_escaped and unescape — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

`is_fully_escaped` checks whether a match pattern body (inside `^...$`) contains only escaped regex metacharacters, so pytest knows it can treat it as a literal string for diff output. The current metacharacter list is:

```python
metacharacters = "{}()+.*?^$[]"
```

This is missing `|`, the regex alternation operator. A pattern like `^foo|bar$` would pass the `is_fully_escaped` check even though the `|` makes it a regex alternation rather than a literal. This causes `rawmatch` to be set to the unescaped value `foo|bar`, leading to a misleading diff in the failure message.

The `unescape` function has the same omission in its character class, so `\|` wouldn't be unescaped even if someone properly escaped it.

This adds `|` to both the metacharacter list in `is_fully_escaped` and the character class in `unescape`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
