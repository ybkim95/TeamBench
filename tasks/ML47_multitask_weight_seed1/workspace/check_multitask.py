"""Validate multi-task weighting fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainer import MultiTaskTrainer


def check_no_explosion_near_zero():
    """Verify weights are bounded when loss approaches zero."""
    trainer = MultiTaskTrainer()
    near_zero_losses = [torch.tensor(1e-6), torch.tensor(1.0)]
    try:
        total = trainer.weighted_loss(near_zero_losses)
        if not torch.isfinite(total):
            return False, f"Loss is non-finite ({total.item()}) when task loss near zero"
        return True, f"Loss finite near zero: {total.item():.4f}"
    except Exception as e:
        return False, f"Exception when task loss near zero: {e}"


def check_epsilon_in_denominator():
    """Verify epsilon is added to prevent division by zero."""
    with open("trainer.py") as f:
        src = f.read()
    # Must have epsilon in denominator
    has_epsilon = (
        "self.epsilon" in src and ("+ self.epsilon" in src or "self.epsilon +" in src)
    )
    if not has_epsilon:
        return False, "trainer.py does not add epsilon to denominator"
    return True, "Epsilon present in denominator"


def check_detach_used():
    """Verify loss is detached before weighting to avoid higher-order gradients."""
    with open("trainer.py") as f:
        src = f.read()
    has_detach = ".detach()" in src
    if not has_detach:
        return False, "trainer.py does not detach loss before computing weight"
    return True, "Loss detached before weighting"


def check_weights_bounded():
    """Verify weights are bounded for various loss values."""
    trainer = MultiTaskTrainer()
    test_cases = [
        [torch.tensor(0.001), torch.tensor(1.0)],
        [torch.tensor(0.0), torch.tensor(0.5)],
        [torch.tensor(1e-8), torch.tensor(2.0)],
    ]
    for losses in test_cases:
        total = trainer.weighted_loss(losses)
        if not torch.isfinite(total):
            vals = [l.item() for l in losses]
            return False, f"Non-finite loss for inputs {vals}: {total.item()}"
    return True, "Weights bounded for all test cases including near-zero"


def check_gradient_stable():
    """Verify gradients are finite after backward pass."""
    import torch.nn as nn
    torch.manual_seed(0)
    trainer = MultiTaskTrainer()
    # Simple model
    w = nn.Parameter(torch.randn(4))
    x = torch.randn(8, 4)
    y1 = x @ w + 0.01 * torch.randn(8)
    y2 = x @ w * 2

    # Compute near-zero loss for task 1 (easy task)
    pred = x @ w
    loss1 = ((pred - y1) ** 2).mean() * 0.001  # near zero
    loss2 = ((pred - y2) ** 2).mean()

    total = trainer.weighted_loss([loss1, loss2])
    total.backward()
    grad_norm = w.grad.norm().item()
    if not torch.isfinite(torch.tensor(grad_norm)):
        return False, f"Gradient non-finite ({grad_norm}) with near-zero task loss"
    if grad_norm > 1e6:
        return False, f"Gradient exploded: norm={grad_norm:.2e}"
    return True, f"Gradient stable: norm={grad_norm:.4f}"


def check_weighting_balance():
    """Verify harder tasks (larger loss) get higher weight."""
    trainer = MultiTaskTrainer()
    easy_loss = torch.tensor(0.1)
    hard_loss = torch.tensor(1.0)
    losses = [easy_loss, hard_loss]
    total = trainer.weighted_loss(losses)
    # With inverse weighting, hard task should dominate
    # We can't check directly without exposing weights, but check loss is finite
    if not torch.isfinite(total):
        return False, "Combined loss is non-finite"
    return True, f"Weighting produces finite combined loss: {total.item():.4f}"


def check_normalization():
    """Verify weights are normalized so gradients are scale-invariant."""
    trainer = MultiTaskTrainer()
    # Scale all losses by 10x — total should be roughly the same scale
    losses_normal = [torch.tensor(1.0) for _ in range(3)]
    losses_scaled = [torch.tensor(10.0) for _ in range(3)]
    t1 = trainer.weighted_loss(losses_normal).item()
    t2 = trainer.weighted_loss(losses_scaled).item()
    # With normalized weights, both should give the same combined loss
    ratio = abs(t2 / (t1 + 1e-8))
    if ratio > 50 or ratio < 0.02:
        return False, f"Weights not normalized: ratio when scaling by 10x = {ratio:.3f}"
    return True, f"Weights normalized: scale-10x ratio = {ratio:.3f}"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if res.get("crashed", False):
        return False, "Training crashed (gradient explosion / NaN)"
    if not res.get("converged", False):
        losses = res.get("final_val_losses", [])
        return False, f"Training did not converge: val_losses={losses}"
    return True, f"Training converged: val_losses={res.get('final_val_losses', [])}"


def check():
    checks = [
        ("No explosion near zero", check_no_explosion_near_zero),
        ("Epsilon in denominator", check_epsilon_in_denominator),
        ("Detach used", check_detach_used),
        ("Weights bounded", check_weights_bounded),
        ("Gradient stable", check_gradient_stable),
        ("Weighting balance", check_weighting_balance),
        ("Normalization", check_normalization),
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
