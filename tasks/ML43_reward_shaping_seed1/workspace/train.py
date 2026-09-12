"""Train DQN on shaped navigation environment."""
import json
import sys
import os
import numpy as np
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import GridEnv, ShapedEnv
from agent import DQNAgent


def evaluate(agent, env_base, n_eval: int = 50) -> float:
    """Evaluate agent success rate on unshaped environment."""
    successes = 0
    for ep in range(n_eval):
        obs = env_base.reset()
        for _ in range(env_base.max_steps):
            action = agent.select_action(obs)
            obs, reward, done, truncated, info = env_base.step(action)
            if done and not truncated:
                successes += 1
                break
            if done or truncated:
                break
    return successes / n_eval


def train():
    np.random.seed(42)
    torch.manual_seed(42)

    env_base = GridEnv(grid_size=10, seed=0)
    env = ShapedEnv(env_base)
    agent = DQNAgent(gamma=0.95)

    history = []
    sync_every = 20

    for ep in range(868):
        obs = env.reset()
        ep_reward = 0.0
        for _ in range(env_base.max_steps):
            action = agent.select_action(obs)
            next_obs, reward, done, truncated, info = env.step(action)
            agent.store(obs, action, reward, next_obs, float(done and not truncated))
            agent.update()
            obs = next_obs
            ep_reward += reward
            if done or truncated:
                break

        if (ep + 1) % sync_every == 0:
            agent.sync_target()

        if (ep + 1) % 100 == 0:
            success_rate = evaluate(agent, env_base)
            history.append({"episode": ep + 1, "success_rate": success_rate})
            print(f"Ep {ep+1}/{868} | success_rate={success_rate:.3f}")

    final_success = evaluate(agent, env_base, n_eval=100)
    results = {
        "final_success_rate": final_success,
        "converged": final_success > 0.4,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final success rate: {final_success:.3f}")
    return results


if __name__ == "__main__":
    train()
