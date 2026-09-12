# GH1004_dask_11665: Fix filtering on parquet file containing a struct column — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/11652
- Repo: https://github.com/dask/dask

## Issue Description

<!-- Please include a self-contained copy-pastable example that generates the issue if possible.

Please be concise with code posted. See guidelines below on how to provide a good bug report:

- Craft Minimal Bug Reports http://matthewrocklin.com/blog/work/2018/02/28/minimal-bug-reports
- Minimal Complete Verifiable Examples https://stackoverflow.com/help/mcve

Bug reports that follow these guidelines are easier to diagnose, and so are often handled much more quickly.
-->

**Describe the issue**:

When reading parquet files with `dd.read_parquet(path, columns, filters)` if the parquet contains columns of dtype `pa.struct()` the filters may fail.

**Minimal Complete Verifiable Example**:

```python
import pyarrow as pa
import pyarrow.parquet as pq

# Define data for the table
data = [
    pa.array([
        {'subfield1': 10, 'subfield2': 12},  # Nested column row 1
        {'subfield1': 20, 'subfield2': 12},  # Nested column row 2
        {'subfield1': 30, 'subfield2': 12}   # Nested column row 3
    ]),
    pa.array(['aa', 'bb', 'bb'])  # ID column
]

# Define the schema, including the nested column
schema = pa.schema([
    ('nested_column', pa.struct([
        ('subfield1', pa.int32()),
        ('subfield2', pa.int32())
    ])),
    ('id', pa.string())
])

# Create the table
table = pa.Table.from_arrays(data, schema=schema)

# Write to a Parquet file
pq.write_table(table, 'nested_example.parquet', row_group_size=1)




import dask.dataframe

ddf = dask.dataframe.read_parquet('nested_example.parquet', filters=[('id', 'in', ['bb'])])
ddf.compute()
```
Running this code we obtain the following error

```shell
File "/home/melciorpijoan/workspace/smadex/smadex-algorithm/smadex-smadeep/data/dmitry_dask_filters.py", line 31, in <module>
    ddf.compute()
  File "/home/melciorpijoan/miniconda3/envs/smadeep310-dask2024121/lib/python3.10/site-packages/dask_expr/io/parquet.py", line 1442, in _plan
    parts, stats = apply_filters(parts, stats, self.filters)
  File "/home/melciorpijoan/miniconda3/envs/smadeep310-dask2024121/lib/python3.10/site-packages/dask/dataframe/io/parquet/core.py", line 1441, in apply_filters
    out_parts, out_statistics = apply_conjunction(parts, statistics, conjunction)
  File "/home/melciorpijoan/miniconda3/envs/smadeep310-dask2024121/lib/python3.10/site-packages/dask/dataframe/io/parquet/core.py", line 1428, in apply_conjunction
    and any(min <= item <= max for item in value)
  File "/home/melciorpijoan/miniconda3/envs/smadeep310-dask2024121/lib/python3.10/site-packages/dask/dataframe/io/parquet/core.py", line 1428, in <genexpr>
    and any(min <= item <= max for item in value)
TypeError: '<=' not supported between instances of 'float' and 'str'
```
This is clearly wrong because the column "id" is a string, it should not be read as a float.

**Anything else we need to know?**:
We have analyzed a bit the traceback with a coworker and we believe that the issue is that the filter tries to read the wrong column. In [dask/dataframe/io/parquet/arrow.py line 292](https://github.com/dask/dask/blob/4fb8993ce15831c03ff21575db7fd3acdcac9ebe/dask/dataframe/io/parquet/arrow.py#L292) we have
```python
row_group_schema = {
        col_name: i for i, col_name in enumerate(row_group.schema.names)
    }

    def name_stats(column_name):
        col = row_group.metadata.column(row_group_schema[column_name])
```
The problem is that in the schema we have the names `['nested_column', 'id']` and in the parquet metadata we have the nested column flattened `['nested_column.subfield1', 'nested_column.subfield2', 'id']`.
```python
ds = pa.dataset.dataset('nested_example.parquet')

ff = list(ds.get_fragments())[0]
rg = ff.split_by_row_group()[0]
r = rg.row_groups[0]
m = r.metadata

print(r.schema.names)
print("metadata": m.to_dict())
```
Output
```shell
['nested_column', 'id']
{
    "num_columns": 3,
    "columns": [
        {
            'path_in_schema': 'nested_column.subfield1',
            ...
        },
        {
            'path_in_schema': 'nested_column.subfield2',
            ...
        },
        {
            'path_in_schema': 'id',
            ...
        }
    ]
}
```
So when we get the index of the column `"id"` in the schema we get 1 but the column that corresponds to the index 1 in the parquet is `'nested_column.subfield2'`, which is numeric.

**Environment**:
We have checked this bug in two versions, our production code runs with
- Dask version: 2024.8.0, without query planning
- Pandas version: 2.2.0
- Pyarrow version: 17.0.0
- Python version: 3.10
- Operating System: ubuntu
- Install method (conda, pip, source): pip

We have also checked if the bug exists in the latest release of dask
- Dask version: 2024.12.1, with query planning
- Pandas version: 2.2.0
- Pyarrow version: 17.0.0
- Python version: 3.10
- Operating System: ubuntu
- Install method (conda, pip, source): pip

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

cc [user] do you have thoughts here?

### Comment 2 ([user]):

Thanks for raising [user] ! Hopefully (withheld: the upstream fix is not part of the task) addresses this bug?

### Comment 3 ([user]):

Thanks for the quick fix! :)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
