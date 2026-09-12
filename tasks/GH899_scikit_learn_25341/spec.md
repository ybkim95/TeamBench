# GH899_scikit_learn_25341: FIX Support read-only sparse datasets for `Tree`-based estimators — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/25333
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

### Describe the bug

When calling `cross_val_score` with a sparse data matrix `X` and a `RandomForestClassifier` with `n_jobs=-1`, there is a weird interaction with joblib and memmapping that makes the buffer from `X` read-only, breaking the cython code for the tree construction but it is weird as it only appears with the `cross_validate` function, and not when calling the classifier alone, while `n_jobs=1` for the  cross val function so joblib should not enter the play here...

### Steps/Code to Reproduce

```python
from scipy.sparse import csr_matrix
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

X, y = make_classification(10000, n_features=200)
X = csr_matrix(X, copy=True)

clf = RandomForestClassifier(n_jobs=-1)

cross_val_score(clf, X, y)
```

### Expected Results

Working code

### Actual Results

```
ValueError: 
All the 5 fits failed.
It is very likely that your model is misconfigured.
You can try to debug the error by setting error_score='raise'.

Below are more details about the failures:
--------------------------------------------------------------------------------
5 fits failed with the following error:
joblib.externals.loky.process_executor._RemoteTraceback: 
"""
Traceback (most recent call last):
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/externals/loky/process_executor.py", line 428, in _process_worker
    r = call_item()
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/externals/loky/process_executor.py", line 275, in __call__
    return self.fn(*self.args, **self.kwargs)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/_parallel_backends.py", line 620, in __call__
    return self.func(*args, **kwargs)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/parallel.py", line 288, in __call__
    return [func(*args, **kwargs)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/parallel.py", line 288, in <listcomp>
    return [func(*args, **kwargs)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/utils/fixes.py", line 117, in __call__
    return self.function(*args, **kwargs)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/ensemble/_forest.py", line 185, in _parallel_build_trees
    tree.fit(X, y, sample_weight=curr_sample_weight, check_input=False)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/tree/_classes.py", line 889, in fit
    super().fit(
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/tree/_classes.py", line 379, in fit
    builder.build(self.tree_, X, y, sample_weight)
  File "sklearn/tree/_tree.pyx", line 147, in sklearn.tree._tree.DepthFirstTreeBuilder.build
  File "sklearn/tree/_tree.pyx", line 173, in sklearn.tree._tree.DepthFirstTreeBuilder.build
  File "sklearn/tree/_splitter.pyx", line 789, in sklearn.tree._splitter.BaseSparseSplitter.init
  File "stringsource", line 660, in View.MemoryView.memoryview_cwrapper
  File "stringsource", line 350, in View.MemoryView.memoryview.__cinit__
ValueError: buffer source array is read-only
"""

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/model_selection/_validation.py", line 686, in _fit_and_score
    estimator.fit(X_train, y_train, **fit_params)
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/sklearn/ensemble/_forest.py", line 474, in fit
    trees = Parallel(
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/parallel.py", line 1098, in __call__
    self.retrieve()
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/parallel.py", line 975, in retrieve
    self._output.extend(job.get(timeout=self.timeout))
  File "/home/temp/.local/miniconda/lib/python3.10/site-packages/joblib/_parallel_backends.py", line 567, in wrap_future_result
    return future.result(timeout=timeout)
  File "/home/temp/.local/miniconda/lib/python3.10/concurrent/futures/_base.py", line 458, in result
    return self.__get_result()
  File "/home/temp/.local/miniconda/lib/python3.10/concurrent/futures/_base.py", line 403, in __get_result
    raise self._exception
ValueError: buffer source array is read-only
```

### Versions

```shell
System:
    python: 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:36:39) [GCC 10.4.0]
executable: /home/temp/.local/miniconda/bin/python3.10
   machine: Linux-5.14.0-1054-oem-x86_64-with-glibc2.31

Python dependencies:
      sklearn: 1.2.0
          pip: 22.3
   setuptools: 65.5.0
        numpy: 1.23.5
        scipy: 1.9.3
       Cython: 0.29.32
       pandas: 1.5.2
   matplotlib: 3.6.2
       joblib: 1.2.0
threadpoolctl: 3.1.0

Built with OpenMP: True

threadpoolctl info:
       user_api: blas
   internal_api: mkl
         prefix: libmkl_rt
       filepath: /home/temp/.local/miniconda/lib/libmkl_rt.so.2
        version: 2022.1-Product
threading_layer: intel
    num_threads: 4

       user_api: openmp
   internal_api: openmp
         prefix: libomp
       filepath: /home/temp/.local/miniconda/lib/libomp.so
        version: None
    num_threads: 8
```
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I think this might be the same problem as in #25247. Could you take a look at that issue and see if it is related and if you have anything to add to it please?

I'll close this for now. If this isn't a duplicate we can reopen it.

### Comment 2 ([user]):

This is a slightly different problem. (withheld: the upstream fix is not part of the task) has been opened to fix it.

### Comment 3 ([user]):

Sorry I missed the #25247 , seems related. Feel free to close this one if it is a duplicate.

The thing that I find really weird is that this works fine without `cross_val_score` but not with it. It feels that the memmap thing happen due to the cross_val_score, even though it is with `n_jobs=1`.

## PR Review Comments

**[user]** on `sklearn/ensemble/tests/test_forest.py`:

Minor changes to reduce the run time of the tests, set the `random_seed` to be deterministic, and I do not think the memmap here is required for the test to fail on `main`:

```suggestion
    X, y = make_classification(n_samples=100, n_features=20, random_state=0)
    X = csr_matrix(X, copy=True)

    clf = RandomForestClassifier(n_jobs=2, random_state=0)
    cross_val_score(clf, X, y, cv=2)
```

**[user]** on `doc/whats_new/v1.3.rst`:

I think this can be moved to 1.2.1 as a bug fix.

**[user]** on `doc/whats_new/v1.3.rst`:

```suggestion
```

**[user]** on `doc/whats_new/v1.2.rst`:

This could move before the `sklearn.utils` entry

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
