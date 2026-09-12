# GH1005_ray_60236: [Data] - Only return selected data columns in hive partitioned parquet files — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ray-project/ray/issues/60215
- Repo: https://github.com/ray-project/ray

## Issue Description

### What happened + What you expected to happen

When using the `columns` argument of `ray.data.read_parquet` to exclude all the partition columns the resulting data incorrectly contains all the partition columns. The data should contain only the `columns` specified.

### Versions / Dependencies

The bug was introduced by ray==2.53.0

Python 3.10.15
Ubuntu 24.04.3
Python packages:
```
$ pip freeze
attrs==25.4.0
certifi==2026.1.4
charset-normalizer==3.4.4
click==8.3.1
filelock==3.20.3
idna==3.11
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
msgpack==1.1.2
numpy==2.2.6
packaging==25.0
pandas==2.3.3
protobuf==6.33.4
pyarrow==22.0.0
python-dateutil==2.9.0.post0
pytz==2025.2
PyYAML==6.0.3
ray==2.53.0
referencing==0.37.0
requests==2.32.5
rpds-py==0.30.0
six==1.17.0
typing_extensions==4.15.0
tzdata==2025.3
urllib3==2.6.3
```

### Reproduction script

```
import tempfile

import pyarrow
import pyarrow.dataset

import ray

table = pyarrow.table(
    {
        "partition_column0": [1, 1, 3, 2, 2],
        "partition_column1": ["a", "a", "a", "a", "b"],
        "normal_column0": [10.5, 20.3, 15.7, 30.2, 25.8],
        "normal_column1": [130.5, 2670.3, 125.7, 370.2, 235.8],
    }
)

partition_columns = ["partition_column0", "partition_column1"]

with tempfile.TemporaryDirectory() as tmpdir:
    pyarrow.dataset.write_dataset(
        table,
        tmpdir,
        partitioning=partition_columns,
        partitioning_flavor="hive",
        format="parquet",
    )
    ray_dataset = ray.data.read_parquet(
        tmpdir,
        columns=["normal_column0"],
        partitioning=ray.data.datasource.partitioning.Partitioning("hive"),
    )
    print(ray_dataset.schema())
    print(ray_dataset.take_all())
```
which returns
```
2026-01-16 16:07:07,242 INFO parquet_datasource.py:1048 -- Estimated parquet encoding ratio is 0.016.
2026-01-16 16:07:07,242 INFO parquet_datasource.py:1108 -- Estimated parquet reader batch size at 14913081 rows
Column          Type
------          ----
normal_column0  double
2026-01-16 16:07:07,593 INFO logging.py:397 -- Registered dataset logger for dataset dataset_0_0
2026-01-16 16:07:07,602 INFO streaming_executor.py:178 -- Starting execution of Dataset dataset_0_0. Full logs are in /tmp/ray/session_2026-01-16_16-07-05_312498_632975/logs/ray-data
2026-01-16 16:07:07,602 INFO streaming_executor.py:179 -- Execution plan of Dataset dataset_0_0: InputDataBuffer[Input] -> TaskPoolMapOperator[ReadParquet]
2026-01-16 16:07:07,608 INFO streaming_executor.py:686 -- [dataset]: A new progress UI is available. To enable, set `ray.data.DataContext.get_current().enable_rich_progress_bars = True` and `ray.data.DataContext.get_current().use_ray_tqdm = False`.
2026-01-16 16:07:07,608 WARNING resource_manager.py:136 -- ⚠️  Ray's object store is configured to use only 42.9% of available memory (28.3GiB out of 66.1GiB total). For optimal Ray Data performance, we recommend setting the object store to at least 50% of available memory. You can do this by setting the 'object_store_memory' parameter when calling ray.init() or by setting the RAY_DEFAULT_OBJECT_STORE_MEMORY_PROPORTION environment variable.
2026-01-16 16:07:07,989 INFO streaming_executor.py:304 -- ✔️  Dataset dataset_0_0 execution finished in 0.39 seconds
[{'normal_column0': 10.5, 'partition_column0': '1', 'partition_column1': 'a'}, {'normal_column0': 20.3, 'partition_column0': '1', 'partition_column1': 'a'}, {'normal_column0': 30.2, 'partition_column0': '2', 'partition_column1': 'a'}, {'normal_column0': 25.8, 'partition_column0': '2', 'partition_column1': 'b'}, {'normal_column0': 15.7, 'partition_column0': '3', 'partition_column1': 'a'}]
```
If you look at the output you will see that `.schema()` correctly returns only `normal_column0`, but the data also contains both the partition columns. If you set `columns` to include one of the partition columns e.g. `columns=["partition_column1", "normal_column0"]` then it works correctly. 

### Issue Severity

Medium: It is a significant difficulty but I can work around it.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I ran a `git bisect` and identified that (withheld: the upstream fix is not part of the task) is the PR that introduced this problem.

### Comment 2 ([user]):

Thanks for bringing this up. This PR #60236 should address the issue.

### Comment 3 ([user]):

Thanks - that was quick

## PR Review Comments

**[user]** on `python/ray/data/_internal/datasource/parquet_datasource.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The logic here is correct, but this comment could be clearer to improve future maintainability. It currently infers user intent, but the condition `not self._partition_columns` is about the dataset's properties (i.e., it's not partitioned). A more direct comment explaining this would be better.

How about this?

```suggestion
# If a projection is active but the dataset has no partition columns,
# then no partition columns should be included in the output.
# Returning [] ensures that no partition columns are added,
# whereas the previous `None` was misinterpreted as "all partitions".
```

**[user]** on `python/ray/data/tests/datasource/test_parquet.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This is a great regression test for ensuring `select_columns()` doesn't implicitly add back partition columns.

However, it seems this test doesn't cover the code path changed in `parquet_datasource.py`. The change is under the `if not self._partition_columns:` condition, which is for when the `ParquetDatasource` is configured with an empty list of partition columns.

In this test, `read_parquet` is called without a `columns` argument, so `ParquetDatasource` infers `self._partition_columns` from the partitioned path (e.g., `['partition_col0', 'partition_col1']`), which is not empty. The filtering of partition columns happens later in `_get_partition_columns` because they are not in the projection map from `select_columns`.

To properly test the code change, we need a scenario where `ParquetDatasource` is initialized with an empty `_partition_columns`. This happens, for example, when `read_parquet` is called with a `columns` argument that does not include any partition columns.

Could you please add another test case to cover this scenario? Here is a suggestion:

```python
def test_read_partitioned_with_columns_arg_excluding_partitions(
    ray_start_regular_shared, tmp_path
):
    """
    Tests that when `read_parquet` is called with the `columns` argument,
    and that argument does not include any partition columns, then no
    partition columns are included in the resulting dataset.
    """
    table = pa.table(
        {
            "data_col0": [10.5, 20.3, 30.2],
            "p": [1, 2, 1],
        }
    )
    pq.write_to_dataset(
        table,
        root_path=tmp_path,
        partition_cols=["p"],
    )

    # Read with `columns` argument that excludes partition columns.
    # This should cause `self._partition_columns` in ParquetDatasource to be `[]`,
    # hitting the changed code path.
    ds = ray.data.read_parquet(tmp_path, columns=["data_col0"])

    # Verify only the requested column is present.
    # Before the fix, this would also include "p".
    assert ds.columns() == ["data_col0"]

    # Verify data is correct.
    result_df = ds.to_pandas()
    expected_df = pd.DataFrame({"data_col0": [10.5, 20.3, 30.2]})
    assert rows_same(result_df, expected_df)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
