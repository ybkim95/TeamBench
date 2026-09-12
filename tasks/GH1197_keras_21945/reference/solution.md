# Reference solution — GH1197_keras_21945

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1197_keras_21945`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1197_keras_21945/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/layers/rnn/gru_test.py` (modified, +24/-0)
- `keras/src/layers/rnn/rnn.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `keras/src/layers/rnn/rnn.py`
```diff
@@ -387,7 +387,7 @@ def call(
                     batch_size=ops.shape(sequences)[0]
                 )
         if self.stateful:
-            actual_batch_size = ops.shape(sequences)[0]
+            actual_batch_size = sequences.shape[0]
             if (
                 self._expected_batch_size is not None
                 and actual_batch_size is not None
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/layers/rnn/rnn.py`
