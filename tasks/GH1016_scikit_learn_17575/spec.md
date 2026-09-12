# GH1016_scikit_learn_17575: FIX escape double quotes when exporting tree with Graphviz — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

#### Reference Issues/PRs


#### What does this implement/fix? Explain your changes.
Double quotes in graphviz labels need escaping. Escape class and feature
names to avoid breaking the result.

#### Any other comments?

## PR Review Comments

**[user]** on `sklearn/tree/_export.py`:

Why is this `str()` call required? Can `feature_names` be integers in this context?

**[user]** on `sklearn/tree/tests/test_export.py`:

To improve readability may I suggest the following idiom:

```python
from textwrap import dedent

...
    contents1 = export_graphviz(clf,
                                feature_names=["feature\"0\"", "feature\"1\""],
                                out_file=None)
    contents2 = dedent("""\
        digraph Tree {
        node [shape=box] ;
        ...
        }""")


```

**[user]** on `sklearn/tree/_export.py`:

I _think_ they should always be strings, and if they are not, they'll probably cause a lot of other problems. I'll remove the call.

**[user]** on `sklearn/tree/tests/test_export.py`:

I was hesitant to use a convention different from the surrounding code, since all test cases in the file use this form. Do you think it's worth changing only for this new case?

**[user]** on `sklearn/tree/tests/test_export.py`:

[user] So would you prefer the code using the same convention as the surrounding test cases? Or the one you suggested?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
