# ML43: RL Reward Shaping Bug (Brief)

## Your Task
Fix the reward shaping in `env.py`.

Training a DQN on a **continuous 2D reaching environment** fails because the reward shaping
violates the potential-based theorem — the agent learns to orbit the goal
instead of reaching it.

## Symptoms
- Agent circles near the goal but rarely terminates
- Success rate stays near 0 despite decreasing shaped loss
- High shaped reward doesn't correlate with actual goal-reaching

## What to Fix
- `env.py`: `ShapedEnv.step()` — the shaping bonus must use `gamma * phi(s') - phi(s)`
- Do NOT modify `train.py` or `agent.py`

## Success Criteria
- `python check_agent.py` exits 0
- Success rate > 0.4 on unmodified environment
