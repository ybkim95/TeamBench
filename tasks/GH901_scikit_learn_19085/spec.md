# GH901_scikit_learn_19085: FIX Fix recall in multilabel classification when true labels are all negative — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/8245
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

<!--
If your issue is a usage question, submit it here instead:
- StackOverflow with the scikit-learn tag: http://stackoverflow.com/questions/tagged/scikit-learn
- Mailing List: https://mail.python.org/mailman/listinfo/scikit-learn
For more information, see User Questions: http://scikit-learn.org/stable/support.html#user-questions
-->

<!-- Instructions For Filing a Bug: https://github.com/scikit-learn/scikit-learn/blob/master/CONTRIBUTING.md#filing-bugs -->

#### Description
<!-- Example: Joblib Error thrown when calling fit on LatentDirichletAllocation with evaluate_every > 0-->
`average_precision_score` does not return correct AP when `y_true` is all negative labels.
#### Steps/Code to Reproduce
<!--
Example:
```
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

docs = ["Help I have a bug" for i in range(1000)]

vectorizer = CountVectorizer(input=docs, analyzer='word')
lda_features = vectorizer.fit_transform(docs)

lda_model = LatentDirichletAllocation(
    n_topics=10,
    learning_method='online',
    evaluate_every=10,
    n_jobs=4,
)
model = lda_model.fit(lda_features)
```
If the code is too long, feel free to put it in a public gist and link
it in the issue: https://gist.github.com
-->
One can run this piece of dummy code:

    sklearn.metrics.ranking.average_precision_score(np.array([0, 0, 0, 0, 0]), np.array([0.1, 0.1, 0.1, 0.1, 0.1]))

It returns `nan` instead the correct value with the error: 
```
RuntimeWarning: invalid value encountered in true_divide
recall = tps / tps[-1]
```

#### Expected Results
<!-- Example: No error is thrown. Please paste or describe the expected results.-->
As per this [Stackoverflow answer](http://stats.stackexchange.com/questions/1773/what-are-correct-values-for-precision-and-recall-in-edge-cases), Recall = 1 when FN=0, since 100% of the TP were discovered and Precision = 1 when FP=0, since no there were no spurious results.

#### Actual Results
<!-- Please paste or specifically describe the actual output or traceback. -->
Current output is:

```
/usr/local/lib/python3.5/dist-packages/sklearn/metrics/ranking.py:415: RuntimeWarning: invalid value encountered in true_divide
  recall = tps / tps[-1]
Out[201]: nan

```
#### Versions
<!--
Please run the following snippet and paste the output below.
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("NumPy", numpy.__version__)
import scipy; print("SciPy", scipy.__version__)
import sklearn; print("Scikit-Learn", sklearn.__version__)
-->
Linux-4.4.0-59-generic-x86_64-with-Ubuntu-16.04-xenial
Python 3.5.2 (default, Nov 17 2016, 17:05:23) 
[GCC 5.4.0 20160609]
NumPy 1.12.0
SciPy 0.18.1
Scikit-Learn 0.18.1


<!-- Thanks for contributing! -->

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

If someone can help me understand how to correctly do the False Positive calculation, I can submit a Pull Request.

For this bug, recall will be 1 since there are 0 True Positives and False Negatives. However, to calculate precision, I need to understand the correct way to find False Positives. The above sample results in `_binary_clf_curve` returning the same number of False Positives as the number of samples. Should I simply use that as the cue and say that is TPs=0 and FPs=len(y_true), then precision is 1?

I am not sure I quite understand how the threshold calculation is being performed [here](https://github.com/varunagrawal/scikit-learn/blob/master/sklearn/metrics/ranking.py#L263).

### Comment 2 ([user]):

Can you check if #7356 fixes this?

### Comment 3 ([user]):

> Can you check if #7356 fixes this?

No it doesn't. I think we just need to have to do something like this to handle this edge case:
```python
recall = 1 if tps[-1] == 0 else tps / tps[-1] 
```

[user] if you do a PR please add a non-regression test with only zeros in `y_true`.

### Comment 4 ([user]):

[user] can you please also specify what needs to be done for precision? Or should that be as is?

### Comment 5 ([user]):

I believe the code works as it is. You can add a test with only 1s in `y_true` to make sure that precision is 1 in this case.

### Comment 6 ([user]):

[user] hoping you can take a look at the PR.

### Comment 7 ([user]):

Updates on this. Is this merged?

### Comment 8 ([user]):

The current functionality of average_precision has changed. I'm planning to submit a new PR for that. Will close this when the other PR is ready.

### Comment 9 ([user]):

The standard TREC Eval is able to compute AP and other metrics on the same data.

### Comment 10 ([user]):

so how did you solve it ?

## PR Review Comments

**[user]** on `sklearn/metrics/_ranking.py`:

In [precision_recall_fscore_support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html?highlight=precision_recall_fscore_support#sklearn-metrics-precision-recall-fscore-support), there is a `zero_division` parameter that controls how we handle the edge case. This parameter is also used in `recall_score` and `precision_score`. If we want to be consistent with `precision_recall_fscore_support`, we would need to add a `zero_division` and use the same semantics.

What do you think?

**[user]** on `sklearn/metrics/_ranking.py`:

[user] this issue has been sitting unfixed for years. I think this fix should be merged as-is before it bit rots, and open a separate issue for semantic consistency.

**[user]** on `sklearn/metrics/_ranking.py`:

I agree with [user] on this. It's been over 3 years for what is a very simple bugfix, and we can track semantic consistency via another issue. That issue can be tackled by someone else, potentially from the sklearn team, which would get the ball rolling sooner.

**[user]** on `sklearn/metrics/tests/test_ranking.py`:

I think we can remove this, since the input is the exactly the same as the one above it.

**[user]** on `doc/whats_new/v1.0.rst`:

We can adjust the whats new to state which function is being fixed.

```rst
- |Fix| Fixes `average_precision_score` for multilabel classification when true labels are
   all negative. :pr:`19085` by :user:`Varun Agrawal <varunagrawal>`.
```

There also needs to be an entry for `precision_recall_curve` to describe the new behavior.

These entries need to be moved to `doc/whats_new/v1.1.rst`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
