# GH1053_dask_10590: Use the inferred filesystem/region by default when ``filesystem='arrow'`` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/10585
- Repo: https://github.com/dask/dask

## Issue Description

```python
import dask.dataframe as dd
df = dd.read_parquet("s3://coiled-data/uber/") # works
df = dd.read_parquet("s3://coiled-data/uber/", filesystem="pyarrow")
```

```python-traceback
---------------------------------------------------------------------------
OSError                                   Traceback (most recent call last)
File ~/workspace/dask/dask/backends.py:136, in CreationDispatch.register_inplace.<locals>.decorator.<locals>.wrapper(*args, **kwargs)
    135 try:
--> 136     return func(*args, **kwargs)
    137 except Exception as e:

File ~/workspace/dask/dask/dataframe/io/parquet/core.py:538, in read_parquet(path, columns, filters, categories, index, storage_options, engine, use_nullable_dtypes, dtype_backend, calculate_divisions, ignore_metadata_file, metadata_task_size, split_row_groups, blocksize, aggregate_files, parquet_file_extension, filesystem, **kwargs)
    536     blocksize = None
--> 538 read_metadata_result = engine.read_metadata(
    539     fs,
    540     paths,
    541     categories=categories,
    542     index=index,
    543     use_nullable_dtypes=use_nullable_dtypes,
    544     dtype_backend=dtype_backend,
    545     gather_statistics=calculate_divisions,
    546     filters=filters,
    547     split_row_groups=split_row_groups,
    548     blocksize=blocksize,
    549     aggregate_files=aggregate_files,
    550     ignore_metadata_file=ignore_metadata_file,
    551     metadata_task_size=metadata_task_size,
    552     parquet_file_extension=parquet_file_extension,
    553     dataset=dataset_options,
    554     read=read_options,
    555     **other_options,
    556 )
    558 # In the future, we may want to give the engine the
    559 # option to return a dedicated element for `common_kwargs`.
    560 # However, to avoid breaking the API, we just embed this
    561 # data in the first element of `parts` for now.
    562 # The logic below is inteded to handle backward and forward
    563 # compatibility with a user-defined engine.

File ~/workspace/dask/dask/dataframe/io/parquet/arrow.py:532, in ArrowDatasetEngine.read_metadata(cls, fs, paths, categories, index, use_nullable_dtypes, dtype_backend, gather_statistics, filters, split_row_groups, blocksize, aggregate_files, ignore_metadata_file, metadata_task_size, parquet_file_extension, **kwargs)
    531 # Stage 1: Collect general dataset information
--> 532 dataset_info = cls._collect_dataset_info(
    533     paths,
    534     fs,
    535     categories,
    536     index,
    537     gather_statistics,
    538     filters,
    539     split_row_groups,
    540     blocksize,
    541     aggregate_files,
    542     ignore_metadata_file,
    543     metadata_task_size,
    544     parquet_file_extension,
    545     kwargs,
    546 )
    548 # Stage 2: Generate output `meta`

File ~/workspace/dask/dask/dataframe/io/parquet/arrow.py:1047, in ArrowDatasetEngine._collect_dataset_info(cls, paths, fs, categories, index, gather_statistics, filters, split_row_groups, blocksize, aggregate_files, ignore_metadata_file, metadata_task_size, parquet_file_extension, kwargs)
   1046 if ds is None:
-> 1047     ds = pa_ds.dataset(
   1048         paths,
   1049         filesystem=_wrapped_fs(fs),
   1050         **_processed_dataset_kwargs,
   1051     )
   1053 # Get file_frag sample and extract physical_schema

File ~/mambaforge/envs/test-env/lib/python3.11/site-packages/pyarrow/dataset.py:776, in dataset(source, schema, format, filesystem, partitioning, partition_base_dir, exclude_invalid_files, ignore_prefixes)
    775 if all(_is_path_like(elem) for elem in source):
--> 776     return _filesystem_dataset(source, **kwargs)
    777 elif all(isinstance(elem, Dataset) for elem in source):

File ~/mambaforge/envs/test-env/lib/python3.11/site-packages/pyarrow/dataset.py:466, in _filesystem_dataset(source, schema, filesystem, partitioning, format, partition_base_dir, exclude_invalid_files, selector_ignore_prefixes)
    464 factory = FileSystemDatasetFactory(fs, paths_or_selector, format, options)
--> 466 return factory.finish(schema)

File ~/mambaforge/envs/test-env/lib/python3.11/site-packages/pyarrow/_dataset.pyx:2941, in pyarrow._dataset.DatasetFactory.finish()

File ~/mambaforge/envs/test-env/lib/python3.11/site-packages/pyarrow/error.pxi:144, in pyarrow.lib.pyarrow_internal_check_status()

File ~/mambaforge/envs/test-env/lib/python3.11/site-packages/pyarrow/error.pxi:115, in pyarrow.lib.check_status()

OSError: Error creating dataset. Could not read schema from 'coiled-data/uber/'. Is this a 'parquet' file?: Not a regular file: 'coiled-data/uber/'

The above exception was the direct cause of the following exception:

OSError                                   Traceback (most recent call last)
Cell In[3], line 1
----> 1 df = dd.read_parquet("s3://coiled-data/uber/", filesystem="pyarrow")

File ~/workspace/dask/dask/backends.py:138, in CreationDispatch.register_inplace.<locals>.decorator.<locals>.wrapper(*args, **kwargs)
    136     return func(*args, **kwargs)
    137 except Exception as e:
--> 138     raise type(e)(
    139         f"An error occurred while calling the {funcname(func)} "
    140         f"method registered to the {self.backend} backend.\n"
    141         f"Original Message: {e}"
    142     ) from e

OSError: An error occurred while calling the read_parquet method registered to the pandas backend.
Original Message: Error creating dataset. Could not read schema from 'coiled-data/uber/'. Is this a 'parquet' file?: Not a regular file: 'coiled-data/uber/'
```

cc [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for raising [user]! Can you share the version of pyarrow? I can look into this on Monday, but my current environment with pyarrow-12 seems to work:

```
In [1]: %time dd.read_parquet("s3://coiled-data/uber/", storage_options={"anonymous": True}, filesystem="arrow").head()
CPU times: user 731 ms, sys: 330 ms, total: 1.06 s
Wall time: 3.7 s
Out[1]: 
  hvfhs_license_num dispatching_base_num originating_base_num  ... access_a_ride_flag wav_request_flag wav_match_flag
0            HV0003               B02867               B02867  ...                  N                N            NaN
1            HV0003               B02879               B02879  ...                  N                N            NaN
2            HV0005               B02510                 <NA>  ...                  N                N            NaN
3            HV0005               B02510                 <NA>  ...                  N                N            NaN
4            HV0005               B02510                 <NA>  ...                  N                N            NaN

[5 rows x 24 columns]
```

### Comment 2 ([user]):

I'm on 13 normally, but I just re-ran with 12 and it continued to fail.  I just made a fresh environment as follows and it still failed:

```
 mamba create -n test-arrow pyarrow=12 dask ipython s3fs
```

### Comment 3 ([user]):

[user] did you have a workaround for this?

### Comment 4 ([user]):

You can create your own filesystem directly:

```
import boto3
session = boto3.session.Session()
credentials = session.get_credentials()

from pyarrow.fs import S3FileSystem

fs = S3FileSystem(
    secret_key=credentials.secret_key,
    access_key=credentials.access_key,
    region='us-east-2',
    session_token=credentials.token)
```

But you'll have to use

https://github.com/phofl/dask-expr/tree/testing

if you want to use dask-expr

### Comment 5 ([user]):

I just reproduced this on my Macbook Pro. It seems like you sometimes need to specify the region when using `filesystem="arrow"` for some reason...

```python
dd.read_parquet("s3://coiled-data/uber/", storage_options={"anonymous": True, "region": "us-east-2"}, filesystem="arrow")
```

### Comment 6 ([user]):

This reproduces without Dask:

```python
import pyarrow.dataset as ds
from pyarrow.fs import S3FileSystem
fs = S3FileSystem(
    anonymous=True,
    region="us-east-1",  # Error is resolved by `region="us-east-2”`
)
ds.dataset(["coiled-data/uber/"], filesystem=fs, format="parquet")
```

Note that the error message is much more helpful if you pass in `"coiled-data/uber/"` instead of `["coiled-data/uber/"]`:

```
OSError: When getting information for key 'uber' in bucket 'coiled-data': AWS Error UNKNOWN (HTTP status 301) during HeadObject operation: No response body. Looks like the configured region is 'us-east-1' while the bucket is located in 'us-east-2'.
```

### Comment 7 ([user]):

closed by (withheld: the upstream fix is not part of the task)

## PR Review Comments

**[user]** on `dask/dataframe/io/parquet/arrow.py`:

```suggestion
                    # Use inferred region as the default
```

**[user]** on `dask/dataframe/io/tests/test_parquet.py`:

This only reads a tiny bit of metadata, but it still takes a few seconds.

**[user]** on `dask/dataframe/io/parquet/arrow.py`:

Maybe it helps here, one can specify region as part of the URI:
`s3://[access_key:secret_key@]bucket/path[?region=]`
https://arrow.apache.org/docs/r/articles/fs.html#connecting-directly-with-a-uri

**[user]** on `dask/dataframe/io/parquet/arrow.py`:

I suppose storage options can also contain a token, and that I can't find anything about including the token in the URI; don't let this comment hinder merging though.

**[user]** on `dask/dataframe/io/parquet/arrow.py`:

Down the rabbit hole a bit, doesn't appear one can set access token in the URI; though query parameters are region, scheme, endpoint_override, and some others:
https://github.com/apache/arrow/blob/6e6fd0a30aebee6738bb4bb703344f0c866debea/cpp/src/arrow/filesystem/s3fs.cc#L334

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
