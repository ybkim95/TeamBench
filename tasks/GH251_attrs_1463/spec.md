# GH251_attrs_1463: Improve performance of asdict in the common case — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-attrs/attrs

## PR Description

# Summary

We improve performance of `attrs.asdict` by:

* Using a fast check for atomic types (list int, float or str)
* Using `issubclass` instead of `isinstance` for various type checks

Benchmark:
```
asdict: Mean +- std dev: [main] 4.07 us +- 0.41 us -> [pr] 2.48 us +- 0.21 us: 1.64x faster

Benchmark hidden because not significant (1): instance creation

Geometric mean: 1.28x faster
```
<details><summary>Test script</summary>

```
import pyperf

setup = """
from attrs import define, asdict

@define
class Simple:
     i : int
     s : str
     l : list

s = Simple(10, 'hi', [3, 1, 4])

"""

runner = pyperf.Runner()
runner.timeit(name="instance creation", stmt="Simple(10, 'hi', [3, 1, 4])", setup=setup)
runner.timeit(name="asdict", stmt="asdict(s)", setup=setup)
```
</details>

Notes:

* a similar PR was added to cpython dataclasses as well (withheld: the upstream fix is not part of the task)
* With a similar approach we can improve performance of `astuple`. That is left to a separate PR though. Also see https://github.com/python-attrs/attrs/issues/1129

# Pull Request Check List

<!--
This is just a friendly reminder about the most common mistakes.
Please make sure that you tick all boxes.
But please read our [contribution guide](https://github.com/python-attrs/attrs/blob/main/.github/CONTRIBUTING.md) at least once, it will save you unnecessary review cycles!

If an item doesn't apply to your pull request, **check it anyway** to make it apparent that there's nothing left to do.
If your pull request is a documentation fix or a trivial typo, feel free to delete the whole thing.
-->

- [x] Do **not** open pull requests from your `main` branch – **use a separate branch**!
  - There's a ton of footguns waiting if you don't heed this warning. You can still go back to your project, create a branch from your main branch, push it, and open the pull request from the new branch.
  - This is not a pre-requisite for your pull request to be accepted, but **you have been warned**.
- [x] Added **tests** for changed code.
  Our CI fails if coverage is not 100%.
- [x] New features have been added to our [Hypothesis testing strategy](https://github.com/python-attrs/attrs/blob/main/tests/strategies.py).
- [x] Changes or additions to public APIs are reflected in our type stubs (files ending in ``.pyi``).
    - [x] ...and used in the stub test file `tests/typing_example.py`.
    - [x] If they've been added to `attr/__init__.pyi`, they've *also* been re-imported in `attrs/__init__.pyi`.
- [x] Updated **documentation** for changed code.
    - [x] New functions/classes have to be added to `docs/api.rst` by hand.
    - [x] Changes to the signatures of `@attr.s()` and `@attrs.define()` have to be added by hand too.
    - [x] Changed/added classes/methods/functions have appropriate `versionadded`, `versionchanged`, or `deprecated` [directives](http://www.sphinx-doc.org/en/stable/markup/para.html#directive-versionadded).
          The next version is the second number in the current release + 1.
          The first number represents the current year.
          So if the current version on PyPI is 22.2.0, the next version is gonna be 22.3.0.
          If the next version is the first in the new year, it'll be 23.1.0.
      - [x] If something changed that affects both `attrs.define()` and `attr.s()`, you have to add version directives to both.
- [x] Documentation in `.rst` and `.md` files is written using [semantic newlines](https://rhodesmill.org/brandon/2012/one-sentence-per-line/).
- [x] Changes (and possible deprecations) have news fragments in [`changelog.d`](https://github.com/python-attrs/attrs/blob/main/changelog.d).
- [x] Consider granting [push permissions to the PR branch](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork), so maintainers can fix minor issues themselves without pestering you.

<!--
If you have *any* questions to *any* of the points above, just **submit and ask**!
This checklist is here to *help* you, not to deter you from contributing!
-->

## PR Review Comments

**[user]** on `tests/test_funcs.py`:

This doesn't conform with our docstring standard and proves why it's important :)

What exactly is tested here?  (c.f. https://hynek.me/articles/document-your-tests/ for more context)

**[user]** on `tests/test_funcs.py`:

The method name and docstring indeed did not match, I updated the name.

I was trying to test the `else` branch inside the recursive part of the `asdict` implementation. The branch covers non-atomic objects minus some container types. I could add some more tests (e.g. `fraction.Fraction`) if needed.

**[user]** on `tests/test_funcs.py`:

OK, I've fixed the docstring as well as I could myself!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
