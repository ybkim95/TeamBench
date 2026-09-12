# GH976_scikit_learn_16849: BUG Fix instability issue of ARDRegression (with speedup) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/15186
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

<!-- Instructions For Filing a Bug: https://github.com/scikit-learn/scikit-learn/blob/master/CONTRIBUTING.md#filing-bugs -->

#### Description
Testing failed for the test `test_ard_accuracy_on_easy_problem` in test_bayes.py

#### Steps/Code to Reproduce
```
pytest -x sklearn/linear_model/tests/test_bayes.py
```


#### Expected Results
All tests pass

#### Actual Results

```
def test_ard_accuracy_on_easy_problem():
        # Check that ARD converges with reasonable accuracy on an easy problem
        # (Github issue #14055)
        # This particular seed seems to converge poorly in the failure-case
        # (scipy==1.3.0, sklearn==0.21.2)
        seed = 45
        X = np.random.RandomState(seed=seed).normal(size=(250, 3))
        y = X[:, 1]
    
        regressor = ARDRegression()
        regressor.fit(X, y)
    
        abs_coef_error = np.abs(1 - regressor.coef_[1])
        # Expect an accuracy of better than 1E-4 in most cases -
        # Failure-case produces 0.16!
>       assert abs_coef_error < 0.01
E       assert 0.018021599217421413 < 0.01

sklearn/linear_model/tests/test_bayes.py:218: AssertionError
```
#### Versions
System:
    python: 3.7.4 (default, Aug 13 2019, 20:35:49)  [GCC 7.3.0]
executable: /home/corrie/.pyenv/versions/anaconda3-2019.03/bin/python
   machine: Linux-5.0.0-31-generic-x86_64-with-debian-buster-sid

Python deps:
       pip: 19.2.3
setuptools: 41.4.0
   sklearn: 0.22.dev0
     numpy: 1.17.2
     scipy: 1.3.1
    Cython: 0.29.13
    pandas: 0.25.1
matplotlib: 3.1.1
    joblib: 0.13.2

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Same problem here, I'm getting the exactly same value of abs_coef_error.

**Version**

System:
   machine: Linux-4.15.0-62-generic-x86_64-with-Ubuntu-16.04-xenial
executable: /home/riccardo.folloni/Documents/open_source/scikit_contrib/bin/python
    python: 3.5.2 (default, Oct  8 2019, 13:06:37)  [GCC 5.4.0 20160609]

Python deps:
    pandas: 0.24.2
       pip: 19.2.3
matplotlib: 3.0.3
    joblib: 0.14.0
    Cython: 0.29.13
     scipy: 1.3.1
setuptools: 41.4.0
   sklearn: 0.22.dev0
     numpy: 1.17.2

### Comment 2 ([user]):

I cannot reproduce this issue with latest version 0.23.dev0 neither with 0.22. It seems this problem is solved, right?

### Comment 3 ([user]):

[user] did you manage to investigate this one?

### Comment 4 ([user]):

Nope, had completely forgotten I posted this error. Also can't reproduce since I got a new computer and now get a different error.
[user] can you still reproduce the error?

### Comment 5 ([user]):

I can reproduce it on my platform:

System:
    python: 3.7.6 (default, Jan 30 2020, 09:44:41)  [GCC 9.2.1 20190827 (Red Hat 9.2.1-1)]
executable: /home/cmarmo/.skldevenv/bin/python
   machine: Linux-5.5.10-200.fc31.x86_64-x86_64-with-fedora-31-Thirty_One

Python dependencies:
       pip: 20.0.2
setuptools: 40.8.0
   sklearn: 0.23.dev0
     numpy: 1.17.2
     scipy: 1.3.1
    Cython: 0.29.13
    pandas: 0.25.1
matplotlib: 3.1.1
    joblib: 0.13.2

Built with OpenMP: True

### Comment 6 ([user]):

See also #16097 and #15420: note that my CPU does not support AVX-512 and, indeed, changing the seed to 46 fixes the issue.

### Comment 7 ([user]):

Same with:
System:
    python: 3.8.1 (default, Jan  8 2020, 22:29:32)  [GCC 7.3.0]
executable: /home/cmarmo/.conda/envs/pylatest_pip_openblas_pandas/bin/python
   machine: Linux-5.5.10-200.fc31.x86_64-x86_64-with-glibc2.10

Python dependencies:
       pip: 20.0.2
setuptools: 46.0.0.post20200309
   sklearn: 0.23.dev0
     numpy: 1.18.1
     scipy: 1.4.1
    Cython: None
    pandas: None
matplotlib: 3.2.0
    joblib: 0.14.1

As reported in #14055 this is an issue in scipy>=1.3?
Maybe #16102 is indeed the only solution?

### Comment 8 ([user]):

Thanks for the reports. I Can reproduce on a basic linux too. 

The original issue is https://github.com/scikit-learn/scikit-learn/issues/14055. It was closed but it's not entirely fixed yet. The issue is related to scipy's `cond` parameter of the `pinvh` function, which changed in scipy 1.3. The "Fix" was to backport `pinvh` to that of scipy 1.2.

Before the fix, i.e. using the latest scipy, the test would fail 46 times out of 100 seeds. After the fix, i.e. on scikit-learn master (using the backport of `pinvh`), it fails 7 times.

As mentioned a few times in the previous issues/PR, the fix was only a basic patch. But the underlying instability issue remains, and needs to be carefully addressed (probably not gonna be easy...)

### Comment 9 ([user]):

Having the test randomly can be confusing for unrelated PRs. Should we skip the test for now?

### Comment 10 ([user]):

I don't think it fails randomly? It fails for specific seeds and specific architectures but in a deterministic manner it seems.

## PR Review Comments

**[user]** on `sklearn/linear_model/tests/test_bayes.py`:

If the target is constant, it makes sense to me that both coefficients should bet set to zero. So I think this is a bug fix

**[user]** on `sklearn/linear_model/tests/test_bayes.py`:

The test should now run properly on many different seeds (there was a 7% failure rate before), and with a *much* higher precision

**[user]** on `sklearn/linear_model/_bayes.py`:

So that's basically the main fix. Instead of relying on the [woodbury formula](https://en.wikipedia.org/wiki/Woodbury_matrix_identity), we just directly invert the matrix (called S_N in  [the ref](http://www.utstat.toronto.edu/~rsalakhu/sta4273/notes/Lecture2.pdf#page=15)). This seems to be much more stable and also much faster because here we invert a matrix that is `n_features x features` whereas in master the inversion is on a `n_samples x n_samples`.

Strangely enough, this somewhat reverts a commit from 10 years ago (withheld: the upstream fix is not part of the task), whose goal was to make things faster but I'm not sure it did. [user] if you're still around your input would be greatly appreciated!

**[user]** on `sklearn/linear_model/_bayes.py`:

We don't need the scipy's backport to we can remove it now

**[user]** on `doc/whats_new/v0.23.rst`:

you could also mention (withheld: the upstream fix is not part of the task)files#r403760030 here maybe?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
