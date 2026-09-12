"""Model with BatchNorm layers."""
import torch.nn as nn


class BNModel(nn.Module):
    def __init__(self, input_dim=48, hidden_dim=96, num_classes=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(48, 96),
            nn.BatchNorm1d(96),
            nn.ReLU(),
            nn.Linear(96, 96),
            nn.BatchNorm1d(96),
            nn.ReLU(),
            nn.Linear(96, 96),
            nn.BatchNorm1d(96),
            nn.ReLU(),
            nn.Linear(96, 96),
            nn.BatchNorm1d(96),
            nn.ReLU(),
            nn.Linear(96, 96),
            nn.BatchNorm1d(96),
            nn.ReLU(),
            nn.Linear(96, 5)
        )

    def forward(self, x):
        return self.net(x)
