"""Validate replay buffer FIFO fix."""
import json
import sys
import os
import torch
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_buffer import ReplayBuffer


def check_reservoir_sampling():
    """Verify buffer uses reservoir sampling (uniform distribution across tasks)."""
    np.random.seed(0)
    buffer = ReplayBuffer(capacity=150)
    input_dim = 16

    # Add 4x capacity worth of data in sequential "tasks"
    n_per_task = 150
    for task_id in range(4):
        x = torch.ones(n_per_task, input_dim) * task_id  # distinct per task
        y = torch.full((n_per_task,), task_id, dtype=torch.long)
        buffer.add(x, y)

    # Sample and check distribution across tasks
    xs, ys = buffer.sample(len(buffer))
    if ys is None:
        return False, "Buffer empty after adding data"

    task_counts = {t: (ys == t).sum().item() for t in range(4)}
    total = sum(task_counts.values())

    # With FIFO: only the last task should be in buffer (most recent evicts oldest)
    # With reservoir: roughly equal distribution
    last_task_frac = task_counts.get(4 - 1, 0) / total
    if last_task_frac > 0.8:
        return False, (
            f"FIFO bias detected: last task has {last_task_frac:.1%} of buffer. "
            f"Distribution: {task_counts}. Reservoir sampling should give ~{1/4:.1%} each."
        )
    return True, f"Buffer distribution across tasks: {task_counts}"


def check_early_tasks_retained():
    """Verify task 0 samples survive after adding later tasks."""
    np.random.seed(1)
    buffer = ReplayBuffer(capacity=150)
    input_dim = 16

    # Add task 0
    x0 = torch.zeros(100, input_dim)  # task 0: all zeros
    y0 = torch.zeros(100, dtype=torch.long)
    buffer.add(x0, y0)

    # Fill with tasks 1 to N-1 (many more samples)
    for task_id in range(1, 4):
        x = torch.ones(500, input_dim) * (task_id + 1)
        y = torch.full((500,), task_id, dtype=torch.long)
        buffer.add(x, y)

    xs, ys = buffer.sample(len(buffer))
    task0_count = (ys == 0).sum().item()
    if task0_count == 0:
        return False, "Task 0 samples completely evicted from buffer (FIFO bias)"
    task0_frac = task0_count / len(ys)
    if task0_frac < 0.02:
        return False, f"Task 0 has only {task0_frac:.1%} of buffer — nearly evicted by FIFO"
    return True, f"Task 0 retained: {task0_count}/{len(ys)} = {task0_frac:.1%}"


def check_reservoir_n_seen():
    """Verify n_seen is tracked correctly for reservoir sampling probability."""
    buffer = ReplayBuffer(capacity=150)
    n_added = 300
    x = torch.randn(n_added, 16)
    y = torch.zeros(n_added, dtype=torch.long)
    buffer.add(x, y)
    if buffer.n_seen != n_added:
        return False, f"n_seen={buffer.n_seen} != n_added={n_added}"
    return True, f"n_seen tracked correctly: {buffer.n_seen}"


def check_buffer_respects_capacity():
    """Verify buffer does not exceed capacity."""
    buffer = ReplayBuffer(capacity=150)
    for _ in range(5):
        x = torch.randn(200, 16)
        y = torch.zeros(200, dtype=torch.long)
        buffer.add(x, y)
    if len(buffer) > 150:
        return False, f"Buffer size {len(buffer)} exceeds capacity 150"
    return True, f"Buffer capacity respected: {len(buffer)} <= 150"


def check_sample_returns_correct_shape():
    """Verify sample() returns tensors of correct shape."""
    buffer = ReplayBuffer(capacity=150)
    x = torch.randn(100, 16)
    y = torch.randint(0, 5, (100,))
    buffer.add(x, y)
    xs, ys = buffer.sample(32)
    if xs is None:
        return False, "sample() returned None"
    if xs.shape != (32, 16):
        return False, f"Sample x shape {xs.shape} != (32, 16)"
    if ys.shape != (32,):
        return False, f"Sample y shape {ys.shape} != (32,)"
    return True, f"Sample shapes correct: x={xs.shape}, y={ys.shape}"


def check_uniform_distribution():
    """Statistical test: verify distribution is approximately uniform."""
    np.random.seed(42)
    buffer = ReplayBuffer(capacity=150)
    n_tasks = 4

    # Add equal amounts from each task
    per_task = 150 * 2  # 2x capacity to force eviction
    for t in range(n_tasks):
        x = torch.full((per_task, 16), float(t))
        y = torch.full((per_task,), t, dtype=torch.long)
        buffer.add(x, y)

    xs, ys = buffer.sample(len(buffer))
    counts = {t: (ys == t).sum().item() for t in range(n_tasks)}
    expected = len(buffer) / n_tasks
    max_deviation = max(abs(counts[t] - expected) / expected for t in range(n_tasks))

    if max_deviation > 0.5:  # more than 50% deviation from uniform
        return False, (
            f"Distribution not uniform (max deviation {max_deviation:.1%}): {counts}. "
            f"Expected ~{expected:.0f} each."
        )
    return True, f"Approximately uniform distribution: {counts} (max dev {max_deviation:.1%})"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    forgetting = res.get("forgetting", 1.0)
    task0_final = res.get("task0_final_acc", 0)
    if not res.get("converged", False):
        return False, (
            f"Continual learning did not converge: "
            f"forgetting={forgetting:.3f} (>0.3) or task0_final={task0_final:.3f} (<0.3)"
        )
    return True, f"Converged: forgetting={forgetting:.3f}, task0_final={task0_final:.3f}"


def check():
    checks = [
        ("Reservoir sampling (no FIFO bias)", check_reservoir_sampling),
        ("Early tasks retained", check_early_tasks_retained),
        ("n_seen tracked", check_reservoir_n_seen),
        ("Capacity respected", check_buffer_respects_capacity),
        ("Sample shape", check_sample_returns_correct_shape),
        ("Uniform distribution", check_uniform_distribution),
        ("Training results", check_training_results),
    ]

    all_pass = True
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"Exception: {e}"
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    print("\nPASS" if all_pass else "\nFAIL")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
