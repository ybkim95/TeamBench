# GH894_great_expectati_4044: [FEATURE][BUGFIX] Support nullable int column types — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/great-expectations/great_expectations/issues/4040
- Repo: https://github.com/great-expectations/great_expectations

## Issue Description

**Describe the bug**
When a dataframe uses one of Pandas' nullable ``IntXDtype()`` types (most commonly, ``Int32Dtype()``), there is no way to validate this type in ``expect_column_values_to_be_in_type_list``.

**To Reproduce**
1. Create a dataframe with a ``pd.Int32Dtype()`` column. It may need to contain some null values.
2. Save it to parquet (tested with pyarrow engine).
3. Create expectation suite that checks the type of that column. The validation can include all the usual int types. Also, for good measure, add ``Int32Dtype``, which, reading the ``_validate_pandas`` function, seems intended to work.
4. Run the expectation suite against the parquet file.

**Example**
```python
validator.expect_column_values_to_be_in_type_list(
    column="Week",
    type_list=[
        "int32",  # This seems like it should work based on error message
        "Int32Dtype",  # This should work, based on reading code
    ],
)
```
returns
```
{
  "exception_info": {
    "raised_exception": false,
    "exception_traceback": null,
    "exception_message": null
  },
  "meta": {},
  "success": false,
  "result": {
    "observed_value": "int32"
  }
}
```
even though
```python
validator.head().dtypes['Week']
```
returns
```
Int32Dtype()
```

This is because
```python
assert validator.head().dtypes['Week'] not in [pd.Int32Dtype]
assert validator.head().dtypes['Week'] in [pd.Int32Dtype()]
```

**Expected behavior**
- Including ``Int32Dtype`` ought to result in successful validation.
- Failure ought to indicate that this string should be added (instead, it prints that the column type is ``int32``, which is very confusing if ``int32`` is in the list of types to consider valid).
- The various ``IntXDtype`` types should be automatically included in the auto-generated list of integer types used by the default profiler.

**Environment (please complete the following information):**
 - Operating System: Windows 11
 - Great Expectations Version: 0.14.1

**Fix**
``ExpectColumnValuesToBeInTypeList._validate_pandas`` (line 345 and following) does provide functionality for looking up dtypes from pandas. However, it uses the types themselves, whereas these Pandas dtypes (subclasses of ``ExtensionDtype``) are intended to be instantiated like ``pd.Int32Dtype()`` to get the desired type.

Thus,
```python
                        pd_type = getattr(pd, type_)
                        if isinstance(pd_type, type):
                            comp_types.append(pd_type)
```
should be updated to something like
```python
                        pd_type = getattr(pd, type_)
                        if isinstance(pd_type, type):
                            comp_types.append(pd_type())
```
Applying this change makes my particular example succeed when ``Int32Dtype`` is included in the list.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'd like to submit a PR for this.

### Comment 2 ([user]):

Thank you very much [user], we'll keep an eye out. Let us know if you need any help getting this over the line.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
