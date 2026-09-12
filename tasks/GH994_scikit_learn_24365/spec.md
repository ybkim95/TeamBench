# GH994_scikit_learn_24365: FIX log_loss at boundaries and integer y_pred — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

#### Reference Issues/PRs
None

#### What does this implement/fix? Explain your changes.
This PR fixes `log_loss` for cases at the boundaries like
```
assert log_loss([0, 1], [0, 1], eps=0) == 0
assert log_loss([0, 1], [0, 0], eps=0) == np.inf
assert log_loss([0, 1], [1, 1], eps=0) == np.inf
```

Note that this also fixes the bug of not allowing integer `y_pred` as in the test cases above.

Old behaviour:
<details>

```python
from sklearn.metrics import log_loss

log_loss([0, 1], [0, 1], eps=0)
```
`UFuncTypeError: Cannot cast ufunc 'true_divide' output from dtype('float64') to dtype('int64') with casting rule 'same_kind'`
```python
log_loss([0, 1.], [0, 1.], eps=0)
```
`nan`
```python
log_loss([0, 1.], [0, 0.], eps=0)
```
`nan`
```python
log_loss([0, 1.], [1, 1.], eps=0)
```
`nan`


</details>

## PR Review Comments

**[user]** on `sklearn/metrics/_classification.py`:

What's the reason for not always dividing by `y_pred_sum`?

**[user]** on `sklearn/metrics/tests/test_classification.py`:

leftover

**[user]** on `sklearn/metrics/_classification.py`:

I thought about numerical rounding effects, but that may not be needed. I'll remove it.

BTW, I was very surprised when I found out this normalization step. Do you know the reason/use case for it? Strictly speaking, it gives wrong results.

**[user]** on `sklearn/metrics/tests/test_classification.py`:

No leftover. It is a comment on how to arrive at the magic umber 1.8817971.

**[user]** on `sklearn/metrics/_classification.py`:

Why are you saying it gives wrong results? `y_pred` are probabilities that must sum to one, so it does seem reasonable to me to enforce that constraint in some way.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
