# GH983_dask_11144: Update ``test_groupby_grouper_dispatch`` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/11140
- Repo: https://github.com/dask/dask

## Issue Description

`pytest` started emitting a warning on `importorskip` when the library can be found, but raises an error when attempting to import it. We're running into this in gpuCI when attempting to import `cudf`. See, for example, [this gpuCI build](https://gpuci.gpuopenanalytics.com/job/dask/job/dask/job/prb/job/dask-prb/5930/) over in (withheld: the upstream fix is not part of the task) which has several errors like this:

```
03:10:30 ________________ test_groupby_large_ints_exception[tasks-cudf] _________________
03:10:30 [gw1] linux -- Python 3.10.14 /opt/conda/envs/dask/bin/python3.10
03:10:30 
03:10:30 backend = 'cudf'
03:10:30 
03:10:30     @pytest.mark.parametrize(
03:10:30         "backend",
03:10:30         [
03:10:30             "pandas",
03:10:30             pytest.param("cudf", marks=pytest.mark.gpu),
03:10:30         ],
03:10:30     )
03:10:30     def test_groupby_large_ints_exception(backend):
03:10:30 >       data_source = pytest.importorskip(backend)
03:10:30 E       pytest.PytestDeprecationWarning: 
03:10:30 E       Module 'cudf' was found, but when imported by pytest it raised:
03:10:30 E           ImportError('libarrow.so.1600: cannot open shared object file: No such file or directory')
03:10:30 E       In pytest 9.1 this warning will become an error by default.
03:10:30 E       You can fix the underlying problem, or alternatively overwrite this behavior and silence this warning by passing exc_type=ImportError explicitly.
03:10:30 E       See [https://docs.pytest.org/en/stable/deprecations.html#pytest-importorskip-default-behavior-regarding-importerror](https://docs.pytest.org/en/stable/deprecations.html#pytest-importorskip-default-behavior-regarding-importerror%1B[0m)
03:10:30 
03:10:30 dask/dataframe/tests/test_groupby.py:3130: PytestDeprecationWarning
```

Similar to (withheld: the upstream fix is not part of the task) 

cc [user] [user] [user] for visibility. By chance, does anyone have bandwidth to handle this one?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Think the larger context here is some breakage that cropped up in cuDF this week around libarrow 16.1.0 that should generally be resolved now:

- (withheld: the upstream fix is not part of the task)
- (withheld: the upstream fix is not part of the task)

So wouldn't expect to see this warning in GPU CI on subsequent runs.

Beyond that specific breakage, is there preferable behavior we'd want from pytest here? IMO, I prefer this noisier output when the module is available but broken versus the more obfuscated errors we see when the broken package is silently imported and used in testing.

### Comment 2 ([user]):

Thanks [user]. Running CI over in (withheld: the upstream fix is not part of the task) just to double check that things look good. 

> IMO, I prefer this noisier output when the module is available but broken versus the more obfuscated errors we see when the broken package is silently imported and used in testing.

Same. Given that's what `pytest` is doing now, I don't think we need any code changes on our end

### Comment 3 ([user]):

Indeed the `libarrow` issue has been resolved (🎉 ) but there are still a couple of other failures like this

```
10:26:47 ____________________ test_groupby_grouper_dispatch[tasks-b] ____________________
10:26:47 [gw1] linux -- Python 3.10.14 /opt/conda/envs/dask/bin/python3.10
10:26:47 

10:26:47 key = 'b'
10:26:47 

10:26:47     @pytest.mark.gpu
10:26:47     @pytest.mark.parametrize("key", ["a", "b"])
10:26:47     def test_groupby_grouper_dispatch(key):
10:26:47         cudf = pytest.importorskip("cudf")
10:26:47     
10:26:47         # not directly used but must be imported
10:26:47         pytest.importorskip("dask_cudf")  # noqa: F841
10:26:47     
10:26:47         pdf = pd.DataFrame(
10:26:47             {
10:26:47                 "a": ["a", "b", "c", "d", "e", "f", "g", "h"],
10:26:47                 "b": [1, 2, 3, 4, 5, 6, 7, 8],
10:26:47                 "c": [1.0, 2.0, 3.5, 4.1, 5.5, 6.6, 7.9, 8.8],
10:26:47             }
10:26:47         )
10:26:47         gdf = cudf.from_pandas(pdf)
10:26:47     
10:26:47         pd_grouper = grouper_dispatch(pdf)(key=key)
10:26:47         gd_grouper = grouper_dispatch(gdf)(key=key)
10:26:47     
10:26:47         # cuDF's numeric behavior aligns with numeric_only=True
10:26:47         expect = pdf.groupby(pd_grouper).sum(numeric_only=True)
10:26:47 >       got = gdf.groupby(gd_grouper).sum()
10:26:47 

10:26:47 dask/dataframe/tests/test_groupby.py:2996: 
10:26:47 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
10:26:47 /opt/conda/envs/dask/lib/python3.10/site-packages/cudf/core/mixins/mixin_factory.py:11: in wrapper
10:26:47     return method(self, *args1, *args2, **kwargs1, **kwargs2)
10:26:47 /opt/conda/envs/dask/lib/python3.10/site-packages/cudf/core/groupby/groupby.py:759: in _reduce
10:26:47     return self.agg(op)
10:26:47 /opt/conda/envs/dask/lib/python3.10/site-packages/nvtx/nvtx.py:116: in inner
10:26:47     result = func(*args, **kwargs)
10:26:47 /opt/conda/envs/dask/lib/python3.10/site-packages/cudf/core/groupby/groupby.py:631: in agg
10:26:47     ) = self._groupby.aggregate(columns, normalized_aggs)
10:26:47 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
10:26:47 

10:26:47 >   ???
10:26:47 E   TypeError: function is not supported for this dtype: sum
10:26:47 

10:26:47 groupby.pyx:192: TypeError
```

See [this CI run](https://gpuci.gpuopenanalytics.com/job/dask/job/dask/job/prb/job/dask-prb/5935/CUDA_VER=11.8.0,LINUX_VER=ubuntu20.04,PYTHON_VER=3.10,RAPIDS_VER=24.06/console) for full details

### Comment 4 ([user]):

>See this CI run for full details

Oh interesting. Thanks for running a test PR [user] ! I'll look into a fix.

### Comment 5 ([user]):

Hopefully (withheld: the upstream fix is not part of the task) will resolve the "real" gpuci failure.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
