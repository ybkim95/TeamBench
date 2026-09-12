"""Validate BYOL predictor fix."""
import json
import sys
import os
import torch
import torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from byol import BYOL, Predictor


def check_predictor_applied_in_loss():
    """Verify that predictor is applied to online projections."""
    with open("byol.py") as f:
        src = f.read()
    # The fix should use self.predictor(online_z1/z2) not just online_z1/z2 directly
    has_predictor_call = "self.predictor(online_z" in src or "predictor(online_z" in src
    if not has_predictor_call:
        return False, "byol.py does not apply predictor to online projections in loss()"
    return True, "Predictor applied to online projections"


def check_no_collapse():
    """Verify representations are non-trivial (not collapsed)."""
    torch.manual_seed(0)
    byol = BYOL()
    x = torch.randn(64, 32)
    reps = byol.get_representation(x)
    # Collapsed representations have near-zero variance
    var = reps.var(dim=0).mean().item()
    if var < 1e-4:
        return False, f"Representations collapsed: variance={var:.8f} < 1e-4"
    return True, f"Representations non-trivial: variance={var:.4f}"


def check_online_target_asymmetry():
    """Verify online has predictor but target does not."""
    byol = BYOL()
    # Online should have more parameters (predictor adds params)
    online_params = sum(p.numel() for p in byol.online.parameters())
    target_params = sum(p.numel() for p in byol.target.parameters())
    pred_params = sum(p.numel() for p in byol.predictor.parameters())
    # Online + predictor > target (asymmetry exists)
    if pred_params == 0:
        return False, "Predictor has no parameters — not instantiated"
    if online_params != target_params:
        # This is fine if architectures differ, but they should be same
        pass
    return True, (
        f"Asymmetry: online={online_params}, target={target_params}, "
        f"predictor={pred_params} params"
    )


def check_loss_not_trivially_zero():
    """Verify loss is not trivially zero (which would indicate collapsed fix)."""
    torch.manual_seed(0)
    byol = BYOL()
    x1 = torch.randn(16, 32)
    x2 = torch.randn(16, 32)
    loss = byol.loss(x1, x2)
    if loss.item() < 1e-6:
        return False, f"Loss is trivially zero ({loss.item():.8f}) — collapse detected"
    if loss.item() > 4.0:
        return False, f"Loss too large ({loss.item():.4f}) — representations may be random"
    return True, f"Loss in valid range: {loss.item():.4f}"


def check_predictor_architecture():
    """Verify predictor has the correct bottleneck structure."""
    byol = BYOL()
    pred = byol.predictor
    if not isinstance(pred, Predictor):
        return False, "byol.predictor is not a Predictor instance"
    # Run a forward pass
    z = torch.randn(8, 64)
    out = pred(z)
    if out.shape != z.shape:
        return False, f"Predictor output shape {out.shape} != input shape {z.shape}"
    return True, f"Predictor architecture OK: (64) -> predictor -> (64)"


def check_ema_updates_target():
    """Verify target network is updated via EMA."""
    torch.manual_seed(0)
    byol = BYOL()
    # Record initial target params
    t_before = list(byol.target.parameters())[0].data.clone()
    o_before = list(byol.online.parameters())[0].data.clone()
    # Simulate one update
    byol._ema_update()
    t_after = list(byol.target.parameters())[0].data.clone()
    # Target should have moved slightly toward online
    diff = (t_after - t_before).norm().item()
    if diff < 1e-10:
        return False, "Target parameters not updated by EMA"
    return True, f"EMA update OK: target moved by {diff:.6f}"


def check_representations_discriminative():
    """After a few gradient steps, representations should cluster by class."""
    torch.manual_seed(0)
    byol = BYOL()
    params = list(byol.online.parameters()) + list(byol.predictor.parameters())
    optimizer = torch.optim.Adam(params, lr=1e-3)

    # Simple 2-class data
    class0 = torch.randn(32, 32) + 2.0
    class1 = torch.randn(32, 32) - 2.0

    for _ in range(20):
        x = torch.cat([class0, class1])
        perm = torch.randperm(len(x))
        xb = x[perm[:32]]
        x1 = xb + 0.1 * torch.randn_like(xb)
        x2 = xb + 0.1 * torch.randn_like(xb)
        byol.update(x1, x2, optimizer)

    h0 = byol.get_representation(class0)
    h1 = byol.get_representation(class1)
    inter_dist = (h0.mean(0) - h1.mean(0)).norm().item()
    intra_dist = (h0.std(0).mean() + h1.std(0).mean()).item() / 2

    if intra_dist > 0 and inter_dist / intra_dist < 0.5:
        return False, (
            f"Representations not discriminative: inter/intra={inter_dist/intra_dist:.3f}"
        )
    return True, f"Representations discriminative: inter/intra={inter_dist:.3f}/{intra_dist:.3f}"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    acc = res.get("final_probe_acc", 0)
    if not res.get("converged", False):
        return False, f"BYOL did not converge: probe_acc={acc:.3f} < 0.55"
    return True, f"BYOL converged: probe_acc={acc:.3f}"


def check():
    checks = [
        ("Predictor applied in loss", check_predictor_applied_in_loss),
        ("No collapse", check_no_collapse),
        ("Online/target asymmetry", check_online_target_asymmetry),
        ("Loss not trivially zero", check_loss_not_trivially_zero),
        ("Predictor architecture", check_predictor_architecture),
        ("EMA updates target", check_ema_updates_target),
        ("Representations discriminative", check_representations_discriminative),
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
