# GH924_numpy_30615: BUG: np.take out dtype — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/numpy/numpy/issues/25588
- Repo: https://github.com/numpy/numpy

## Issue Description

### Describe the issue:

`np.take(a, indices, out=out)` fails if `out.dtype` is not exactly `a.dtype`. The doc says about `out`:
> It should be of the appropriate shape and dtype.

But what is *appropriate*?

### Reproduce the code example:

```python
import numpy as np
a = np.arange(3).astype(np.int32)
indices = np.arange(2)
out = np.zeros_like(indices, dtype=np.int64)
np.take(a, indices, out=out)
```


### Error message:

```shell
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
File ~/github/numpy/build-install/usr/lib/python3.11/site-packages/numpy/_core/fromnumeric.py:59, in _wrapfunc(obj, method, *args, **kwds)
     58 try:
---> 59     return bound(*args, **kwds)
     60 except TypeError:
     61     # A TypeError occurs if the object does have such a method in its
     62     # class, but its signature is not identical to that of NumPy's. This
   (...)
     66     # Call _wrapit from within the except clause to ensure a potential
     67     # exception has a traceback chain.

TypeError: Cannot cast array data from dtype('int64') to dtype('int32') according to the rule 'safe'

During handling of the above exception, another exception occurred:

TypeError                                 Traceback (most recent call last)
Cell In[4], line 1
----> 1 np.take(a, indices, out=out)

File ~/github/numpy/build-install/usr/lib/python3.11/site-packages/numpy/_core/fromnumeric.py:192, in take(a, indices, axis, out, mode)
     95 @array_function_dispatch(_take_dispatcher)
     96 def take(a, indices, axis=None, out=None, mode='raise'):
     97     """
     98     Take elements from an array along an axis.
     99 
   (...)
    190            [5, 7]])
    191     """
--> 192     return _wrapfunc(a, 'take', indices, axis=axis, out=out, mode=mode)

File ~/github/numpy/build-install/usr/lib/python3.11/site-packages/numpy/_core/fromnumeric.py:68, in _wrapfunc(obj, method, *args, **kwds)
     59     return bound(*args, **kwds)
     60 except TypeError:
     61     # A TypeError occurs if the object does have such a method in its
     62     # class, but its signature is not identical to that of NumPy's. This
   (...)
     66     # Call _wrapit from within the except clause to ensure a potential
     67     # exception has a traceback chain.
---> 68     return _wrapit(obj, method, *args, **kwds)

File ~/github/numpy/build-install/usr/lib/python3.11/site-packages/numpy/_core/fromnumeric.py:45, in _wrapit(obj, method, *args, **kwds)
     43 except AttributeError:
     44     wrap = None
---> 45 result = getattr(asarray(obj), method)(*args, **kwds)
     46 if wrap:
     47     if not isinstance(result, mu.ndarray):

TypeError: Cannot cast array data from dtype('int64') to dtype('int32') according to the rule 'safe'
```


### Python and NumPy Versions:

'numpy_version': '2.0.0.dev0+git20240115.bbdd595'

### Runtime Environment:

not important

### Context for the issue:

`out = np.take(a, indices)` works, but passing the `out` arg explicitly saves intermediate memory and could be a tiny bit faster.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

It looks like this is happening because inside of the `take` implementation, we explicitly downcast `out` to the same dtype as `a`:

https://github.com/numpy/numpy/blob/b0371ef240560e78b651a5d7c9407ae3212a3d56/numpy/_core/src/multiarray/item_selection.c#L306-L310

Ultimately the error you're seeing gets triggered from the early return on line 310 in that C file.

I'm not sure offhand why the `PyArray_FromArray` call is there, although `git blame` says it's been there since 2011. Presumably we'd need to do something smarter at that location to check if `out` is already sufficiently "wide" to hold the  output.

### Comment 2 ([user]):

I seem to recall an old issue or PR about it.  The `out` casting check is incorrectly reversed or so.

### Comment 3 ([user]):

Related issue https://github.com/numpy/numpy/issues/16319 and (withheld: the upstream fix is not part of the task).

### Comment 4 ([user]):

Current behaviour is that `np.take` always returns `out` if it is given. The desired behaviour is unclear to me.
If a user passes an `out` of same shape and dtype as the result, this seems fine. But what should happen if a user passes an out of same shape but different dtype? Possibilities are:

1. Always error (current main)
2. Only error when out.dtype is smaller
  In this case options for return value are:
  a) Return a separate newly created array
  b) Return out as specified by user and cast resulting values to out.dtype.

### Comment 5 ([user]):

See also https://github.com/numpy/numpy/issues/16319, https://github.com/numpy/numpy/issues/22766, and https://github.com/numpy/numpy/issues/21676

### Comment 6 ([user]):

Hi, I’ve reviewed the feedback provided in PR #25600 and would like to try fixing this issue by addressing those points.
Since I’m still new to the codebase, I’d appreciate any guidance. May I take this on?

### Comment 7 ([user]):

No need to ask, just open a PR. Feel free to ask questions in here.

## PR Review Comments

**[user]** on `numpy/_core/tests/test_regression.py`:

Can you please explain this change?

**[user]** on `numpy/_core/tests/test_item_selection.py`:

Please move this test to `test_deprecations` and use the pattern used there.

**[user]** on `numpy/_core/src/multiarray/item_selection.c`:

Please add the comments we usually add to say when the deprecation happened (before it) and also inside the deprecation itself, such as `(deprecated NumPy 2.5)`.

The last sentence feels like unnecessary to me.  (I should think once more if we shouldn't just use safe casting, although then one might be tempted to ask for a `casting=` kwarg.)

**[user]** on `numpy/_core/src/multiarray/item_selection.c`:

This needs cleaning up, you are inserting code but that code interacts closely with this so you can't insert code between these two lines.
I.e. the `dtype` reference can be lost on error.

**[user]** on `numpy/_core/src/multiarray/item_selection.c`:

This is the _exact_ same code as the first branch, except for a flag that is irrelevant in the first branch.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
