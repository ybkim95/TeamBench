"""Residual network model — contains initialization bug."""
import torch
import torch.nn as nn
import math


class ResBlock(nn.Module):
    """Residual block: output = x + F(x).

    BUG: The last linear layer uses default Xavier initialization.
    In a deep stack of 10 blocks, each block adds ~variance(1)
    to the signal, so the output variance grows to ~10.
    This causes poor gradient flow at initialization.

    FIX: Initialize the last linear layer to near-zero weights
    so each block initially acts as an identity mapping.
    """

    def __init__(self, dim: int):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.bn1 = nn.BatchNorm1d(dim)
        self.fc2 = nn.Linear(dim, dim)
        self.bn2 = nn.BatchNorm1d(dim)
        self.act = nn.ReLU()

        # BUG: fc2 uses default Xavier init — should be zero/near-zero
        # nn.init.zeros_(self.fc2.weight)  # <-- correct fix
        # nn.init.zeros_(self.fc2.bias)    # <-- correct fix

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.act(self.bn1(self.fc1(x)))
        out = self.bn2(self.fc2(out))
        return self.act(out + residual)


class ResNet(nn.Module):
    """Deep residual network with 10 blocks."""

    def __init__(self, input_dim: int = 24, hidden_dim: int = 48,
                 num_classes: int = 1, num_blocks: int = 10):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
        )
        self.blocks = nn.ModuleList([ResBlock(hidden_dim) for _ in range(num_blocks)])
        self.head = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        for block in self.blocks:
            x = block(x)
        return self.head(x)


def check_init_variance(model: ResNet) -> dict:
    """Measure output variance at initialization to diagnose the bug."""
    model.eval()
    with torch.no_grad():
        x = torch.randn(256, model.stem[0].in_features)
        x = model.stem(x)
        variances = []
        for block in model.blocks:
            x = block(x)
            variances.append(x.var().item())
    return {"variances": variances, "max_variance": max(variances)}
