# Reference solution — GH937_airflow_63617

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH937_airflow_63617`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH937_airflow_63617/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `airflow-core/src/airflow/dag_processing/manager.py` (modified, +20/-15)
- `airflow-core/src/airflow/models/dag.py` (modified, +1/-1)
- `airflow-core/tests/unit/dag_processing/test_manager.py` (modified, +120/-4)
- `airflow-core/tests/unit/models/test_dag.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `airflow-core/src/airflow/dag_processing/manager.py`
```diff
@@ -690,10 +690,11 @@ def _refresh_dag_bundles(self, known_files: dict[str, set[DagFileInfo]]):
 
             known_files[bundle.name] = found_files
 
-            self.deactivate_deleted_dags(bundle_name=bundle.name, present=found_files)
+            observed_filelocs = self._get_observed_filelocs(found_files)
+            self.deactivate_deleted_dags(bundle_name=bundle.name, observed_filelocs=observed_filelocs)
             self.clear_orphaned_import_errors(
                 bundle_name=bundle.name,
-                observed_filelocs={str(x.rel_path) for x in found_files},  # todo: make relative
+                observed_filelocs=observed_filelocs,
             )
 
         if any_refreshed:
@@ -710,17 +711,17 @@ def _find_files_in_bundle(self, bundle: BaseDagBundle) -> list[Path]:
 
         return rel_paths
 
-    def deactivate_deleted_dags(self, bundle_name: str, present: set[DagFileInfo]) -> None:
-        """Deactivate DAGs that come from files that are no longer present in bundle."""
-
-        def find_zipped_dags(abs_path: os.PathLike) -> Iterator[str]:
-            """
-            Find dag files in zip file located at abs_path.
+    def _get_observed_filelocs(self, present: set[DagFileInfo]) -> set[str]:
+        """
+        Return observed DAG source paths for bundle entries.
 
-            We return the abs "paths" formed by joining the relative path inside the zip
-            with the path to the zip.
+        For regular files this includes the relative file path.
+        For ZIP archives this includes DAG-like inner paths such as
+        ``archive.zip/dag.py``.
+        """
 
-            """
+        def find_zipped_dags(abs_path: os.PathLike) -> Iterator[str]:
+            """Yield absolute paths for DAG-like files inside a ZIP archive."""
             try:
                 with zipfile.ZipFile(abs_path) as z:
                     for info in z.infolist():
@@ -729,22 +730,26 @@ def find_zipped_dags(abs_path: os.PathLike) -> Iterator[str]:
  
```

### `airflow-core/src/airflow/models/dag.py`
```diff
@@ -588,7 +588,7 @@ def dag_display_name(self) -> str:
     def deactivate_deleted_dags(
         cls,
         bundle_name: str,
-        rel_filelocs: list[str],
+        rel_filelocs: set[str],
         session: Session = NEW_SESSION,
     ) -> bool:
         """
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `airflow-core/src/airflow/dag_processing/manager.py`
- `airflow-core/src/airflow/models/dag.py`
