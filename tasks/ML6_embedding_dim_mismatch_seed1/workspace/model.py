"""Model architecture for CNN feature extractor with FC layer mismatch.

Contains 2 dimension mismatch bugs that cause RuntimeError on forward pass.
"""
import torch
import torch.nn as nn


class FeatureExtractor(nn.Module):
    """Extracts features from input."""
    def __init__(self, input_dim: int = 20):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        # BUG 1: Projects to 256 but next layer expects 512
        self.fc2 = nn.Linear(256, 256)  # Should be 512
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(self.fc2(self.relu(self.fc1(x))))  # (batch, 256)


class Projector(nn.Module):
    """Projects features to representation space."""
    def __init__(self, input_dim: int = 512):  # Expects 512
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        # BUG 2: Outputs 128 but Head expects 256
        self.fc2 = nn.Linear(256, 128)  # Should be 256
        self.relu = nn.ReLU()

    def forward(self, x):
        # x: (batch, 512) — but FeatureExtractor sends (batch, 256) → crash
        return self.fc2(self.relu(self.fc1(x)))  # (batch, 128)


class Head(nn.Module):
    """Classification or reconstruction head."""
    def __init__(self, input_dim: int = 256, n_classes: int = 10):
        super().__init__()
        # Expects 256 but Projector outputs 128 → crash
        self.fc = nn.Linear(input_dim, n_classes)

    def forward(self, x):
        return self.fc(x)


class Model(nn.Module):
    """Full CNN feature extractor with FC layer mismatch."""
    def __init__(self, input_dim: int = 20):
        super().__init__()
        self.extractor = FeatureExtractor(input_dim)
        self.projector = Projector()
        self.head = Head()

    def forward(self, x):
        feat = self.extractor(x)    # (batch, 256) — should be 512
        proj = self.projector(feat)  # RuntimeError: mat1 and mat2 shapes cannot be multiplied
        return self.head(proj)       # RuntimeError
