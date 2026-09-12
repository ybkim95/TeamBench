"""Model architecture for siamese network for similarity with projection mismatch.

Contains 2 dimension mismatch bugs that cause RuntimeError on forward pass.
"""
import torch
import torch.nn as nn


class FeatureExtractor(nn.Module):
    """Extracts features from input."""
    def __init__(self, input_dim: int = 17):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        # BUG 1: Projects to 64 but next layer expects 128
        self.fc2 = nn.Linear(256, 64)  # Should be 128
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(self.fc2(self.relu(self.fc1(x))))  # (batch, 64)


class Projector(nn.Module):
    """Projects features to representation space."""
    def __init__(self, input_dim: int = 128):  # Expects 128
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        # BUG 2: Outputs 512 but Head expects 256
        self.fc2 = nn.Linear(256, 512)  # Should be 256
        self.relu = nn.ReLU()

    def forward(self, x):
        # x: (batch, 128) — but FeatureExtractor sends (batch, 64) → crash
        return self.fc2(self.relu(self.fc1(x)))  # (batch, 512)


class Head(nn.Module):
    """Classification or reconstruction head."""
    def __init__(self, input_dim: int = 256, n_classes: int = 2):
        super().__init__()
        # Expects 256 but Projector outputs 512 → crash
        self.fc = nn.Linear(input_dim, n_classes)

    def forward(self, x):
        return self.fc(x)


class Model(nn.Module):
    """Full siamese network for similarity with projection mismatch."""
    def __init__(self, input_dim: int = 17):
        super().__init__()
        self.extractor = FeatureExtractor(input_dim)
        self.projector = Projector()
        self.head = Head()

    def forward(self, x):
        feat = self.extractor(x)    # (batch, 64) — should be 128
        proj = self.projector(feat)  # RuntimeError: mat1 and mat2 shapes cannot be multiplied
        return self.head(proj)       # RuntimeError
