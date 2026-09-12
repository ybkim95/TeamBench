# Reference solution — GH1068_pytorch_166924

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1068_pytorch_166924`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1068_pytorch_166924/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/dynamo/test_ctx_manager.py` (modified, +53/-0)
- `test/dynamo/test_repros.py` (modified, +0/-42)
- `torch/_dynamo/resume_execution.py` (modified, +94/-45)
- `torch/_dynamo/symbolic_convert.py` (modified, +6/-2)

## Diff Summary (What the Fix Changes)

### `torch/_dynamo/resume_execution.py`
```diff
@@ -250,8 +250,8 @@ class ResumeFunctionMetadata:
         default_factory=list
     )
     # per-offset map from new block target offsets to original block target offsets
-    block_target_offset_remap: dict[int, dict[int, int]] = dataclasses.field(
-        default_factory=dict
+    block_target_offset_remap: dict[tuple[int, int], dict[int, int]] = (
+        dataclasses.field(default_factory=dict)
     )
 
 
@@ -291,20 +291,23 @@ class ContinueExecutionCache:
     generated_code_metadata = ExactWeakKeyDictionary()
 
     @classmethod
-    def lookup(cls, code: types.CodeType, lineno: int, *key: Any) -> types.CodeType:
+    def lookup(
+        cls, code: types.CodeType, lineno: int, init_offset: int, *key: Any
+    ) -> types.CodeType:
         if code not in cls.cache:
             cls.cache[code] = {}
         key = tuple(key)
         if key not in cls.cache[code]:
-            cls.cache[code][key] = cls.generate(code, lineno, *key)
+            cls.cache[code][key] = cls.generate(code, lineno, init_offset, *key)
         return cls.cache[code][key]
 
     @classmethod
     def generate(
         cls,
         code: types.CodeType,
         lineno: int,
-        offset: int,
+        init_offset: int,
+        resume_offset: int,
         setup_fn_target_offsets: tuple[int, ...],  # only used in Python 3.11+
         nstack: int,
         argnames: tuple[str, ...],
@@ -317,7 +320,7 @@ def generate(
         # which prevents excessive recompilation of inner frames
         nested_code_objs: tuple[types.CodeType],
     ) -> types.CodeType:
-        assert offset is not None
+        assert resume_offset is not None
         assert not (
             code.co_flags
             & (CO_GENERATOR | CO_COROUTINE | CO_ITERABLE_COROUTINE | CO_ASYNC_GENERATOR)
@@ -327,7 +330,8 @@ def generate(
             return cls.generate_based_on_original_code_object(
                 code,
                 lineno,
-                offset,
+                init_offset,
+            
```

### `torch/_dynamo/symbolic_convert.py`
```diff
@@ -2479,7 +2479,9 @@ def store_attr_graph_break(self, inst: Instruction) -> None:
             reason=GraphCompileReason("store_attr", [self.frame_summary()]),
             stack_pops=2,
         )
-        self.output.add_output_instructions([copy.copy(inst)])
+        inst_copy = copy.copy(inst)
+        inst_copy.exn_tab_entry = None
+        self.output.add_output_instructions([inst_copy])
         self.popn(2)
         self.output.add_output_instructions(
             self.create_call_resume_at(
@@ -2679,14 +2681,16 @@ def create_call_resume_at(
             if sys.version_info < (3, 12):
                 assert len(argnames_null) == 0, "variables should not be NULL in < 3.12"
 
+            assert cur_tx.current_instruction.offset is not None
             # compile_subgraph did not codegen any NULLs,
             # so we should not count NullVariables
             stack_len = len(cur_tx.stack) - len(meta.stack_null_idxes)
 
             new_code: types.CodeType = ContinueExecutionCache.lookup(
                 cur_tx.f_code,
                 cur_tx.lineno,
-                resume_inst.offset,
+                cur_tx.current_instruction.offset,
+                resume_inst.offset,  # type: ignore[arg-type]
                 tuple(b.target.offset for b in cur_tx.block_stack),
                 stack_len,
                 argnames,
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `torch/_dynamo/resume_execution.py`
- `torch/_dynamo/symbolic_convert.py`
