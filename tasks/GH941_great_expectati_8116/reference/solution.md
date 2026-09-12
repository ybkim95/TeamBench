# Reference solution — GH941_great_expectati_8116

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH941_great_expectati_8116`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH941_great_expectati_8116/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/data_context/store/gx_cloud_store_backend.py` (modified, +59/-11)
- `tests/data_context/cloud_data_context/test_checkpoint_crud.py` (modified, +121/-14)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/store/gx_cloud_store_backend.py`
```diff
@@ -44,7 +44,7 @@ class PayloadDataField(TypedDict):
 
 
 class ResponsePayload(TypedDict):
-    data: PayloadDataField
+    data: PayloadDataField | list[PayloadDataField]
 
 
 AnyPayload = Union[ResponsePayload, ErrorPayload]
@@ -222,7 +222,7 @@ def __init__(  # noqa: PLR0913
         }
         filter_properties_dict(properties=self._config, inplace=True)
 
-    def _get(self, key: Tuple[str, ...]) -> ResponsePayload:  # type: ignore[override]
+    def _get(self, key: Tuple[GXCloudRESTResource, str | None, str | None]) -> ResponsePayload:  # type: ignore[override]
         ge_cloud_url = self.get_url_for_key(key=key)
         params: Optional[dict] = None
         try:
@@ -387,7 +387,9 @@ def _post(self, value: Any, **kwargs) -> GXCloudResourceRef:
             response_json = response.json()
 
             object_id = response_json["data"]["id"]
-            object_url = self.get_url_for_key((self.ge_cloud_resource_type, object_id))
+            object_url = self.get_url_for_key(
+                (self.ge_cloud_resource_type, object_id, None)
+            )
             # This method is where posts get made for all cloud store endpoints. We pass
             # the response_json back up to the caller because the specific resource may
             # want to parse resource specific data out of the response.
@@ -471,7 +473,9 @@ def list_keys(self, prefix: Tuple = ()) -> List[Tuple[GXCloudRESTResource, str,
             )
 
     def get_url_for_key(  # type: ignore[override]
-        self, key: Tuple[str, ...], protocol: Optional[Any] = None
+        self,
+        key: Tuple[GXCloudRESTResource, str | None, str | None],
+        protocol: Optional[Any] = None,
     ) -> str:
         id = key[1]
         url = construct_url(
@@ -542,26 +546,70 @@ def remove_key(self, key):
                 f"Unable to delete object in GX Cloud Store Backend: {repr(e)}"
             )
 
-    def _update(self, key, value, **kwargs):
-        existing = self._get(key)
+    def _get_one
```

## Moved from `brief.md`

## Files That May Need Changes

- `great_expectations/data_context/store/gx_cloud_store_backend.py`
