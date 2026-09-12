"""Model architecture for text embedding classifier with projection mismatch.

Contains 2 dimension mismatch bugs that cause RuntimeError on forward pass.
"""
import torch
import torch.nn as nn


class EmbeddingLayer(nn.Module):
    """Projects input to embedding space."""
    def __init__(self, vocab_size: int = 10000, embedding_dim: int = 256):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embedding_dim)
        # BUG 1: Projects to 512 but Encoder expects 256
        self.projection = nn.Linear(embedding_dim, 512)  # Should be 256

    def forward(self, x):
        # x: (batch, seq_len) token ids
        embedded = self.embed(x)  # (batch, seq_len, 256)
        # Mean pool over sequence
        pooled = embedded.mean(dim=1)  # (batch, 256)
        return self.projection(pooled)  # (batch, 512) ← WRONG DIM


class Encoder(nn.Module):
    """Encodes embedding to hidden representation."""
    def __init__(self, input_dim: int = 256, hidden_dim: int = 128):
        super().__init__()
        # Expects input_dim=256 but EmbeddingLayer outputs 512 → crash
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        # BUG 2: Outputs 64 but Classifier expects 128
        self.fc2 = nn.Linear(hidden_dim, 64)  # Should be 128

    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))  # (batch, 64) ← WRONG DIM


class Classifier(nn.Module):
    """Final classification head."""
    def __init__(self, input_dim: int = 128, n_classes: int = 5):
        super().__init__()
        # Expects input_dim=128 but Encoder outputs 64 → crash
        self.fc = nn.Linear(input_dim, n_classes)

    def forward(self, x):
        return self.fc(x)


class TextClassifier(nn.Module):
    """Full text classifier pipeline."""
    def __init__(self):
        super().__init__()
        self.embedding = EmbeddingLayer()
        self.encoder = Encoder()
        self.classifier = Classifier()

    def forward(self, x):
        # This will crash due to dimension mismatches
        emb = self.embedding(x)      # (batch, 512) — should be 256
        enc = self.encoder(emb)      # RuntimeError: mat1 and mat2 shapes cannot be multiplied
        out = self.classifier(enc)   # RuntimeError: mat1 and mat2 shapes cannot be multiplied
        return out
