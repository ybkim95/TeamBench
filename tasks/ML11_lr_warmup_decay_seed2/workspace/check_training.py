"""Validate training results and scheduler correctness."""
import json
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_scheduler():
    """Verify scheduler produces correct LR profile."""
    import torch
    import torch.optim as optim
    import torch.nn as nn
    from scheduler import WarmupCosineScheduler

    model = nn.Linear(4, 2)
    optimizer = optim.SGD(model.parameters(), lr=1e-3)
    base_lr = 1e-3
    warmup_steps = 10
    total_steps = 100
    scheduler = WarmupCosineScheduler(optimizer, base_lr, warmup_steps, total_steps)

    lrs = []
    for _ in range(total_steps):
        scheduler.step()
        lrs.append(scheduler.get_last_lr())

    # LR at step 1 should be near 0 (start of warmup)
    assert lrs[0] < base_lr * 0.5, f"LR at step 1 should be < 0.5*base_lr, got {lrs[0]:.6f}"

    # LR at end of warmup (step=warmup_steps) should be close to base_lr
    lr_at_warmup_end = lrs[warmup_steps - 1]
    assert lr_at_warmup_end > base_lr * 0.8,         f"LR at warmup end should be >= 0.8*base_lr={base_lr*0.8:.6f}, got {lr_at_warmup_end:.6f}"

    # LR should be monotonically decreasing after warmup
    post_warmup = lrs[warmup_steps:]
    is_decreasing = all(post_warmup[i] >= post_warmup[i+1] for i in range(len(post_warmup)-1))
    assert is_decreasing, "LR should be monotonically decreasing after warmup"

    # LR at end should be near 0
    assert lrs[-1] < base_lr * 0.1, f"LR at end should be near 0, got {lrs[-1]:.6f}"
    print("SCHEDULER_OK")
    return True


def check():
    # Check 1: training results exist
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    converged = res.get("converged", False)
    print(f"Final val acc: {acc:.4f}, converged: {converged}")

    if not converged:
        print("FAIL: Model did not converge")
        return False

    # Check 2: scheduler correctness
    try:
        check_scheduler()
    except AssertionError as e:
        print(f"FAIL: Scheduler bug not fixed: {e}")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
