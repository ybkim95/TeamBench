# Reference solution — GH866_pandas_64569

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH866_pandas_64569`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH866_pandas_64569/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/io/pytables.py` (modified, +68/-64)
- `pandas/tests/io/pytables/test_put.py` (modified, +12/-0)

## Diff Summary (What the Fix Changes)

### `pandas/io/pytables.py`
```diff
@@ -3279,10 +3279,6 @@ def write_array_empty(self, key: str, value: ArrayLike) -> None:
     def write_array(
         self, key: str, obj: AnyArrayLike, items: Index | None = None
     ) -> None:
-        # TODO: we only have a few tests that get here, the only EA
-        #  that gets passed is DatetimeArray, and we never have
-        #  both self._filters and EA
-
         value = extract_array(obj, extract_numpy=True)
 
         if key in self.group:
@@ -3303,71 +3299,79 @@ def write_array(
                 value = value.T
                 transposed = True
 
-        atom = None
-        if self._filters is not None:
-            with suppress(ValueError):
-                # get the atom for this datatype
-                atom = _tables().Atom.from_dtype(value.dtype)
-
-        if atom is not None:
-            # We only get here if self._filters is non-None and
-            #  the Atom.from_dtype call succeeded
-
-            # create an empty chunked array and fill it from value
-            if not empty_array:
-                ca = self._handle.create_carray(
-                    self.group, key, atom, value.shape, filters=self._filters
-                )
-                ca[:] = value
-
-            else:
-                self.write_array_empty(key, value)
-
-        elif value.dtype.type == np.object_:
-            # infer the type, warn if we have a non-string type here (for
-            # performance)
-            inferred_type = lib.infer_dtype(value, skipna=False)
-            if empty_array:
-                pass
-            elif inferred_type == "string":
-                pass
-            elif _global_config["mode"]["performance_warnings"]:
-                ws = performance_doc % (inferred_type, key, items)
-                warnings.warn(ws, PerformanceWarning, stacklevel=find_stack_level())
-
-            vlarr = self._handle.create_vlarray(self.group, key, _tables().ObjectAtom())
-            vlarr.append(value)
-
-        elif lib.is_np_dtype(v
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/io/pytables.py`
