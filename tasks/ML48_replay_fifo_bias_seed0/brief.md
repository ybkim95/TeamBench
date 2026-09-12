# ML48: Replay Buffer FIFO Bias Bug (Brief)

## Your Task
Fix the replay buffer in `replay_buffer.py` to use reservoir sampling.

Training a **sequential task continual learning** with experience replay still shows
catastrophic forgetting because the buffer uses FIFO eviction — early
task samples are evicted first, leaving only recent-task data in the buffer.

## Symptoms
- Task 0 accuracy drops to near-chance after training on tasks 1-4
- Replay buffer contains only samples from the most recent task(s)
- Forgetting metric exceeds 0.3

## What to Fix
- `replay_buffer.py`: replace deque FIFO with reservoir sampling
- Keep `capacity`, `sample()`, and `n_seen` interface unchanged
- Do NOT modify `train.py` or `model.py`

## Success Criteria
- `python check_continual.py` exits 0
- Task 0 forgetting < 0.3
