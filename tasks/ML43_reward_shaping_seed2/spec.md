# ML43: RL Reward Shaping Violates Potential Theorem

## Goal
Fix `env.py` so the reward shaping is valid potential-based shaping.
Run `python train.py` then `python check_agent.py` — both must pass.

## Task
Training a DQN agent on a **maze navigation environment** using reward shaping.
The agent must achieve >0.4 success rate on the unmodified sparse-reward environment.

---

## The Bug: Non-Potential Reward Shaping

**Location**: `env.py` `ShapedEnv.step()` — the shaping bonus computation

### Background: Potential-Based Shaping (Ng et al. 1999)

The only reward shaping that guarantees preservation of the optimal policy is:

```
F(s, a, s') = gamma * Phi(s') - Phi(s)
```

for some potential function `Phi: S -> R`. This form **telescopes** across trajectories,
so the total shaped return equals the original return plus a bounded constant.

### Current (Buggy) Code

```python
# BUG: Missing gamma factor — not valid potential-based shaping
bonus = self.alpha * (self._prev_dist - curr_dist)
# This equals alpha*(-curr_dist) - alpha*(-prev_dist)
# = alpha*Phi(s') - alpha*Phi(s)  where Phi(s) = -dist(s)
# But valid shaping requires: gamma*Phi(s') - Phi(s)
# When alpha != 1 and gamma != 1, these are different!
```

With `alpha=2.0` and `gamma=0.95`, the bug means:
- The agent receives `2.0x` the intended shaping signal
- The shaping does NOT telescope, so the agent can collect net positive bonus
  by orbiting around the goal without ever terminating
- The optimal policy under the shaped reward is to orbit, not reach the goal

### Correct Fix

```python
# Valid potential-based shaping: F(s,a,s') = gamma * Phi(s') - Phi(s)
phi_curr = -curr_dist    # Phi(s') = -dist(s', goal)
phi_prev = -self._prev_dist  # Phi(s) = -dist(s, goal)
bonus = self.gamma * phi_curr - phi_prev
```

This satisfies the potential theorem and does NOT create orbiting incentives.

---

## Training Config
- Episodes: 828, gamma: 0.95
- Shaping alpha: 2.0 (used in buggy version only)

## Deliverables
1. Fixed `env.py` with correct potential-based shaping
2. `training_results.json` after running `python train.py`
3. `python check_agent.py` exits 0
