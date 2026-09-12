# Reference solution — GH943_great_expectati_7881

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH943_great_expectati_7881`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH943_great_expectati_7881/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/data_context/data_context/cloud_data_context.py` (modified, +29/-0)
- `great_expectations/data_context/store/gx_cloud_store_backend.py` (modified, +37/-20)
- `tests/data_context/cloud_data_context/test_expectation_suite_crud.py` (modified, +21/-1)
- `tests/data_context/store/test_gx_cloud_store_backend.py` (modified, +53/-1)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/data_context/cloud_data_context.py`
```diff
@@ -13,6 +13,7 @@
     Tuple,
     Union,
     cast,
+    overload,
 )
 
 import requests
@@ -548,6 +549,33 @@ def create_expectation_suite(
 
         return expectation_suite
 
+    @overload
+    def delete_expectation_suite(
+        self,
+        expectation_suite_name: str = ...,
+        ge_cloud_id: None = ...,
+        id: None = ...,
+    ) -> bool:
+        ...
+
+    @overload
+    def delete_expectation_suite(
+        self,
+        expectation_suite_name: None = ...,
+        ge_cloud_id: str = ...,
+        id: None = ...,
+    ) -> bool:
+        ...
+
+    @overload
+    def delete_expectation_suite(
+        self,
+        expectation_suite_name: None = ...,
+        ge_cloud_id: None = ...,
+        id: str = ...,
+    ) -> bool:
+        ...
+
     def delete_expectation_suite(
         self,
         expectation_suite_name: str | None = None,
@@ -569,6 +597,7 @@ def delete_expectation_suite(
         key = GXCloudIdentifier(
             resource_type=GXCloudRESTResource.EXPECTATION_SUITE,
             id=id,
+            resource_name=expectation_suite_name,
         )
 
         return self.expectations_store.remove_key(key)
```

### `great_expectations/data_context/store/gx_cloud_store_backend.py`
```diff
@@ -469,28 +469,45 @@ def remove_key(self, key):
             key = key.to_tuple()
 
         id = key[1]
-
-        data = {
-            "data": {
-                "type": self.ge_cloud_resource_type,
-                "id": id,
-                "attributes": {
-                    "deleted": True,
-                },
-            }
-        }
-
-        url = construct_url(
-            base_url=self.ge_cloud_base_url,
-            organization_id=self.ge_cloud_credentials["organization_id"],
-            resource_name=self.ge_cloud_resource_name,
-            id=id,
-        )
+        if len(key) == 3:
+            resource_object_name = key[2]
+        else:
+            resource_object_name = None
 
         try:
-            response = self._session.delete(url, json=data)
-            response.raise_for_status()
-            return True
+            # prefer deletion by id if id present
+            if id:
+                data = {
+                    "data": {
+                        "type": self.ge_cloud_resource_type,
+                        "id": id,
+                        "attributes": {
+                            "deleted": True,
+                        },
+                    }
+                }
+
+                url = construct_url(
+                    base_url=self.ge_cloud_base_url,
+                    organization_id=self.ge_cloud_credentials["organization_id"],
+                    resource_name=self.ge_cloud_resource_name,
+                    id=id,
+                )
+                response = self._session.delete(url, json=data)
+                response.raise_for_status()
+                return True
+            # delete by name
+            elif resource_object_name:
+                url = construct_url(
+                    base_url=self.ge_cloud_base_url,
+                    organization_id=self.ge_cloud_credentials["organization_id"],
+                    resource_name=self.ge_cloud_resource_name,
+                )
+      
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/data_context/data_context/cloud_data_context.py`
- `great_expectations/data_context/store/gx_cloud_store_backend.py`
