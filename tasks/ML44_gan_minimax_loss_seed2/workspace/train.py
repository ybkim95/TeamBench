"""Train GAN on synthetic mixture data."""
import json
import sys
import os
import torch
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gan import GAN


def make_data(n: int = 3711, n_modes: int = 3, dim: int = 4):
    torch.manual_seed(42)
    centers = torch.randn(3, 4) * 3.0
    samples_per_mode = n // 3
    parts = []
    for c in centers:
        parts.append(c + 0.3 * torch.randn(samples_per_mode, 4))
    return torch.cat(parts, dim=0)


def compute_coverage(samples: torch.Tensor, real: torch.Tensor, threshold: float = 1.0) -> float:
    """Fraction of real data modes covered by generated samples."""
    # Simple coverage: for each real point, check if any generated sample is close
    covered = 0
    check_n = min(200, len(real))
    for i in range(check_n):
        dists = (samples - real[i]).norm(dim=1)
        if dists.min().item() < threshold:
            covered += 1
    return covered / check_n


def train():
    torch.manual_seed(0)
    real_data = make_data()
    gan = GAN()
    n = len(real_data)

    history = []
    for epoch in range(214):
        idx = torch.randperm(n)
        d_losses, g_losses = [], []
        for i in range(0, n, 32):
            batch = real_data[idx[i:i + 32]]
            if len(batch) < 4:
                continue
            d_l, g_l = gan.train_step(batch, len(batch))
            d_losses.append(d_l)
            g_losses.append(g_l)

        if (epoch + 1) % 50 == 0:
            samples = gan.sample(500)
            coverage = compute_coverage(samples, real_data[:500])
            history.append({
                "epoch": epoch + 1,
                "d_loss": np.mean(d_losses),
                "g_loss": np.mean(g_losses),
                "coverage": coverage,
            })
            print(f"Epoch {epoch+1}/{214} d_loss={np.mean(d_losses):.4f} "
                  f"g_loss={np.mean(g_losses):.4f} coverage={coverage:.3f}")

    final_samples = gan.sample(1000)
    final_coverage = compute_coverage(final_samples, real_data[:500])
    results = {
        "final_coverage": final_coverage,
        "converged": final_coverage > 0.5,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final coverage: {final_coverage:.3f}")
    return results


if __name__ == "__main__":
    train()
