# Reference solution — GH1089_pytorch_lightni_8421

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1089_pytorch_lightni_8421`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1089_pytorch_lightni_8421/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +1/-0)
- `pytorch_lightning/utilities/enums.py` (modified, +1/-1)
- `tests/utilities/test_enums.py` (added, +11/-0)

## Diff Summary (What the Fix Changes)

### `pytorch_lightning/utilities/enums.py`
```diff
@@ -34,7 +34,7 @@ def __eq__(self, other: Union[str, Enum]) -> bool:
     def __hash__(self) -> int:
         # re-enable hashtable so it can be used as a dict key or in a set
         # example: set(LightningEnum)
-        return hash(self.name)
+        return hash(self.value.lower())
 
 
 class AMPType(LightningEnum):
```

## Moved from `brief.md`

## Files That May Need Changes

- `pytorch_lightning/utilities/enums.py`
