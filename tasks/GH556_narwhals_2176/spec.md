# GH556_narwhals_2176: fix: don't downcast `large_string` to `string` unnecessarily in `concat_str` for PyArrow — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/narwhals-dev/narwhals/issues/2097
- Repo: https://github.com/narwhals-dev/narwhals

## Issue Description

Currently we convert `nw.String` to pyarrow string. Polars would convert `pl.String` to pyarrow large_string. We should probably be doing the same?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Sounds the right move to me.

[user] maybe you'd be able to reveal a bug in the current implementation - by passing a string that would trigger an overflow?

I've no idea if we'd have coverage for that already in a test

### Comment 2 ([user]):

I think we should treat this as a bug
```python
df = pa.table({
    'store': ['foo', 'bar'],
    'item': ['axe', 'saw']
}, schema=pa.schema([('store', pa.large_string()), ('item', pa.large_string())]))

print(nw.from_native(df).with_columns(store_item = nw.concat_str('store', 'item', separator='-')))
```
results in
```
┌───────────────────────────────────┐
|        Narwhals DataFrame         |
|-----------------------------------|
|pyarrow.Table                      |
|store: large_string                |
|item: large_string                 |
|store_item: string                 |
|----                               |
|store: [["foo","bar"]]             |
|item: [["axe","saw"]]              |
|store_item: [["foo-axe","bar-saw"]]|
└───────────────────────────────────┘
```
So, two `large_string`s got concatenated into a `string`. I'd have expected them to get concatenated into a `large-string`

### Comment 3 ([user]):

Does `pyarrow` keep the result as `large_string` if you rewrite (https://github.com/narwhals-dev/narwhals/issues/2097#issuecomment-2713939861) using only native functions?

Seems plausible that it could be down-casting to reduce memory usage if it wasn't needed?

Do agree it is a bug if we aren't matching the native behavior though

### Comment 4 ([user]):

> Does pyarrow keep the result as large_string if you rewrite (https://github.com/narwhals-dev/narwhals/issues/2097#issuecomment-2713939861) using only native functions?

yup

### Comment 5 ([user]):

```python
In [5]: pc.binary_join_element_wise(df['store'], df['item'])
Out[5]: 
<pyarrow.lib.ChunkedArray object at 0x7f09e680d8a0>
[
  [
    "foo",
    "bar"
  ]
]

In [6]: pc.binary_join_element_wise(df['store'], df['item']).type
Out[6]: DataType(large_string)
```

### Comment 6 ([user]):

> > Does pyarrow keep the result as large_string if you rewrite ([#2097 (comment)](https://github.com/narwhals-dev/narwhals/issues/2097#issuecomment-2713939861)) using only native functions?
> 
> yup

🐛 🐛 🐛

### Comment 7 ([user]):

The "concatenating strings" part is definitely a bug, and we'll fix it for the next release, but I'm less sure about mapping `large_string` to `string`

First, because mixing them doesn't seem very well-supported in PyArrow https://github.com/apache/arrow/issues/45717

Second, because PyArrow defaults to `string` for `pa.scalar('a')`, and in `read_csv`. So, we should probably respect their default

## PR Review Comments

**[user]** on `narwhals/_arrow/namespace.py`:

```suggestion
                *(s.native for s in compliant_series_list), separator=separator
```

**[user]** on `narwhals/_arrow/utils.py`:

```suggestion
        return it, lit(separator, type=pa.string())
```

**[user]** on `narwhals/_arrow/utils.py`:

```suggestion
    return it, lit(separator, type=pa.large_string())
```

**[user]** on `narwhals/_arrow/utils.py`:

[user] I think I can shorten this **and** avoid the `# type: ignore[arg-type]`.

Mind if I add a commit?

**[user]** on `narwhals/_arrow/utils.py`:

sure thaknks

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
