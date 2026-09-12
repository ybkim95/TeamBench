"""Active learning model with MC Dropout support."""
import torch
import torch.nn as nn


class ActiveModel(nn.Module):
    """Classifier with dropout for MC Dropout uncertainty estimation."""

    def __init__(self, input_dim: int = 20, hidden_dim: int = 64,
                 n_classes: int = 4, dropout_rate: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x):
        return self.net(x)
