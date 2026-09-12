# GH260_attrs_1496: Fix `optional` validator to accept tuples of len > 1 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-attrs/attrs

## PR Description

# IMPORTANT
The pre-commit hooks are reverting my work-around for the "ty" issue, even with an attempted work around for the pre-commit issue. Rather than adding yet another work-around, I'm going to see what the maintainers suggest.

# Summary

Replaces #1495 (I renamed my branch, which closed the draft PR.)

The `optional` validator (`attrs.validators.optional`) should accept any `tuple` of validators, just as it accepts any `list` of validators. It looks like the peculiar type annotation syntax for variable-length `tuple`s (`tuple[<type>, ...]`) was overlooked, and the exactly-one-element form (`tuple[<type>]`) was inadvertently used instead.

The proposed change corrects the annotation.

# Pull Request Check List

<!--
This is just a friendly reminder about the most common mistakes.
Please make sure that you tick all boxes.
But please read our [contribution guide](https://github.com/python-attrs/attrs/blob/main/.github/CONTRIBUTING.md) at least once, it will save you unnecessary review cycles!

If an item doesn't apply to your pull request, **check it anyway** to make it apparent that there's nothing left to do.
If your pull request is a documentation fix or a trivial typo, feel free to delete the whole thing.
-->

- [x] Do **not** open pull requests from your `main` branch – [**use a separate branch**](https://hynek.me/articles/pull-requests-branch/)!
  - There's a ton of footguns waiting if you don't heed this warning. You can still go back to your project, create a branch from your main branch, push it, and open the pull request from the new branch.
  - This is not a pre-requisite for your pull request to be accepted, but **you have been warned**.
- (N/A) Added **tests** for changed code.
  Our CI fails if coverage is not 100%.
- [x] Changes or additions to public APIs are reflected in our type stubs (files ending in ``.pyi``).
    - [x] ...and used in the stub test file `typing-examples/baseline.py` or, if necessary, `typing-examples/mypy.py`.
    - (N/A) If they've been added to `attr/__init__.pyi`, they've *also* been re-imported in `attrs/__init__.pyi`.
- (N/A) Updated **documentation** for changed code.
    - New functions/classes have to be added to `docs/api.rst` by hand.
    - Changes to the signatures of `@attr.s()` and `@attrs.define()` have to be added by hand too.
    - Changed/added classes/methods/functions have appropriate `versionadded`, `versionchanged`, or `deprecated` [directives](http://www.sphinx-doc.org/en/stable/markup/para.html#directive-versionadded).
          The next version is the second number in the current release + 1.
          The first number represents the current year.
          So if the current version on PyPI is 22.2.0, the next version is gonna be 22.3.0.
          If the next version is the first in the new year, it'll be 23.1.0.
      - If something changed that affects both `attrs.define()` and `attr.s()`, you have to add version directives to both.
- (N/A) Documentation in `.rst` and `.md` files is written using [semantic newlines](https://rhodesmill.org/brandon/2012/one-sentence-per-line/).
- [x] Changes (and possible deprecations) have news fragments in [`changelog.d`](https://github.com/python-attrs/attrs/blob/main/changelog.d).
- [x] Consider granting [push permissions to the PR branch](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork), so maintainers can fix minor issues themselves without pestering you.

<!--
If you have *any* questions to *any* of the points above, just **submit and ask**!
This checklist is here to *help* you, not to deter you from contributing!
-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
