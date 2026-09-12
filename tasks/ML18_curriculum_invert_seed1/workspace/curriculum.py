"""Curriculum learning utilities — contains inverted pacing function bug."""
import torch
import numpy as np


def compute_difficulty_scores(X: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Compute per-sample difficulty scores (higher = harder).

    For classification: difficulty = distance to class boundary
    Easy samples: far from decision boundary (high-confidence region)
    Hard samples: near decision boundary (ambiguous region)
    """
    # Compute distance from each sample to its class centroid
    # Samples far from their class centroid are "harder"
    classes = y.unique()
    difficulty = torch.zeros(len(X))
    for c in classes:
        mask = (y == c)
        if mask.sum() == 0:
            continue
        centroid = X[mask].mean(0)
        dists = ((X[mask] - centroid) ** 2).sum(1).sqrt()
        difficulty[mask] = dists
    # Normalize to [0, 1]
    d_min, d_max = difficulty.min(), difficulty.max()
    if d_max > d_min:
        difficulty = (difficulty - d_min) / (d_max - d_min)
    return difficulty


def pacing_function(epoch: int, total_epochs: int, start_fraction: float = 0.3) -> float:
    """Return the fraction of training data to use at this epoch.

    Curriculum learning: start with easy samples, gradually add harder ones.
    At epoch 0: use `start_fraction` of data (easiest samples only)
    At final epoch: use 100% of data (all samples)

    BUG: The pacing function is INVERTED — it starts at 1.0 and ends at start_fraction.
    This means we begin with ALL data (hard samples included) and end with only easy ones.
    """
    progress = epoch / max(total_epochs - 1, 1)  # 0.0 at start, 1.0 at end

    # BUG: Inverted — decreases from 1.0 to start_fraction
    fraction = 1.0 - (1.0 - start_fraction) * progress
    # CORRECT would be:
    # fraction = start_fraction + (1.0 - start_fraction) * progress

    return float(max(0.01, min(1.0, fraction)))


def get_curriculum_subset(
    X: torch.Tensor,
    y: torch.Tensor,
    difficulty: torch.Tensor,
    epoch: int,
    total_epochs: int,
    start_fraction: float = 0.3,
) -> tuple:
    """Return the curriculum subset for this epoch.

    Selects the `fraction` easiest samples (lowest difficulty scores).
    """
    fraction = pacing_function(epoch, total_epochs, start_fraction)
    n_use = max(1, int(len(X) * fraction))
    # Sort by difficulty (ascending = easiest first)
    sorted_idx = difficulty.argsort()
    selected_idx = sorted_idx[:n_use]
    return X[selected_idx], y[selected_idx], fraction
