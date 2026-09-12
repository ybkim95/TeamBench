# GH1056_ray_46321: [RLlib] Moving sampling coordination for `batch_mode=complete_episodes` to `synchronous_parallel_sample`. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ray-project/ray/issues/45826
- Repo: https://github.com/ray-project/ray

## Issue Description

### What happened + What you expected to happen

Ray throws an exception if the environment takes to long to perform a step: 

No samples returned from remote workers. If you have a slow environment or model, consider increasing the `sample_timeout_s` or decreasing the `rollout_fragment_length` in `AlgorithmConfig.env_runners().

This happens both if `enable_rl_module_and_learner` is True or False, and for `batch_mode` complete_episodes and truncate_episodes. **Ideally, I want to use `complete_episodes` for training!**

I added a short example below, using `time.sleep(1)` for simplicity instead of the real computations my environment performs. Setting the `sample_timeout_s` does not seem to affect this problem. Removing the costly computation works but is obviously not an option.

### Versions / Dependencies

python: 3.11.9
ray: 2.23.0

### Reproduction script

```python

from ray.rllib.algorithms import PPOConfig
from gymnasium import spaces
import numpy as np
import gymnasium as gym

class FakeEnv(gym.Env):
    action_space = spaces.Discrete(2)
    observation_space = spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
    counter = 0

    def __init__(self, *args, **kwargs):
        pass

    def step(
            self, action
    ):
        time.sleep(1) # or any other computation that takes a "long" time

        terminated = self.counter > 10

        if action == 0:
            return self.observation_space.sample(), 1, False, terminated, {}
        if action == 1:
            return self.observation_space.sample(), -1, True, terminated, {}

    def reset(
            self, *, seed=None, options=None,
    ):
        self.counter = 0
        return self.observation_space.sample(), {}

algo = (
    PPOConfig()
    .api_stack(enable_rl_module_and_learner=True)
    .environment(FakeEnv)
    .framework("torch")
    .env_runners(num_env_runners=1, num_envs_per_env_runner=1, batch_mode="complete_episodes", sample_timeout_s=3600)
).build()

algo.train()
```

### Issue Severity

High: It blocks me from completing my task.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I am also facing the same issue.

### Comment 2 ([user]):

Try running with 

```
.api_stack(
    enable_rl_module_and_learner=True,
    enable_env_runner_and_connector_v2=True
)
```

and

```
.env_runners(
    sample_timeout_s=None
)
```

I could not get it to work with evaluation.

### Comment 3 ([user]):

[user] Thanks for raising this issue. This led us find a bug in our sampling logic which is fixed in the related PR and should go in the next days into master. 

The configuration posted by [user] is the intended config to activate the new API stack and avoid the error referred to here.

## PR Review Comments

**[user]** on `rllib/env/single_agent_env_runner.py`:

I very much like this!

Can we add a small TODO comment here that this logic, currently handled by `synchronous_parallel_sample` will eventually be moved fully into `EnvRunnerGroup`? So from the algo, you would do:
```
if self.config.batch_mode == "complete_episodes"
    self.env_runner_group.sample(num_timesteps=[batch size], complete_episodes=True)
```

something like this ^. Don't have to do this in this PR!

**[user]** on `rllib/env/single_agent_env_runner.py`:

Awesome. I would love this move!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
