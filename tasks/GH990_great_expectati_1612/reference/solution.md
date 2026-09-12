# Reference solution — GH990_great_expectati_1612

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH990_great_expectati_1612`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH990_great_expectati_1612/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/data_context/store/database_store_backend.py` (modified, +32/-2)
- `great_expectations/data_context/store/expectations_store.py` (modified, +6/-0)
- `tests/data_context/store/test_database_store_backend.py` (modified, +23/-0)
- `tests/data_context/store/test_expectations_store.py` (modified, +56/-2)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/store/database_store_backend.py`
```diff
@@ -96,20 +96,50 @@ def _get(self, key):
     def _set(self, key, value, **kwargs):
         cols = {k: v for (k, v) in zip(self.key_columns, key)}
         cols["value"] = value
-        ins = self._table.insert().values(**cols)
+
+        if kwargs.get("allow_update", False):
+            if self.has_key(key):
+                ins = (
+                    self._table.update()
+                    .where(getattr(self._table.columns, self.key_columns[0]) == key[0])
+                    .values(**cols)
+                )
+            else:
+                ins = self._table.insert().values(**cols)
+        else:
+            ins = self._table.insert().values(**cols)
+
         try:
             self.engine.execute(ins)
         except IntegrityError as e:
             if self._get(key) == value:
                 logger.info(f"Key {str(key)} already exists with the same value.")
             else:
                 raise ge_exceptions.StoreBackendError(
-                    "Integrity error {str(e)} while trying to store key"
+                    f"Integrity error {str(e)} while trying to store key"
                 )
 
     def _move(self):
         raise NotImplementedError
 
+    def get_url_for_key(self, key):
+        url = self._convert_engine_and_key_to_url(key)
+        return url
+
+    def _convert_engine_and_key_to_url(self, key):
+        # SqlAlchemy engine URL is formatted in the following way
+        # postgresql://postgres:password@localhost:5433/work
+        # [engine]://[username]:[password]@[host]:[port]/[db_name]
+
+        # which contains information like username and password that should not be public
+        # This function changes the formatting to the following:
+        # [engine]://[db_name]/[key]
+
+        full_url = str(self.engine.url)
+        engine_name = full_url.split("://")[0]
+        db_name = full_url.split("/")[-1]
+        return engine_name + "://" + db_name + "/" + str(key)
+
     def _has_key(self, key):
         sel = (
```

### `great_expectations/data_context/store/expectations_store.py`
```diff
@@ -48,6 +48,12 @@ def __init__(self, store_backend=None, runtime_environment=None):
             store_backend=store_backend, runtime_environment=runtime_environment
         )
 
+    def set(self, key, value):
+        self._validate_key(key)
+        return self._store_backend.set(
+            self.key_to_tuple(key), self.serialize(key, value), allow_update=True
+        )
+
     def remove_key(self, key):
         return self.store_backend.remove_key(key)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/data_context/store/database_store_backend.py`
- `great_expectations/data_context/store/expectations_store.py`
