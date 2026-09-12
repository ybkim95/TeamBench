# Reference solution — GH968_pymc_7637

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH968_pymc_7637`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH968_pymc_7637/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.pre-commit-config.yaml` (modified, +10/-10)
- `pymc/sampling/mcmc.py` (modified, +2/-0)
- `pymc/sampling/parallel.py` (modified, +10/-6)
- `pymc/step_methods/compound.py` (modified, +7/-2)
- `pymc/step_methods/hmc/quadpotential.py` (modified, +11/-5)
- `pymc/step_methods/state.py` (modified, +7/-0)
- `pymc/util.py` (modified, +31/-1)
- `tests/logprob/test_transform_value.py` (modified, +2/-2)
- `tests/sampling/test_mcmc.py` (modified, +28/-25)
- `tests/sampling/test_parallel.py` (modified, +20/-0)
- `tests/step_methods/test_metropolis.py` (modified, +1/-4)

## Diff Summary (What the Fix Changes)

### `pymc/sampling/mcmc.py`
```diff
@@ -1068,7 +1068,9 @@ def _sample_many(
     step: function
         Step function
     """
+    initial_step_state = step.sampling_state
     for i in range(chains):
+        step.sampling_state = initial_step_state
         _sample(
             draws=draws,
             chain=i,
```

### `pymc/sampling/parallel.py`
```diff
@@ -33,7 +33,13 @@
 
 from pymc.blocking import DictToArrayBijection
 from pymc.exceptions import SamplingError
-from pymc.util import CustomProgress, default_progress_theme
+from pymc.util import (
+    CustomProgress,
+    RandomGeneratorState,
+    default_progress_theme,
+    get_state_from_generator,
+    random_generator_from_state,
+)
 
 logger = logging.getLogger(__name__)
 
@@ -96,13 +102,12 @@ def __init__(
         shared_point,
         draws: int,
         tune: int,
-        rng: np.random.Generator,
-        seed_seq: np.random.SeedSequence,
+        rng_state: RandomGeneratorState,
         blas_cores,
     ):
         # For some strange reason, spawn multiprocessing doesn't copy the rng
         # seed sequence, so we have to rebuild it from scratch
-        rng = np.random.Generator(type(rng.bit_generator)(seed_seq))
+        rng = random_generator_from_state(rng_state)
         self._msg_pipe = msg_pipe
         self._step_method = step_method
         self._step_method_is_pickled = step_method_is_pickled
@@ -263,8 +268,7 @@ def __init__(
                 self._shared_point,
                 draws,
                 tune,
-                rng,
-                rng.bit_generator.seed_seq,
+                get_state_from_generator(rng),
                 blas_cores,
             ),
         )
```

### `pymc/step_methods/compound.py`
```diff
@@ -31,7 +31,12 @@
 
 from pymc.blocking import PointType, StatDtype, StatsDict, StatShape, StatsType
 from pymc.model import modelcontext
-from pymc.step_methods.state import DataClassState, WithSamplingState, dataclass_state
+from pymc.step_methods.state import (
+    DataClassState,
+    RandomGeneratorState,
+    WithSamplingState,
+    dataclass_state,
+)
 from pymc.util import RandomGenerator, get_random_generator
 
 __all__ = ("Competence", "CompoundStep")
@@ -91,7 +96,7 @@ def infer_warn_stats_info(
 
 @dataclass_state
 class StepMethodState(DataClassState):
-    rng: np.random.Generator
+    rng: RandomGeneratorState
 
 
 class BlockedStep(ABC, WithSamplingState):
```

### `pymc/step_methods/hmc/quadpotential.py`
```diff
@@ -26,7 +26,12 @@
 from scipy.sparse import issparse
 
 from pymc.pytensorf import floatX
-from pymc.step_methods.state import DataClassState, WithSamplingState, dataclass_state
+from pymc.step_methods.state import (
+    DataClassState,
+    RandomGeneratorState,
+    WithSamplingState,
+    dataclass_state,
+)
 from pymc.util import RandomGenerator, get_random_generator
 
 __all__ = [
@@ -105,7 +110,7 @@ def __str__(self):
 
 @dataclass_state
 class PotentialState(DataClassState):
-    rng: np.random.Generator
+    rng: RandomGeneratorState
 
 
 class QuadPotential(WithSamplingState):
@@ -476,9 +481,8 @@ def current_mean(self, out=None):
 class QuadPotentialDiagAdaptExpState(QuadPotentialDiagAdaptState):
     _alpha: float
     _stop_adaptation: float
-    _variance_estimator: ExpWeightedVarianceState
-
-    _variance_estimator_grad: ExpWeightedVarianceState | None = None
+    _variance_estimator: ExpWeightedVarianceState | None
+    _variance_estimator_grad: ExpWeightedVarianceState | None
 
 
 class QuadPotentialDiagAdaptExp(QuadPotentialDiagAdapt):
@@ -524,6 +528,8 @@ def __init__(self, *args, alpha, use_grads=False, stop_adaptation=None, rng=None
         if stop_adaptation is None:
             stop_adaptation = np.inf
         self._stop_adaptation = stop_adaptation
+        self._variance_estimator = None
+        self._variance_estimator_grad = None
 
     def update(self, sample, grad, tune):
         if tune and self._n_samples < self._stop_adaptation:
```

### `pymc/step_methods/state.py`
```diff
@@ -17,6 +17,8 @@
 
 import numpy as np
 
+from pymc.util import RandomGeneratorState, get_state_from_generator, random_generator_from_state
+
 dataclass_state = dataclass(kw_only=True)
 
 
@@ -66,8 +68,11 @@ def sampling_state(self) -> DataClassState:
         kwargs = {}
         for field in fields(state_class):
             val = getattr(self, field.name)
+            _val: Any
             if isinstance(val, WithSamplingState):
                 _val = val.sampling_state
+            elif isinstance(val, np.random.Generator):
+                _val = get_state_from_generator(val)
             else:
                 _val = val
             kwargs[field.name] = deepcopy(_val)
@@ -81,6 +86,8 @@ def sampling_state(self, state: DataClassState):
         ), f"Encountered invalid state class '{state.__class__}'. State must be '{state_class}'"
         for field in fields(state_class):
             state_val = deepcopy(getattr(state, field.name))
+            if isinstance(state_val, RandomGeneratorState):
+                state_val = random_generator_from_state(state_val)
             self_val = getattr(self, field.name)
             is_frozen = field.metadata.get("frozen", False)
             if is_frozen:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pymc/sampling/mcmc.py`
- `pymc/sampling/parallel.py`
- `pymc/step_methods/compound.py`
- `pymc/step_methods/hmc/quadpotential.py`
- `pymc/step_methods/state.py`
