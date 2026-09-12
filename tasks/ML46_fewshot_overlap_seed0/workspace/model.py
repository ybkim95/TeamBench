"""Prototypical network for few-shot classification."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class ProtoNet(nn.Module):
    """Prototypical Network (Snell et al. 2017)."""

    def __init__(self, input_dim: int = 32, hidden_dim: int = 64,
                 embed_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, x):
        return self.encoder(x)

    def episode_loss(self, support: torch.Tensor, support_labels: torch.Tensor,
                     query: torch.Tensor, query_labels: torch.Tensor,
                     n_way: int = 5) -> tuple:
        """Compute prototypical loss and accuracy for one episode."""
        support_emb = self.forward(support)
        query_emb = self.forward(query)

        # Compute class prototypes
        prototypes = []
        for c in range(n_way):
            mask = support_labels == c
            proto = support_emb[mask].mean(0)
            prototypes.append(proto)
        prototypes = torch.stack(prototypes)  # (N, embed_dim)

        # Compute distances from query to each prototype
        dists = torch.cdist(query_emb.unsqueeze(0), prototypes.unsqueeze(0)).squeeze(0)
        logits = -dists  # (N*Q, N)

        loss = F.cross_entropy(logits, query_labels)
        acc = (logits.argmax(1) == query_labels).float().mean().item()
        return loss, acc
