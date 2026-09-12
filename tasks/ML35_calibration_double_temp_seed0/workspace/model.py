"""Classifier model with built-in temperature scaling — BUG: double-applies temperature."""
import torch
import torch.nn as nn


class CalibratedClassifier(nn.Module):
    """Classification model with post-hoc temperature scaling.

    BUG: This model divides logits by `temperature` in forward().
    The evaluator ALSO divides by temperature before computing softmax,
    resulting in temperature being applied twice (T^2 effective scaling).

    Fix: Remove temperature division from ONE location — either here
    OR in evaluator.py (not both).
    """

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128,
                 num_classes: int = 5, temperature: float = 1.8):
        super().__init__()
        self.temperature = temperature
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass — returns temperature-scaled logits.

        BUG: Divides logits by self.temperature here.
        The evaluator then divides again, applying T twice.
        """
        logits = self.net(x)
        # BUG: temperature scaling applied here (will also be applied in evaluator)
        return logits / self.temperature

    def get_raw_logits(self, x: torch.Tensor) -> torch.Tensor:
        """Return unscaled logits (bypass temperature in forward)."""
        return self.net(x)
