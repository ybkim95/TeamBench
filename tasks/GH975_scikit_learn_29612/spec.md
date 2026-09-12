# GH975_scikit_learn_29612: Fix seed sensitivity of test_fastica_eigh_low_rank_warning — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/26802
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

**CI is still failing on [Linux_Runs.pylatest_conda_forge_mkl](https://dev.azure.com/scikit-learn/scikit-learn/_build/results?buildId=68533&view=logs&j=dde5042c-7464-5d47-9507-31bdd2ee0a3a)** (Jul 10, 2024)
- test_fastica_eigh_low_rank_warning[31]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

## CI is no longer failing! ✅

[Successful run](https://dev.azure.com/scikit-learn/scikit-learn/_build/results?buildId=69196&view=logs&j=dde5042c-7464-5d47-9507-31bdd2ee0a3a) on Aug 02, 2024

### Comment 2 ([user]):

For future reference, it seems like for some global random seed we get a `ConvergenceWarning` rather than a `UserWarning` about singular values:

```
____________________ test_fastica_eigh_low_rank_warning[31] ____________________
[gw1] linux -- Python 3.11.4 /usr/share/miniconda/envs/testvenv/bin/python

global_random_seed = 31

    def test_fastica_eigh_low_rank_warning(global_random_seed):
        """Test FastICA eigh solver raises warning for low-rank data."""
        rng = np.random.RandomState(global_random_seed)
        A = rng.randn(10, 2)
        X = A @ A.T
        ica = FastICA(random_state=0, whiten="unit-variance", whiten_solver="eigh")
        msg = "There are some small singular values"
>       with pytest.warns(UserWarning, match=msg):
E       Failed: DID NOT WARN. No warnings of type (<class 'UserWarning'>,) matching the regex were emitted.
E        Regex: There are some small singular values
E        Emitted warnings: [ ConvergenceWarning('FastICA did not converge. Consider increasing tolerance or the maximum number of iterations.')]

A          = array([[-0.41475721, -0.33336867],
       [ 0.08109199, -0.79102695],
       [-0.21859967, -0.76319684],
       [-0.77...-0.91879129],
       [ 1.19943449, -0.34137424],
       [-1.75860731,  0.05111747],
       [-0.57192899, -0.70056604]])
X          = array([[ 2.83158216e-01,  2.30070116e-01,  3.45091706e-01,
        -2.94201294e-01,  3.21336537e-01, -7.56222642e-02,
... 4.63831401e-01, -7.26324674e-02,
         1.20573385e+00, -4.46836158e-01,  9.69987343e-01,
         8.17895550e-01]])
global_random_seed = 31
ica        = FastICA(random_state=0, whiten_solver='eigh')
msg        = 'There are some small singular values'
rng        = RandomState(MT19937) at 0x7F71B6CA6940

../1/s/sklearn/decomposition/tests/test_fastica.py:450: Failed
```

### Comment 3 ([user]):

The last error is about `test_minibatch_sensible_reassign[34]`: Edit 3 weeks after creating the comment, the `test_minibatch_sensible_reassign` should now have been fixed by (withheld: the upstream fix is not part of the task) :crossed_fingers: 

```
_____________________ test_minibatch_sensible_reassign[34] _____________________
[gw0] linux -- Python 3.11.9 /usr/share/miniconda/envs/testvenv/bin/python

global_random_seed = 34
    def test_minibatch_sensible_reassign(global_random_seed):
        # check that identical initial clusters are reassigned
        # also a regression test for when there are more desired reassignments than
        # samples.
        zeroed_X, true_labels = make_blobs(
            n_samples=100, centers=5, random_state=global_random_seed
        )
        zeroed_X[::2, :] = 0
    
        km = MiniBatchKMeans(
            n_clusters=20, batch_size=10, random_state=global_random_seed, init="random"
        ).fit(zeroed_X)
        # there should not be too many exact zero cluster centers
>       assert km.cluster_centers_.any(axis=1).sum() > 10
E       AssertionError

global_random_seed = 34
km         = MiniBatchKMeans(batch_size=10, init='random', n_clusters=20, random_state=34)
true_labels = array([3, 0, 2, 4, 1, 0, 2, 3, 0, 1, 4, 2, 2, 0, 2, 4, 3, 4, 2, 3, 3, 4,
       2, 2, 1, 4, 3, 4, 3, 1, 1, 1, 4, 1, 4,...3,
       4, 1, 0, 3, 3, 4, 3, 2, 2, 2, 0, 2, 2, 4, 4, 0, 4, 2, 3, 0, 2, 1,
       3, 0, 1, 2, 0, 3, 1, 0, 0, 4, 2, 4])
zeroed_X   = array([[  0.        ,   0.        ],
       [ -9.93451852,   5.17769196],
       [  0.        ,   0.        ],
       ...     ],
       [ -5.62221677,   0.01380172],
       [  0.        ,   0.        ],
       [ -6.95512025,  -1.26162786]])

../1/s/sklearn/cluster/tests/test_k_means.py:440: AssertionError
```

### Comment 4 ([user]):

The last one seems to be Figshare HTTP 403 issue #28297. Test collection error because early on we download a few datasets in conftest.py and we get an error.

```
INTERNALERROR> def worker_internal_error(self, node, formatted_error):
INTERNALERROR>         """
INTERNALERROR>         pytest_internalerror() was called on the worker.
INTERNALERROR>     
INTERNALERROR> E               File "/usr/share/miniconda/envs/testvenv/lib/python3.11/urllib/request.py", line 496, in _call_chain
INTERNALERROR> E                 result = func(*args)
INTERNALERROR> E                          ^^^^^^^^^^^
INTERNALERROR> E               File "/usr/share/miniconda/envs/testvenv/lib/python3.11/urllib/request.py", line 643, in http_error_default
INTERNALERROR> E                 raise HTTPError(req.full_url, code, msg, hdrs, fp)
INTERNALERROR> E             urllib.error.HTTPError: HTTP Error 403: Forbidden
INTERNALERROR> E           assert False
INTERNALERROR> 
INTERNALERROR> /usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/xdist/dsession.py:200: AssertionError
INTERNALERROR> Traceback (most recent call last):
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/_pytest/main.py", line 285, in wrap_session
INTERNALERROR>     session.exitstatus = doit(config, session) or 0
INTERNALERROR>                          ^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/_pytest/main.py", line 339, in _main
INTERNALERROR>     config.hook.pytest_runtestloop(session=session)
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_hooks.py", line 513, in __call__
INTERNALERROR>     return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_manager.py", line 120, in _hookexec
INTERNALERROR>     return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_callers.py", line 182, in _multicall
INTERNALERROR>     return outcome.get_result()
INTERNALERROR>            ^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_result.py", line 100, in get_result
INTERNALERROR>     raise exc.with_traceback(exc.__traceback__)
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_callers.py", line 167, in _multicall
INTERNALERROR>     teardown.throw(outcome._exception)
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/_pytest/logging.py", line 807, in pytest_runtestloop
INTERNALERROR>     return (yield)  # Run all the tests.
INTERNALERROR>             ^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/pluggy/_callers.py", line 103, in _multicall
INTERNALERROR>     res = hook_impl.function(*args)
INTERNALERROR>           ^^^^^^^^^^^^^^^^^^^^^^^^^
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/xdist/dsession.py", line 123, in pytest_runtestloop
INTERNALERROR>     self.loop_once()
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/xdist/dsession.py", line 148, in loop_once
INTERNALERROR>     call(**kwargs)
INTERNALERROR>   File "/usr/share/miniconda/envs/testvenv/lib/python3.11/site-packages/xdist/dsession.py", line 188, in worker_workerfinished
INTERNALERROR>     self._active_nodes.remove(node)
INTERNALERROR> KeyError: <WorkerController gw0>
```

### Comment 5 ([user]):

For reference, the `test_fastica_eigh_low_rank_warning[31]` failure happened again last night with the same symptoms as described above (`ConvergenceWarning` instead of `UserWarning`).

## PR Review Comments

**[user]** on `doc/whats_new/v1.6.rst`:

```suggestion
  :class:`decomposition.FastICA` with `whiten_solver="eigh"` to improve the
```

**[user]** on `sklearn/decomposition/tests/test_fastica.py`:

```suggestion
            # random seeds but this happens after the whiten step so this is
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
