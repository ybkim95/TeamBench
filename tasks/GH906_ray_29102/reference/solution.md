# Reference solution — GH906_ray_29102

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH906_ray_29102`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH906_ray_29102/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/tune/examples/pb2_example.py` (modified, +7/-1)
- `python/ray/tune/examples/pbt_function.py` (modified, +47/-13)
- `python/ray/tune/schedulers/pb2.py` (modified, +19/-3)
- `python/ray/tune/schedulers/pbt.py` (modified, +121/-30)
- `python/ray/tune/tests/test_trial_scheduler.py` (modified, +8/-2)
- `python/ray/tune/tests/test_trial_scheduler_pbt.py` (modified, +69/-8)

## Diff Summary (What the Fix Changes)

### `python/ray/tune/examples/pb2_example.py`
```diff
@@ -28,8 +28,10 @@
         else:
             ray.init()
 
+    perturbation_interval = 5
     pbt = PB2(
-        perturbation_interval=20,
+        time_attr="training_iteration",
+        perturbation_interval=perturbation_interval,
         hyperparam_bounds={
             # hyperparameter bounds.
             "lr": [0.0001, 0.02],
@@ -59,6 +61,10 @@
             # note: this parameter is perturbed but has no effect on
             # the model training in this example
             "some_other_factor": 1,
+            # This parameter is not perturbed and is used to determine
+            # checkpoint frequency. We set checkpoints and perturbations
+            # to happen at the same frequency.
+            "checkpoint_interval": perturbation_interval,
         },
     )
     results = tuner.fit()
```

### `python/ray/tune/examples/pbt_function.py`
```diff
@@ -33,21 +33,29 @@ def pbt_function(config):
     faster convergence. Training will not converge without PBT.
     """
     lr = config["lr"]
+    checkpoint_interval = config.get("checkpoint_interval", 1)
+
     accuracy = 0.0  # end = 1000
-    start = 0
+
+    # NOTE: See below why step is initialized to 1
+    step = 1
     if session.get_checkpoint():
         state = session.get_checkpoint().to_dict()
         accuracy = state["acc"]
-        start = state["step"]
+        last_step = state["step"]
+        # Current step should be 1 more than the last checkpoint step
+        step = last_step + 1
 
-    midpoint = 100  # lr starts decreasing after acc > midpoint
-    q_tolerance = 3  # penalize exceeding lr by more than this multiple
-    noise_level = 2  # add gaussian noise to the acc increase
     # triangle wave:
     #  - start at 0.001 @ t=0,
     #  - peak at 0.01 @ t=midpoint,
     #  - end at 0.001 @ t=midpoint * 2,
-    for step in range(start, 100):
+    midpoint = 100  # lr starts decreasing after acc > midpoint
+    q_tolerance = 3  # penalize exceeding lr by more than this multiple
+    noise_level = 2  # add gaussian noise to the acc increase
+
+    # Let `stop={"done": True}` in the configs below handle trial stopping
+    while True:
         if accuracy < midpoint:
             optimal_lr = 0.01 * accuracy / midpoint
         else:
@@ -64,8 +72,14 @@ def pbt_function(config):
         accuracy = max(0, accuracy)
 
         checkpoint = None
-        if step % 3 == 0:
-            checkpoint = Checkpoint.from_dict({"acc": accuracy, "step": start})
+        if step % checkpoint_interval == 0:
+            # Checkpoint every `checkpoint_interval` steps
+            # NOTE: if we initialized `step=0` above, our checkpointing and perturbing
+            # would be out of sync by 1 step.
+            # Ex: if `checkpoint_interval` = `perturbation_interval` = 3
+            # step:                0 (checkpoint)  1     2            3 (checkpoint)
+
```

### `python/ray/tune/schedulers/pb2.py`
```diff
@@ -1,11 +1,12 @@
-from typing import Dict, Optional
+from typing import Dict, Optional, Tuple
 from copy import deepcopy
 import logging
 import numpy as np
 import pandas as pd
 
 from ray.tune import TuneError
 from ray.tune.schedulers import PopulationBasedTraining
+from ray.tune.experiment import Trial
 
 
 def import_pb2_dependencies():
@@ -368,7 +369,22 @@ def _save_trial_state(self, state, time, result, trial):
         self.data = pd.concat([self.data, entry]).reset_index(drop=True)
         self.data.Trial = self.data.Trial.astype("str")
 
-    def _get_new_config(self, trial, trial_to_clone):
+    def _get_new_config(self, trial: Trial, trial_to_clone: Trial) -> Tuple[Dict, Dict]:
+        """Gets new config for trial by exploring trial_to_clone's config using
+        Bayesian Optimization (BO) to choose the hyperparameter values to explore.
+
+        Overrides `PopulationBasedTraining._get_new_config`.
+
+        Args:
+            trial: The current trial that decided to exploit trial_to_clone.
+            trial_to_clone: The top-performing trial with a hyperparameter config
+                that the current trial will explore.
+
+        Returns:
+            new_config: New hyperparameter configuration (after BO).
+            operations: Empty dict since PB2 doesn't explore in easily labeled ways
+                like PBT does.
+        """
         # If we are at a new timestep, we dont want to penalise for trials
         # still going.
         if self.data["Time"].max() > self.last_exploration_time:
@@ -400,4 +416,4 @@ def _get_new_config(self, trial, trial_to_clone):
             self.current = np.concatenate((self.current, new), axis=0)
             logger.debug(self.current)
 
-        return new_config
+        return new_config, {}
```

### `python/ray/tune/schedulers/pbt.py`
```diff
@@ -63,12 +63,13 @@ def _explore(
             particular variable.
         perturbation_factors: Scaling factors to choose between when mutating
             a continuous hyperparameter.
-        custom_explore_fn: Custom explore fn applied after built-in
-            config perturbations are.
+        custom_explore_fn: Custom explore function applied after built-in
+            config perturbations.
 
     Returns:
         new_config: New hyperparameter configuration (after random mutations).
-        operations: Map of hyperparam -> string describing mutation operation performed
+        operations: Map of hyperparams -> strings describing mutation operations
+            performed
     """
     operations = {}
     new_config = copy.deepcopy(config)
@@ -167,6 +168,49 @@ def _fill_config(
             _fill_config(config[attr], k, v)
 
 
+def _filter_mutated_params_from_config(
+    config: Dict, hyperparam_mutations: Dict
+) -> Dict:
+    """Filter out hyperparameters from a config so that only parameters specified
+    within hyperparam_mutations remain. This recursively filters nested configs.
+
+    Example:
+    >>> config = {
+    ...     "a": {"b": 2, "c": 0, "d": {"e": 0.1}},
+    ...     "f": {"g": 0.5},
+    ... }
+    >>> hyperparam_mutations = {
+    ...     "a": {"b": [1, 2], "c": [-1, 0]},
+    ... }
+    >>> _filter_mutated_params_from_config(config, hyperparam_mutations) == {
+    ...     "a": {"b": 2, "c": 0}
+    ... }
+    True
+
+    Args:
+        config: The config dict that we want to filter.
+        hyperparam_mutations: A dict containing a subset of hyperparameters from
+            config, used to filter the config.
+
+    Returns:
+        mutated_params: A copy of config containing only params specified in
+            hyperparam_mutations
+    """
+    mutated_params = {}
+    for param_name in config:
+        if param_name not in hyperparam_mutations:
+            continue
+
+        if isinstance(config[param_name], dict):
+   
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `python/ray/tune/examples/pb2_example.py`
- `python/ray/tune/examples/pbt_function.py`
- `python/ray/tune/schedulers/pb2.py`
- `python/ray/tune/schedulers/pbt.py`
