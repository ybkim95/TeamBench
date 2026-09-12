# Reference solution — GH1040_darts_2957

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1040_darts_2957`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1040_darts_2957/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `darts/explainability/tft_explainer.py` (modified, +13/-0)
- `darts/tests/explainability/test_tft_explainer.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `darts/explainability/tft_explainer.py`
```diff
@@ -36,6 +36,7 @@
 from darts.explainability.explainability import _ForecastingModelExplainer
 from darts.logging import get_logger, raise_log
 from darts.models import TFTModel
+from darts.utils.ts_utils import SeriesType, get_series_seq_type
 from darts.utils.utils import generate_index
 
 logger = get_logger(__name__)
@@ -192,6 +193,18 @@ def explain(
             foreground_past_covariates,
             foreground_future_covariates,
         )
+        if (
+            get_series_seq_type(foreground_series) is SeriesType.SEQ
+            and len(foreground_series) > self.model.batch_size
+        ):
+            raise_log(
+                ValueError(
+                    f"The number of back- or foreground series to explain ({len(foreground_series)}) "
+                    f"must be smaller than or equal to the model's batch size ({self.model.batch_size})."
+                ),
+                logger=logger,
+            )
+
         horizons, _ = self._process_horizons_and_targets(None, None)
         preds = self.model.predict(
             n=self.n,
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/explainability/tft_explainer.py`
