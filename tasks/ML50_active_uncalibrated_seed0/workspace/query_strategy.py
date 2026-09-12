"""Active learning query strategies — contains uncalibrated entropy bug."""
import torch
import torch.nn.functional as F
import numpy as np


class EntropyStrategy:
    """Active learning using entropy of softmax output.

    BUG: Uses raw softmax entropy from a single forward pass.
    Modern neural networks are overconfident — softmax probabilities
    are NOT well-calibrated. The entropy of an overconfident model:
    1. Is near-zero for in-distribution samples (even near the boundary)
    2. Can be high for out-of-distribution samples that happen to activate
       specific neurons

    This means entropy selection may pick samples that are:
    - Easy (OOD but confidently wrong) instead of hard (boundary)
    - Dominated by the model's miscalibration rather than true uncertainty

    Fix: use MC Dropout (Monte Carlo Dropout) to estimate epistemic uncertainty.
    Run T stochastic forward passes with dropout enabled and measure the
    variance of predictions. This captures what the MODEL doesn't know,
    not just what the SOFTMAX says.

    BALD score: mean_entropy - entropy(mean_prediction)
    = epistemic uncertainty (ignoring aleatoric)
    """

    def select(self, model, X_pool: torch.Tensor, n: int) -> np.ndarray:
        """Select n samples with highest entropy.

        BUG: single forward pass, model.eval() — no MC Dropout.
        High entropy might reflect overconfidence artifacts, not true uncertainty.
        """
        model.eval()
        with torch.no_grad():
            logits = model(X_pool)
            probs = F.softmax(logits, dim=1)
            # Entropy: -sum(p * log(p))
            entropy = -(probs * (probs + 1e-10).log()).sum(dim=1)
        # BUG: this selects based on miscalibrated softmax entropy
        indices = entropy.argsort(descending=True)[:n].numpy()
        return indices


class MCDropoutStrategy:
    """Active learning using BALD (Bayesian Active Learning by Disagreement).

    Uses MC Dropout to estimate epistemic uncertainty via T stochastic passes.
    This is the CORRECT approach when the model is not well-calibrated.
    """

    def __init__(self, n_mc_samples: int = 20):
        self.n_mc_samples = n_mc_samples

    def select(self, model, X_pool: torch.Tensor, n: int) -> np.ndarray:
        """Select n samples with highest epistemic uncertainty (BALD score).

        Runs T forward passes with dropout enabled and selects samples
        where the model's predictions vary most across passes.
        """
        # Enable dropout during inference
        model.train()  # enables dropout
        all_probs = []
        with torch.no_grad():
            for _ in range(self.n_mc_samples):
                logits = model(X_pool)
                probs = F.softmax(logits, dim=1)
                all_probs.append(probs)

        all_probs = torch.stack(all_probs)  # (T, N, C)

        # Mean prediction
        mean_probs = all_probs.mean(0)  # (N, C)

        # Entropy of mean (total uncertainty)
        H_mean = -(mean_probs * (mean_probs + 1e-10).log()).sum(dim=1)

        # Mean of entropies (expected data uncertainty)
        H_individual = -(all_probs * (all_probs + 1e-10).log()).sum(dim=-1)
        E_H = H_individual.mean(0)

        # BALD = H(mean) - E[H] = epistemic uncertainty
        bald = H_mean - E_H
        model.eval()  # restore eval mode
        indices = bald.argsort(descending=True)[:n].numpy()
        return indices
