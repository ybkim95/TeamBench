# GH1015_scikit_learn_28095: FIX divide by zero in line search of GradientBoostingClassifier — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

#### Reference Issues/PRs
This is a fix introduces in #26278 and #27312.

#### What does this implement/fix? Explain your changes.
This PR fixes a situation where the probability in a line search step of `GradientBoostingClassifier` reaches exactly `0` or `1` leading  to a division by zero.

The first commit adds the test. CI will prove that it failed. After that, a fix will be added.

#### Any other comments?
[user] (withheld: the upstream fix is not part of the task)#pullrequestreview-1811388451
> Would it make sense to include such a case as a public API level non-regression tests?

Yes! I'm convinced now.
[user] [user] This might be worth to be included in 1.4.0 or, later, in 1.4.1.


#### Some history
The check `denominator == 0` was introduces in (withheld: the upstream fix is not part of the task).
The check `abs(denominator) < 1e-150` was introduces in (withheld: the upstream fix is not part of the task).
#26278 added `_safe_divide` which handled `denominator == 0` correctly, but not on Pyodide.
#27312 fixed the Pyodide thing, but introduced a `RuntimeWarnings`.
This PR puts back the `abs(denominator) < 1e-150` without warnings.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
