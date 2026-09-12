# GH900_scikit_learn_14286: [MRG+1] FIX Negative or null sample_weights in SVM — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/9674
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

As a first step for dealing with #9494, this reproduces the issue in a unit test.

This should fail with the same IndexError as in the original report.
It only fails when _all_ of the weights of the second class are negative.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Uhm no chances on this one :)

### Comment 2 ([user]):

[user], do you mean that the original issue should be closed without any code change, or that there is something fundamentally wrong with my try to do test driven programming?
Can you reproduce the error with my test?

### Comment 3 ([user]):

Oh sorry, actually the CI did not run and thus I believed that you test did not failed.

### Comment 4 ([user]):

I see. Bad nightly idea to deactivate CI on that. I will switch it back on, s.t. you don't need to test locally.

### Comment 5 ([user]):

FWIW, [A travis build](https://travis-ci.org/scikit-learn/scikit-learn/jobs/271183580) additionally shows the stderr message `warning: class label 1 specified in weight is not found`, which might be related and seems to come from [here](https://github.com/scikit-learn/scikit-learn/blob/e2f99b04270d132d0a485fdb43406e46a95bb2ee/sklearn/svm/src/liblinear/linear.cpp#L2414) in `linear.cpp`.

### Comment 6 ([user]):

No, I guess the warning must be from [the corresponding place](https://github.com/scikit-learn/scikit-learn/blob/e2f99b04270d132d0a485fdb43406e46a95bb2ee/sklearn/svm/src/libsvm/svm.cpp#L2439) in svm.cpp, since the test calls `svm.SVC`, not `svm.LinearSVC`—but I am reading all of this code for the first time.

Actually, this warning might just be a side effect (or even totally unrelated), because the code there is about label weights `weight`. The sample weights are in `W`. They were introduced by [user] in 2010, and they don't exist in [upstream libSVM](https://github.com/cjlin1/libsvm/blob/master/svm.cpp).

### Comment 7 ([user]):

(See [my comment in the issue](https://github.com/scikit-learn/scikit-learn/issues/9494#issuecomment-326975073).)

### Comment 8 ([user]):

Add a fix?

### Comment 9 ([user]):

Ready for review.

### Comment 10 ([user]):

I feel this should be with a check_sample_weights function tested on all estimators with a common test that can be disable for speed with the new context manager.

## PR Review Comments

**[user]** on `sklearn/svm/tests/test_svm.py`:

Could you revert this change

**[user]** on `sklearn/svm/tests/test_svm.py`:

Could you rever this change

**[user]** on `sklearn/svm/tests/test_svm.py`:

It will be more readbable to parametrize the test.

**[user]** on `sklearn/svm/tests/test_svm.py`:

By reviewing, I saw that some of the tests can be improved at the same time that you are writing yours.

You can refer to the following diff:
(withheld: the upstream fix is not part of the task)

**[user]** on `sklearn/svm/src/libsvm/svm.cpp`:

```suggestion
	if(svm_type == C_SVC ||
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
