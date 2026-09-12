# Reference solution — GH1204_evaluate_230

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1204_evaluate_230`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1204_evaluate_230/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/evaluate/module.py` (modified, +1/-1)
- `tests/test_metric.py` (modified, +10/-0)

## Diff Summary (What the Fix Changes)

### `src/evaluate/module.py`
```diff
@@ -559,7 +559,7 @@ def _infer_feature_from_example(self, example):
                     self._enforce_nested_string_type(features, example)
                     features.encode_example(example)
                     return features
-                except ValueError:
+                except (ValueError, TypeError):
                     continue
         feature_strings = "\n".join([f"Feature option {i}: {feature}" for i, feature in enumerate(self.features)])
         error_msg = (
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/evaluate/module.py`
