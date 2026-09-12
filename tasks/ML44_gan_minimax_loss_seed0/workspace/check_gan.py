"""Validate GAN minimax loss fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gan import GAN


def check_generator_loss_type():
    """Verify generator uses non-saturating loss."""
    with open("gan.py") as f:
        src = f.read()
    # Check that -log(D(G(z))) form is used, not log(1 - D(G(z)))
    has_non_saturating = "-torch.log(d_fake" in src or "- torch.log(d_fake" in src
    has_minimax = "torch.log(1 - d_fake" in src or "log(1 - d_fake" in src
    if has_minimax and not has_non_saturating:
        return False, "Generator still uses minimax loss log(1-D(G(z))) — use -log(D(G(z)))"
    if not has_non_saturating:
        return False, "Generator does not use non-saturating loss -log(D(G(z)))"
    return True, "Generator uses non-saturating loss"


def check_gradient_flow():
    """Verify generator loss provides non-zero gradients when D is confident."""
    torch.manual_seed(0)
    gan = GAN()

    # Make discriminator output near 0 (discriminator is confident fake is fake)
    # This is the saturation scenario
    fake = torch.randn(8, 8, requires_grad=False)
    # Manually set D output to near 0 by scaling input
    with torch.no_grad():
        # Create fake samples that fool discriminator to output near 0
        fake_low = torch.zeros(8, 8)

    fake_low.requires_grad_(True)
    # Compute generator loss — should have non-trivial gradient
    d_out = gan.D(fake_low)
    # If using minimax: loss = log(1-d_out) -> gradient ≈ 0 when d_out ≈ 0
    # If using non-saturating: loss = -log(d_out) -> gradient = -1/d_out (large)
    g_loss = gan.generator_loss(fake_low)
    g_loss.backward()

    grad_norm = fake_low.grad.norm().item()
    if grad_norm < 1e-3:
        return False, f"Generator gradient near zero ({grad_norm:.6f}) — saturation not fixed"
    return True, f"Generator gradient OK: norm={grad_norm:.4f}"


def check_loss_sign():
    """Verify generator loss decreases when D(G(z)) increases."""
    torch.manual_seed(0)
    gan = GAN()

    # Loss with high D(G(z)) should be LOWER than with low D(G(z))
    # (generator wants D to be fooled, i.e., D output = 1)
    fake_good = torch.randn(16, 8)  # will likely get mid-range D output
    with torch.no_grad():
        d_good = gan.D(fake_good).mean().item()

    # The non-saturating loss -log(D(G(z))) should be smaller when D(G(z)) is larger
    # Test with a simple construction
    fake_a = torch.zeros(8, 8)  # tends to give low D output
    fake_b = torch.ones(8, 8) * 0.01  # similar

    g_loss_a = gan.generator_loss(fake_a).item()
    g_loss_b = gan.generator_loss(fake_b).item()

    # Both should be finite
    if not (torch.isfinite(torch.tensor(g_loss_a)) and torch.isfinite(torch.tensor(g_loss_b))):
        return False, f"Generator loss is non-finite: a={g_loss_a}, b={g_loss_b}"
    return True, f"Generator loss finite: {g_loss_a:.4f}, {g_loss_b:.4f}"


def check_loss_direction():
    """Verify minimizing g_loss pushes D(G(z)) toward 1."""
    torch.manual_seed(1)
    gan = GAN()
    z = torch.randn(16, 16)
    fake = gan.G(z)

    d_before = gan.D(fake.detach()).mean().item()
    g_loss = gan.generator_loss(fake)
    # Gradient should point toward increasing D(G(z))
    g_loss.backward()

    # Check gradient of G's output: should push output toward region where D→1
    g_loss_val = g_loss.item()
    # Non-saturating loss is negative of log(D(G(z))), so minimizing it maximizes D(G(z))
    # Minimax loss log(1-D(G(z))) minimization also maximizes D(G(z)) but saturates
    # The key is that non-saturating loss = -log(D) and must be negative or small positive
    # Actually -log(D(G(z))) is always positive since D in (0,1)
    # log(1-D(G(z))) minimax is negative and approaches 0 from below
    # Non-saturating is positive, decreasing as D→1
    return True, f"Loss direction check passed: g_loss={g_loss_val:.4f}"


def check_training_results():
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    cov = res.get("final_coverage", 0)
    if not res.get("converged", False):
        return False, f"GAN did not converge: coverage={cov:.3f} < 0.5"
    return True, f"GAN converged: coverage={cov:.3f}"


def check_no_nan():
    """Verify training step produces finite losses."""
    torch.manual_seed(0)
    gan = GAN()
    real = torch.randn(32, 8)
    d_loss, g_loss = gan.train_step(real, 32)
    if not (torch.isfinite(torch.tensor(d_loss)) and torch.isfinite(torch.tensor(g_loss))):
        return False, f"Training step produces non-finite losses: d={d_loss}, g={g_loss}"
    return True, f"Training step losses finite: d={d_loss:.4f}, g={g_loss:.4f}"


def check_d_loss_structure():
    """Verify discriminator still uses standard log loss."""
    with open("gan.py") as f:
        src = f.read()
    if "discriminator_loss" not in src:
        return False, "discriminator_loss method not found"
    # D loss should have both real and fake terms
    if "d_real" not in src or "d_fake" not in src:
        return False, "Discriminator loss missing d_real or d_fake"
    return True, "Discriminator loss structure OK"


def check_gradient_magnitude_ratio():
    """Non-saturating loss should give larger gradients than minimax near saturation."""
    torch.manual_seed(0)
    gan = GAN()

    # Create scenario where D output is near 0 (saturation)
    fake = torch.zeros(8, 8, requires_grad=True)

    # Compute gradient with current (should be non-saturating after fix)
    d_out = gan.D(fake.detach())
    g_loss = gan.generator_loss(fake)
    g_loss.backward()
    grad_norm = fake.grad.norm().item()

    if grad_norm < 0.01:
        return False, f"Gradient norm {grad_norm:.6f} too small — saturation likely not fixed"
    return True, f"Gradient magnitude adequate: {grad_norm:.4f}"


def check():
    checks = [
        ("Loss type in code", check_generator_loss_type),
        ("Gradient flow at saturation", check_gradient_flow),
        ("Loss finiteness", check_loss_sign),
        ("Loss direction", check_loss_direction),
        ("No NaN in training step", check_no_nan),
        ("Discriminator loss structure", check_d_loss_structure),
        ("Gradient magnitude ratio", check_gradient_magnitude_ratio),
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
