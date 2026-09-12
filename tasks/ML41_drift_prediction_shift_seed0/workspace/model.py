"""Classifier model for drift detection task."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleClassifier(nn.Module):
    """Simple MLP classifier for drift detection evaluation."""

    def __init__(self, input_dim: int = 16, hidden_dim: int = 64,
                 num_classes: int = 3):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.head = nn.Linear(hidden_dim // 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x))

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Get intermediate representations (for embedding-based drift detection)."""
        with torch.no_grad():
            return self.encoder(x)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return F.softmax(self.forward(x), dim=-1)
