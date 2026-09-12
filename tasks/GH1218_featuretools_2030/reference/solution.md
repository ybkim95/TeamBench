# Reference solution — GH1218_featuretools_2030

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1218_featuretools_2030`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1218_featuretools_2030/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/workflows/unit_tests_with_latest_deps.yml` (modified, +1/-0)
- `docs/source/release_notes.rst` (modified, +1/-0)
- `featuretools/entityset/deserialize.py` (modified, +5/-0)
- `featuretools/entityset/serialize.py` (modified, +5/-3)
- `featuretools/tests/entityset_tests/test_serialization.py` (modified, +1/-1)
- `featuretools/tests/primitive_tests/test_feature_serialization.py` (modified, +1/-1)
- `featuretools/tests/primitive_tests/test_transform_features.py` (modified, +2/-2)
- `featuretools/tests/requirement_files/latest_requirements.txt` (modified, +1/-1)
- `featuretools/tests/requirement_files/minimum_core_requirements.txt` (modified, +1/-1)
- `featuretools/tests/requirement_files/minimum_spark_requirements.txt` (modified, +1/-1)
- `featuretools/tests/requirement_files/minimum_test_requirements.txt` (modified, +1/-1)
- `setup.cfg` (modified, +3/-3)

## Diff Summary (What the Fix Changes)

### `featuretools/entityset/deserialize.py`
```diff
@@ -34,6 +34,11 @@ def description_to_entityset(description, **kwargs):
     for df in description["dataframes"].values():
         if path is not None:
             data_path = os.path.join(path, "data", df["name"])
+            format = description.get("format")
+            if format is not None:
+                kwargs["format"] = format
+                if format == "parquet" and df["loading_info"]["table_type"] == "pandas":
+                    kwargs["filename"] = df["name"] + ".parquet"
             dataframe = read_woodwork_table(data_path, validate=False, **kwargs)
         else:
             dataframe = empty_dataframe(df)
```

### `featuretools/entityset/serialize.py`
```diff
@@ -13,10 +13,10 @@
 ps = import_or_none("pyspark.pandas")
 
 FORMATS = ["csv", "pickle", "parquet"]
-SCHEMA_VERSION = "7.0.0"
+SCHEMA_VERSION = "8.0.0"
 
 
-def entityset_to_description(entityset):
+def entityset_to_description(entityset, format=None):
     """Serialize entityset to data description.
 
     Args:
@@ -38,6 +38,7 @@ def entityset_to_description(entityset):
         "id": entityset.id,
         "dataframes": dataframes,
         "relationships": relationships,
+        "format": format,
     }
     return data_description
 
@@ -71,7 +72,8 @@ def write_data_description(entityset, path, profile_name=None, **kwargs):
 
 
 def dump_data_description(entityset, path, **kwargs):
-    description = entityset_to_description(entityset)
+    format = kwargs.get("format")
+    description = entityset_to_description(entityset, format)
     for df in entityset.dataframes:
         data_path = os.path.join(path, "data", df.ww.name)
         os.makedirs(os.path.join(data_path, "data"), exist_ok=True)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `featuretools/entityset/deserialize.py`
- `featuretools/entityset/serialize.py`
