"""Continual learning model."""
import torch
import torch.nn as nn


class ContinualModel(nn.Module):
    def __init__(self, input_dim: int = 24, hidden_dim: int = 80,
                 n_classes: int = 8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x):
        return self.net(x)
