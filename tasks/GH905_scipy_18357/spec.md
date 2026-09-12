# GH905_scipy_18357: MAINT: clearer error in `LinearOperator * spmatrix` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scipy/scipy/issues/11564
- Repo: https://github.com/scipy/scipy

## Issue Description

<!-- 
Thank you for taking the time to file a bug report. 
Please fill in the fields below, deleting the sections that 
don't apply to your issue. You can view the final output
by clicking the preview button above.
Note: This is a comment, and won't appear in the output.
-->

My issue is about how LinearOperator objects interact with sparse matrix classes (e.g. ``csc_matrix``). Currently, operations like ``A @ B`` and ``A * B`` fall back on ``dot``, which does input casting without checking for sparse matrix types. Here is the line where the casting happens:

https://github.com/scipy/scipy/blob/1e161716a5e5c827573b9b88aa790af1864dfb1d/scipy/sparse/linalg/interface.py#L412

The effect of this casting is that operations ``A @ B`` raise ValueErrors when ``B`` is a SciPy sparse matrix.

#### Reproducing code example:
<!-- 
If you place your code between the triple backticks below, 
it will be rendered as a code block. 
-->

```
import scipy.sparse as spar
import scipy.sparse.linalg as spla

I = spar.eye(5)  # any dimension will do
A = spla.aslinearoperator(I)
A @ I  # raises a ValueError
```

#### Error message:
<!-- If any, paste the *full* error message inside a code block
as above (starting from line Traceback)
-->

```
Traceback (most recent call last):
  File "/home/riley/anaconda3/envs/dev36/lib/python3.6/site-packages/IPython/core/interactiveshell.py", line 3326, in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)
  File "<ipython-input-15-7d320c9e011f>", line 1, in <module>
    A @ I
  File "/home/riley/anaconda3/envs/dev36/lib/python3.6/site-packages/scipy/sparse/linalg/interface.py", line 426, in __matmul__
    return self.__mul__(other)
  File "/home/riley/anaconda3/envs/dev36/lib/python3.6/site-packages/scipy/sparse/linalg/interface.py", line 390, in __mul__
    return self.dot(x)
  File "/home/riley/anaconda3/envs/dev36/lib/python3.6/site-packages/scipy/sparse/linalg/interface.py", line 420, in dot
    % x)
ValueError: expected 1-d or 2-d array or matrix, got array(<5x5 sparse matrix of type '<class 'numpy.float64'>'
	with 5 stored elements (1 diagonals) in DIAgonal format>, dtype=object)
```

#### Scipy/Numpy/Python version information:
SciPy: 1.4.1.
NumPy: 1.17.1.
Python 3.6.7.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

What would be the desired behavior here?
- Silently returning a sparse matrix/array of the same type seems wrong because there's no promise it'll be actually sparse.
- Wrapping the sparse matrix into `aslinearoperator` and returning a product seems like a good option, but I am not sure whether it's what the user wants.

I believe raising an informative error would be the best; do people agree?

### Comment 2 ([user]):

Hi [user]! Thanks for checking in on this. I think that if someone is using LinearOperator object ``A`` or ``B``, then their most likely assumption will be that ``A @ B`` returns a LinearOperator whenever possible. Certainly, there are limitations where duck typing will only get you so far. But from a mathematical standpoint, a sparse matrix is a linear operator. Since SciPy's LinearOperator class is defined in ``scipy.sparse.linalg`` a user can reasonably expect that SciPy sparse matrices play nice with that class.

That said -- raising an informative error message would be okay, in my opinion. I'd just want the error to recommend a fix, like
```
ValueError : computing A @ B where one of (A, B) is a LinearOperator and the other of (A, B) is a sparse matrix.
If A is the sparse matrix, consider computing A_lo @ B where A_lo = scipy.sparse.linalg.aslinearoperator(A).
If B is the sparse matrix, consider computing A @ B_lo where B_lo = scipy.sparse.linalg.aslinearoperator(B).
```

### Comment 3 ([user]):

Alright; happy to provide a more specific error message once my own #18061 editing the same code is accepted.

### Comment 4 ([user]):

Please take a look at #18357

## PR Review Comments

**[user]** on `scipy/sparse/linalg/tests/test_interface.py`:

Might it be better to use ``@`` instead of ``*`` for multiplication here? I know that ``*`` overloads to matmul for LinearOperator and spmatrix datatypes, but my understanding is that ``@`` is preferable for future-proofing code.

**[user]** on `scipy/sparse/linalg/tests/test_interface.py`:

Indeed; done now.

**[user]** on `scipy/sparse/linalg/tests/test_interface.py`:

[user] can you remember why these test cases were included? They seem unrelated to the rest of this PR?

**[user]** on `scipy/sparse/linalg/tests/test_interface.py`:

To the best of my recollection, this is to ensure that the exception catching isn't too broad, and we aren't overwriting other errors. It is, however, mysterious without a commend and also likely misplaced.

**[user]** on `scipy/sparse/linalg/tests/test_interface.py`:

makes sense, thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
