# Reference solution — GH996_transformers_34531

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH996_transformers_34531`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH996_transformers_34531/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/transformers/tokenization_utils_base.py` (modified, +1/-1)
- `tests/models/layoutlmv2/test_tokenization_layoutlmv2.py` (modified, +4/-0)
- `tests/models/layoutlmv3/test_tokenization_layoutlmv3.py` (modified, +4/-0)
- `tests/models/layoutxlm/test_tokenization_layoutxlm.py` (modified, +4/-0)
- `tests/models/markuplm/test_tokenization_markuplm.py` (modified, +4/-0)
- `tests/models/tapas/test_tokenization_tapas.py` (modified, +4/-0)
- `tests/models/udop/test_tokenization_udop.py` (modified, +4/-0)
- `tests/test_tokenization_common.py` (modified, +104/-0)

## Diff Summary (What the Fix Changes)

### `src/transformers/tokenization_utils_base.py`
```diff
@@ -1722,7 +1722,7 @@ def apply_chat_template(
                             if start_token is None:
                                 # start_token is out of bounds maybe due to truncation.
                                 break
-                            for token_id in range(start_token, end_token + 1 if end_token else len(input_ids)):
+                            for token_id in range(start_token, end_token + 1 if end_token else len(input_ids[i])):
                                 current_mask[token_id] = 1
                         assistant_masks.append(current_mask)
                     out["assistant_masks"] = assistant_masks if is_batched else assistant_masks[0]
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/transformers/tokenization_utils_base.py`
