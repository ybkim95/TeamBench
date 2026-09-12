"""Multi-task model with shared encoder and task-specific heads."""
import torch
import torch.nn as nn


class MultiTaskModel(nn.Module):
    """Shared encoder with 3 task-specific output heads."""

    def __init__(self, input_dim: int = 24, hidden_dim: int = 96,
                 n_tasks: int = 3):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.heads = nn.ModuleList([
            nn.Linear(hidden_dim, 1) for _ in range(n_tasks)
        ])

    def forward(self, x: torch.Tensor) -> list:
        h = self.shared(x)
        return [head(h).squeeze(-1) for head in self.heads]
