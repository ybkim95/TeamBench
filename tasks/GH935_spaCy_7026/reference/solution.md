# Reference solution — GH935_spaCy_7026

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH935_spaCy_7026`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH935_spaCy_7026/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/cli/evaluate.py` (modified, +11/-5)
- `spacy/tests/regression/test_issue7019.py` (added, +12/-0)

## Diff Summary (What the Fix Changes)

### `spacy/cli/evaluate.py`
```diff
@@ -175,10 +175,13 @@ def render_parses(
 def print_prf_per_type(
     msg: Printer, scores: Dict[str, Dict[str, float]], name: str, type: str
 ) -> None:
-    data = [
-        (k, f"{v['p']*100:.2f}", f"{v['r']*100:.2f}", f"{v['f']*100:.2f}")
-        for k, v in scores.items()
-    ]
+    data = []
+    for key, value in scores.items():
+        row = [key]
+        for k in ("p", "r", "f"):
+            v = value[k]
+            row.append(f"{v * 100:.2f}" if isinstance(v, (int, float)) else v)
+        data.append(row)
     msg.table(
         data,
         header=("", "P", "R", "F"),
@@ -191,7 +194,10 @@ def print_textcats_auc_per_cat(
     msg: Printer, scores: Dict[str, Dict[str, float]]
 ) -> None:
     msg.table(
-        [(k, f"{v:.2f}") for k, v in scores.items()],
+        [
+            (k, f"{v:.2f}" if isinstance(v, (float, int)) else v)
+            for k, v in scores.items()
+        ],
         header=("", "ROC AUC"),
         aligns=("l", "r"),
         title="Textcat ROC AUC (per label)",
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/cli/evaluate.py`
