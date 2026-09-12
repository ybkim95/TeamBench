"""Binary classifier for threshold optimization task."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class BinaryClassifier(nn.Module):
    """Simple binary classifier outputting logits."""

    def __init__(self, input_dim: int = 16, hidden_dim: int = 48):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return raw logits (shape: [B, 1])."""
        return self.net(x).squeeze(-1)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return sigmoid probabilities."""
        with torch.no_grad():
            return torch.sigmoid(self.forward(x))
