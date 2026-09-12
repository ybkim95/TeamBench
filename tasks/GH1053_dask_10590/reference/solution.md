# Reference solution — GH1053_dask_10590

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1053_dask_10590`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1053_dask_10590/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/io/parquet/arrow.py` (modified, +7/-3)
- `dask/dataframe/io/tests/test_parquet.py` (modified, +12/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/io/parquet/arrow.py`
```diff
@@ -454,9 +454,13 @@ def extract_filesystem(
                 urlpath = [stringify_path(urlpath)]
 
             if fs in ("arrow", "pyarrow"):
-                fs = type(pa_fs.FileSystem.from_uri(urlpath[0])[0])(
-                    **(storage_options or {})
-                )
+                fs = pa_fs.FileSystem.from_uri(urlpath[0])[0]
+                if storage_options:
+                    # Use inferred region as the default
+                    region = (
+                        {} if "region" in storage_options else {"region": fs.region}
+                    )
+                    fs = type(fs)(**region, **storage_options)
 
             fsspec_fs = ArrowFSWrapper(fs)
             if urlpath[0].startswith("C:") and isinstance(fs, pa_fs.LocalFileSystem):
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/io/parquet/arrow.py`
