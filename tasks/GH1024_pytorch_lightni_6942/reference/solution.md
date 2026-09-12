# Reference solution — GH1024_pytorch_lightni_6942

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1024_pytorch_lightni_6942`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1024_pytorch_lightni_6942/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +7/-1)
- `pytorch_lightning/plugins/environments/cluster_environment.py` (modified, +4/-0)
- `pytorch_lightning/plugins/environments/lightning_environment.py` (modified, +4/-0)
- `pytorch_lightning/plugins/training_type/ddp.py` (modified, +2/-3)
- `tests/plugins/environments/test_lightning_environment.py` (modified, +11/-0)

## Diff Summary (What the Fix Changes)

### `pytorch_lightning/plugins/environments/cluster_environment.py`
```diff
@@ -52,3 +52,7 @@ def local_rank(self) -> int:
     @abstractmethod
     def node_rank(self) -> int:
         """ The rank (index) of the node on which the current process runs. """
+
+    def teardown(self) -> None:
+        """ Clean up any state set after execution finishes. """
+        pass
```

### `pytorch_lightning/plugins/environments/lightning_environment.py`
```diff
@@ -68,6 +68,10 @@ def node_rank(self) -> int:
         group_rank = os.environ.get("GROUP_RANK", 0)
         return int(os.environ.get("NODE_RANK", group_rank))
 
+    def teardown(self) -> None:
+        if "WORLD_SIZE" in os.environ:
+            del os.environ["WORLD_SIZE"]
+
 
 def find_free_network_port() -> int:
     """
```

### `pytorch_lightning/plugins/training_type/ddp.py`
```diff
@@ -280,9 +280,8 @@ def pre_dispatch(self):
 
         self.barrier()
 
-    def post_dispatch(self):
-        if "WORLD_SIZE" in os.environ:
-            del os.environ["WORLD_SIZE"]
+    def post_dispatch(self) -> None:
+        self.cluster_environment.teardown()
 
     def barrier(self, *args, **kwargs):
         if torch_distrib.is_initialized():
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pytorch_lightning/plugins/environments/cluster_environment.py`
- `pytorch_lightning/plugins/environments/lightning_environment.py`
- `pytorch_lightning/plugins/training_type/ddp.py`
