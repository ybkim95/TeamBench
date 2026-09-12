# Reference solution — GH1189_darts_2958

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1189_darts_2958`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1189_darts_2958/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `darts/models/forecasting/pl_forecasting_module.py` (modified, +17/-18)
- `darts/tests/models/forecasting/test_torch_forecasting_model.py` (modified, +16/-22)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/pl_forecasting_module.py`
```diff
@@ -85,7 +85,12 @@ def __init__(
         train_sample_shape: Optional[tuple] = None,
         loss_fn: nn.modules.loss._Loss = nn.MSELoss(),
         torch_metrics: Optional[
-            Union[torchmetrics.Metric, torchmetrics.MetricCollection]
+            Union[
+                torchmetrics.Metric,
+                torchmetrics.MetricCollection,
+                Sequence[Union[torchmetrics.Metric, torchmetrics.MetricCollection]],
+                dict[str, Union[torchmetrics.Metric, torchmetrics.MetricCollection]],
+            ]
         ] = None,
         likelihood: Optional[TorchLikelihood] = None,
         optimizer_cls: torch.optim.Optimizer = torch.optim.Adam,
@@ -130,8 +135,8 @@ def __init__(
             This parameter will be ignored for probabilistic models if the ``likelihood`` parameter is specified.
             Default: ``torch.nn.MSELoss()``.
         torch_metrics
-            A torch metric or a ``MetricCollection`` used for evaluation. A full list of available metrics can be found
-            at https://torchmetrics.readthedocs.io/en/latest/. Default: ``None``.
+            A ``torchmetric.Metric`` or a ``MetricCollection`` used for evaluation. A full list of available metrics
+            can be found `here <https://torchmetrics.readthedocs.io/en/latest/>`__. Default: ``None``.
         likelihood
             One of Darts' :meth:`Likelihood <darts.utils.likelihood_models.torch.TorchLikelihood>` models to be used for
             probabilistic forecasts. Default: ``None``.
@@ -799,20 +804,14 @@ def output_chunk_length(self) -> Optional[int]:
 
     @staticmethod
     def configure_torch_metrics(
-        torch_metrics: Union[torchmetrics.Metric, torchmetrics.MetricCollection],
+        torch_metrics: Union[
+            torchmetrics.Metric,
+            torchmetrics.MetricCollection,
+            Sequence[Union[torchmetrics.Metric, torchmetrics.MetricCollection]],
+            dict[str, Union[torchmetrics.Metric, torchmetrics.MetricCollecti
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/models/forecasting/pl_forecasting_module.py`
