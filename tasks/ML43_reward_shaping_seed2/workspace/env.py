"""RL environment with reward shaping — contains non-potential bonus bug."""
import numpy as np


class GridEnv:
    """Simple maze navigation environment with sparse rewards."""

    def __init__(self, grid_size: int = 6, seed: int = 0):
        self.grid_size = grid_size
        self.rng = np.random.RandomState(seed)
        self.goal = np.array([grid_size - 1, grid_size - 1], dtype=np.float32)
        self.max_steps = grid_size * grid_size * 2
        self.reset()

    def reset(self):
        self.pos = np.array([0.0, 0.0], dtype=np.float32)
        self.steps = 0
        return self._obs()

    def _obs(self):
        # Observation: [pos_x, pos_y] normalized
        return self.pos / self.grid_size

    def step(self, action: int):
        # Actions: 0=up, 1=down, 2=left, 3=right
        moves = np.array([[0, 1], [0, -1], [-1, 0], [1, 0]], dtype=np.float32)
        self.pos = np.clip(self.pos + moves[action], 0, self.grid_size - 1)
        self.steps += 1

        dist = np.linalg.norm(self.pos - self.goal)
        done = dist < 0.5 or self.steps >= self.max_steps
        reward = 1.0 if dist < 0.5 else 0.0
        truncated = self.steps >= self.max_steps and dist >= 0.5
        return self._obs(), reward, done, truncated, {"dist": dist}


class ShapedEnv:
    """Reward-shaped wrapper.

    BUG: The shaping bonus is NOT a valid potential-based shaping.
    A valid shaping requires: F(s,a,s') = gamma * Phi(s') - Phi(s)
    for some potential function Phi.

    The current bonus = alpha * (prev_dist - curr_dist) looks like
    potential shaping with Phi(s) = -alpha * dist(s) BUT the alpha
    factor is applied without the gamma discount, making it:
      bonus = alpha*Phi(s') - alpha*Phi(s) != gamma*Phi(s') - Phi(s)
    when gamma != 1.0.

    Additionally, the bonus accumulates without the terminal correction,
    so the agent learns to orbit the goal collecting shaping bonuses
    without actually terminating (the terminal state has no bonus).

    Correct fix: use bonus = gamma * phi(next_obs) - phi(curr_obs)
    where phi(obs) = -dist(obs * grid_size, goal) / grid_size
    """

    def __init__(self, env: GridEnv, alpha: float = 2.0, gamma: float = 0.95):
        self.env = env
        self.alpha = alpha
        self.gamma = gamma
        self._prev_dist = None

    def reset(self):
        obs = self.env.reset()
        # Distance in normalized coordinates
        self._prev_dist = np.linalg.norm(obs - self.env.goal / self.env.grid_size)
        return obs

    def step(self, action: int):
        obs, reward, done, truncated, info = self.env.step(action)
        curr_dist = np.linalg.norm(obs - self.env.goal / self.env.grid_size)

        # BUG: Missing gamma factor — this is NOT valid potential-based shaping
        # alpha*(prev - curr) != gamma*(-curr) - (-prev) when gamma != 1
        # This creates an orbiting incentive: agent can get bonuses indefinitely
        bonus = self.alpha * (self._prev_dist - curr_dist)
        # CORRECT would be:
        # phi_curr = -curr_dist
        # phi_prev = -self._prev_dist
        # bonus = self.gamma * phi_curr - phi_prev

        self._prev_dist = curr_dist
        shaped_reward = reward + bonus
        return obs, shaped_reward, done, truncated, info

    @property
    def goal(self):
        return self.env.goal

    @property
    def grid_size(self):
        return self.env.grid_size
