"""Check EMA BN stats fix."""
import json, sys, os, copy
import torch
import torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import BNModel
from ema import ModelEMA


def check_ema_bn_behavior():
    """Verify EMA copies BN running stats directly (no EMA smoothing)."""
    torch.manual_seed(0)
    model = BNModel(input_dim=24, hidden_dim=128, num_classes=3)
    ema = ModelEMA(model, decay=0.95)

    # Run a forward pass to update BN running stats significantly
    X = torch.randn(64, 24) * 5.0  # Large scale to create big stats
    model.train()
    _ = model(X)  # Updates running_mean/var

    # Get training model's BN running stats
    train_sd = model.state_dict()
    train_running_means = {k: v.clone() for k, v in train_sd.items() if "running_mean" in k}

    # Update EMA
    ema.update(model)
    ema_sd = ema.ema_model.state_dict()

    # With correct implementation: EMA model's running_mean should EQUAL train's
    # With buggy implementation: EMA model's running_mean would be EMA-smoothed
    #   (closer to 0 than train's because initial EMA model has running_mean≈0)
    for k, train_rm in train_running_means.items():
        ema_rm = ema_sd[k]
        diff = (ema_rm - train_rm).abs().max().item()
        if diff > 1e-4:
            return False, (
                f"EMA model BN running_mean differs from training model by {diff:.6f}. "
                f"BN stats should be copied directly, not EMA-smoothed."
            )

    return True, "EMA model BN running stats correctly copied from training model"


def check_code():
    """Check that running_mean/var are handled separately in EMA update."""
    with open("ema.py") as f:
        src = f.read()
    has_special_bn = (
        ("running_mean" in src or "running_var" in src) and
        "copy_" in src
    )
    if not has_special_bn:
        return False, "ema.py does not have special handling for running_mean/running_var with copy_()"
    return True, "Special BN handling found in ema.py"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    ema_acc = res.get("final_ema_acc", 0)
    train_acc = res.get("final_train_acc", 0)
    print(f"Final: train_acc={train_acc:.4f} ema_acc={ema_acc:.4f}")

    ok, msg = check_ema_bn_behavior()
    print(f"EMA BN check: {msg}")
    if not ok:
        return False

    ok2, msg2 = check_code()
    print(f"Code check: {msg2}")
    if not ok2:
        return False

    if not res.get("converged", False):
        print(f"FAIL: EMA model did not converge (ema_acc={ema_acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
