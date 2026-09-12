# GH866_pandas_64569: BUG: Fix HDFStore.put with StringDtype columns and compression (#64180) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/64180
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

(withheld: the upstream fix is not part of the task) has added support for the new `str` dtype in HDF IO, but apparently was not tested in combination with compression:

```
>>> df = pd.DataFrame({"col": ["a", "b", "c"]})
>>> df.to_hdf("test_strings.h5", key="df")
>>> df.to_hdf("test_strings_compressed.h5", key="df", complevel=1)
...
File ~/conda/envs/pandas-30/lib/python3.13/site-packages/pandas/io/pytables.py:3288, in GenericFixed.write_array(self, key, obj, items)
   3285 if self._filters is not None:
   3286     with suppress(ValueError):
   3287         # get the atom for this datatype
-> 3288         atom = _tables().Atom.from_dtype(value.dtype)
   3290 if atom is not None:
   3291     # We only get here if self._filters is non-None and
   3292     #  the Atom.from_dtype call succeeded
   3293 
   3294     # create an empty chunked array and fill it from value
   3295     if not empty_array:

File ~/conda/envs/pandas-30/lib/python3.13/site-packages/tables/atom.py:366, in Atom.from_dtype(cls, dtype, dflt)
    341 @classmethod
    342 def from_dtype(cls, dtype: np.dtype, dflt: Any = None) -> Atom:
    343     """Create an Atom from a NumPy dtype.
    344 
    345     An optional default value may be specified as the dflt
   (...)    364 
    365     """
--> 366     basedtype = dtype.base
    367     shape = tuple(SizeType(i) for i in dtype.shape)
    368     if basedtype.names:

AttributeError: 'StringDtype' object has no attribute 'base'
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] , I’ve reviewed the previous PR (#60663) and the current failure.

From what I can see, when `complevel` is set, `GenericFixed.write_array` goes through the compression branch and calls `Atom.from_dtype(value.dtype)`. That assumes a NumPy dtype, but `StringDtype` is an ExtensionDtype and doesn’t implement `.base`, which leads to the `AttributeError`. Without compression, `BaseStringArray` correctly takes the `create_vlarray` path, so the issue only appears in the compressed case.

My plan is to ensure `BaseStringArray` is handled before the `Atom.from_dtype` logic so that `StringDtype` always stays on the `VLArray` path, while still passing `filters=self._filters` to support compression. I’ll also add regression tests covering `to_hdf(..., complevel=1)` for both `Series` and `DataFrame`.

If that approach sounds reasonable, I’ll proceed on it or will love if you have any other suggestion.

### Comment 2 ([user]):

Hi everyone. I have successfully reproduced this issue on my local machine using a development build of pandas. I see that [user]  suggested a plan two weeks ago, but since there is no linked PR yet, I would like to work on a fix for this as part of a university project (PIC1 at IST Lisbon).

[user] m, are you already working on a PR for this? If not, I'm happy to take it over. Thanks!

### Comment 3 ([user]):

> Hi everyone. I have successfully reproduced this issue on my local machine using a development build of pandas. I see that [user]  suggested a plan two weeks ago, but since there is no linked PR yet, I would like to work on a fix for this as part of a university project (PIC1 at IST Lisbon).
> 
> [user] m, are you already working on a PR for this? If not, I'm happy to take it over. Thanks!

Yess i am working on it...

### Comment 4 ([user]):

Hi [user] [user] can i also try this issue as well?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
