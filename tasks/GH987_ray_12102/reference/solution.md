# Reference solution — GH987_ray_12102

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH987_ray_12102`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH987_ray_12102/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dashboard/actor_utils.py` (modified, +1/-1)
- `python/ray/_private/function_manager.py` (modified, +18/-8)
- `python/ray/_raylet.pxd` (modified, +1/-0)
- `python/ray/_raylet.pyx` (modified, +8/-5)
- `python/ray/includes/function_descriptor.pxi` (modified, +23/-4)
- `python/ray/job_config.py` (modified, +5/-0)
- `python/ray/tests/test_basic_2.py` (modified, +43/-0)
- `python/ray/workers/default_worker.py` (modified, +12/-17)
- `src/ray/common/function_descriptor.h` (modified, +6/-1)
- `src/ray/raylet/worker_pool.cc` (modified, +17/-29)

## Diff Summary (What the Fix Changes)

### `dashboard/actor_utils.py`
```diff
@@ -27,7 +27,7 @@ def construct_actor_groups(actors):
 def actor_classname_from_task_spec(task_spec):
     return task_spec.get("functionDescriptor", {})\
                 .get("pythonFunctionDescriptor", {})\
-                .get("className", "Unknown actor class")
+                .get("className", "Unknown actor class").split(".")[-1]
 
 
 def _group_actors_by_python_class(actors):
```

### `python/ray/_private/function_manager.py`
```diff
@@ -268,7 +268,11 @@ def _load_function_from_local(self, job_id, function_descriptor):
         )
         try:
             module = importlib.import_module(module_name)
-            function = getattr(module, function_name)._function
+            parts = [part for part in function_name.split(".") if part]
+            object = module
+            for part in parts:
+                object = getattr(object, part)
+            function = object._function
             self._function_execution_info[job_id][function_id] = (
                 FunctionExecutionInfo(
                     function=function,
@@ -278,7 +282,8 @@ def _load_function_from_local(self, job_id, function_descriptor):
             self._num_task_executions[job_id][function_id] = 0
         except Exception as e:
             raise RuntimeError(f"Function {function_descriptor} failed "
-                               "to be loaded from local code. "
+                               "to be loaded from local code.\n"
+                               f"sys.path: {sys.path}, "
                                f"Error message: {str(e)}")
 
     def _wait_for_function(self, function_descriptor, job_id, timeout=10):
@@ -356,7 +361,8 @@ def export_actor_class(self, Class, actor_creation_function_descriptor,
         key = (b"ActorClass:" + job_id.binary() + b":" +
                actor_creation_function_descriptor.function_id.binary())
         actor_class_info = {
-            "class_name": actor_creation_function_descriptor.class_name,
+            "class_name": actor_creation_function_descriptor.class_name.split(
+                ".")[-1],
             "module": actor_creation_function_descriptor.module_name,
             "class": pickle.dumps(Class),
             "job_id": job_id.binary(),
@@ -443,14 +449,18 @@ def _load_actor_class_from_local(self, job_id,
             actor_creation_function_descriptor.class_name)
         try:
             module = importlib.import_module(module_name)
-            actor_c
```

### `python/ray/job_config.py`
```diff
@@ -39,6 +39,11 @@ def __init__(self,
         self.num_java_workers_per_process = num_java_workers_per_process
         self.jvm_options = jvm_options or []
         self.code_search_path = code_search_path or []
+        # It's difficult to find the error that caused by the
+        # code_search_path is a string. So we assert here.
+        assert isinstance(self.code_search_path, (list, tuple)), \
+            f"The type of code search path is incorrect: " \
+            f"{type(code_search_path)}"
         self.runtime_env = runtime_env or dict()
 
     def serialize(self):
```

### `python/ray/workers/default_worker.py`
```diff
@@ -97,13 +97,6 @@
     type=str,
     default="",
     help="The configuration of object spilling. Only used by I/O workers.")
-parser.add_argument(
-    "--code-search-path",
-    default=None,
-    type=str,
-    help="A list of directories or jar files separated by colon that specify "
-    "the search path for user code. This will be used as `CLASSPATH` in "
-    "Java and `PYTHONPATH` in Python.")
 parser.add_argument(
     "--logging-rotate-bytes",
     required=False,
@@ -156,16 +149,6 @@
     if raylet_ip_address is None:
         raylet_ip_address = args.node_ip_address
 
-    code_search_path = args.code_search_path
-    load_code_from_local = False
-    if code_search_path is not None:
-        load_code_from_local = True
-        for p in code_search_path.split(":"):
-            if os.path.isfile(p):
-                p = os.path.dirname(p)
-            sys.path.append(p)
-    ray.worker.global_worker.set_load_code_from_local(load_code_from_local)
-
     ray_params = RayParams(
         node_ip_address=args.node_ip_address,
         raylet_ip_address=raylet_ip_address,
@@ -187,6 +170,18 @@
     ray.worker._global_node = node
     ray.worker.connect(node, mode=mode)
 
+    # Add code search path to sys.path, set load_code_from_local.
+    core_worker = ray.worker.global_worker.core_worker
+    code_search_path = core_worker.get_job_config().code_search_path
+    load_code_from_local = False
+    if code_search_path:
+        load_code_from_local = True
+        for p in code_search_path:
+            if os.path.isfile(p):
+                p = os.path.dirname(p)
+            sys.path.insert(0, p)
+    ray.worker.global_worker.set_load_code_from_local(load_code_from_local)
+
     # Setup log file.
     out_file, err_file = node.get_log_file_handles(
         get_worker_log_file_name(args.worker_type))
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `dashboard/actor_utils.py`
- `python/ray/_private/function_manager.py`
- `python/ray/job_config.py`
- `python/ray/workers/default_worker.py`
