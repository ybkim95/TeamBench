# GH290_attrs_1471: Improve type hinting of or_ — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-attrs/attrs

## PR Description

# Summary

The type hinting for the or_ function presumes that all validators used have the same input type though that is not a requirement. This adds several overloads and a fall-through Any type catch-all to the or_ function that will help satisfy the type check.

# Pull Request Check List

- [x] Do **not** open pull requests from your `main` branch – **use a separate branch**!
  - There's a ton of footguns waiting if you don't heed this warning. You can still go back to your project, create a branch from your main branch, push it, and open the pull request from the new branch.
  - This is not a pre-requisite for your pull request to be accepted, but **you have been warned**.
- [ ] Added **tests** for changed code.
  Our CI fails if coverage is not 100%.
- [ ] New features have been added to our [Hypothesis testing strategy](https://github.com/python-attrs/attrs/blob/main/tests/strategies.py).
- [ ] Changes or additions to public APIs are reflected in our type stubs (files ending in ``.pyi``).
    - [x] ...and used in the stub test file `tests/typing_example.py`.
    - [x] If they've been added to `attr/__init__.pyi`, they've *also* been re-imported in `attrs/__init__.pyi`.
- [ ] Updated **documentation** for changed code.
    - [ ] New functions/classes have to be added to `docs/api.rst` by hand.
    - [ ] Changes to the signatures of `@attr.s()` and `@attrs.define()` have to be added by hand too.
    - [ ] Changed/added classes/methods/functions have appropriate `versionadded`, `versionchanged`, or `deprecated` [directives](http://www.sphinx-doc.org/en/stable/markup/para.html#directive-versionadded).
          The next version is the second number in the current release + 1.
          The first number represents the current year.
          So if the current version on PyPI is 22.2.0, the next version is gonna be 22.3.0.
          If the next version is the first in the new year, it'll be 23.1.0.
      - [ ] If something changed that affects both `attrs.define()` and `attr.s()`, you have to add version directives to both.
- [ ] Documentation in `.rst` and `.md` files is written using [semantic newlines](https://rhodesmill.org/brandon/2012/one-sentence-per-line/).
- [ ] Changes (and possible deprecations) have news fragments in [`changelog.d`](https://github.com/python-attrs/attrs/blob/main/changelog.d).
- [ ] Consider granting [push permissions to the PR branch](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork), so maintainers can fix minor issues themselves without pestering you.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
