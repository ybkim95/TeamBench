# Reference solution — GH1056_ray_46321

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1056_ray_46321`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1056_ray_46321/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `rllib/algorithms/tests/test_callbacks_on_env_runner.py` (modified, +0/-3)
- `rllib/env/single_agent_env_runner.py` (modified, +10/-12)

## Diff Summary (What the Fix Changes)

### `rllib/env/single_agent_env_runner.py`
```diff
@@ -197,19 +197,17 @@ def sample(
                     explore=explore,
                     random_actions=random_actions,
                 )
-            # For complete episodes mode, sample as long as the number of timesteps
-            # done is smaller than the `train_batch_size`.
+            # For complete episodes mode, sample a single episode and
+            # leave coordination of sampling to `synchronous_parallel_sample`.
+            # TODO (simon, sven): The coordination will eventually move
+            # to `EnvRunnerGroup` in the future. So from the algorithm one
+            # would do `EnvRunnerGroup.sample()`.
             else:
-                total = 0
-                samples = []
-                while total < self.config.train_batch_size:
-                    episodes = self._sample_episodes(
-                        num_episodes=self.num_envs,
-                        explore=explore,
-                        random_actions=random_actions,
-                    )
-                    total += sum(len(e) for e in episodes)
-                    samples.extend(episodes)
+                samples = self._sample_episodes(
+                    num_episodes=1,
+                    explore=explore,
+                    random_actions=random_actions,
+                )
 
             # Make the `on_sample_end` callback.
             self._callbacks.on_sample_end(
```

## Moved from `brief.md`

## Files That May Need Changes

- `rllib/env/single_agent_env_runner.py`
