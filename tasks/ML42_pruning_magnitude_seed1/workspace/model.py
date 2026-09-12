"""Multi-head attention model for head pruning task."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadAttention(nn.Module):
    """Multi-head attention with per-head disable support."""

    def __init__(self, embed_dim: int = 48, num_heads: int = 6):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=False)

        # Head mask: 1 = active, 0 = pruned
        self.register_buffer("head_mask", torch.ones(num_heads))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)

        # Apply head mask (pruned heads output zero)
        head_mask = self.head_mask.view(1, self.num_heads, 1, 1)
        out = (attn @ v) * head_mask
        out = out.transpose(1, 2).reshape(B, T, C)
        return self.out_proj(out)

    def prune_heads(self, heads_to_prune: list):
        """Zero out the head mask for pruned heads."""
        for h in heads_to_prune:
            self.head_mask[h] = 0.0

    def get_head_weight_norms(self) -> torch.Tensor:
        """Compute L2 norm of weights for each head (magnitude-based importance)."""
        norms = []
        head_dim = self.head_dim
        for h in range(self.num_heads):
            q_h = self.q_proj.weight[h * head_dim:(h + 1) * head_dim, :]
            k_h = self.k_proj.weight[h * head_dim:(h + 1) * head_dim, :]
            v_h = self.v_proj.weight[h * head_dim:(h + 1) * head_dim, :]
            norm = (q_h.norm() + k_h.norm() + v_h.norm()).item()
            norms.append(norm)
        return torch.tensor(norms)


class TransformerBlock(nn.Module):
    def __init__(self, embed_dim: int = 48, num_heads: int = 6):
        super().__init__()
        self.attn = MultiHeadAttention(embed_dim, num_heads)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 2), nn.GELU(),
            nn.Linear(embed_dim * 2, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x


class AttentionClassifier(nn.Module):
    """Transformer classifier for structured head pruning."""

    def __init__(self, input_dim: int = 8, embed_dim: int = 48,
                 num_heads: int = 6, num_layers: int = 2,
                 num_classes: int = 3, seq_len: int = 16):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, embed_dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads) for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        for block in self.blocks:
            x = block(x)
        return self.head(self.norm(x).mean(dim=1))

    def get_all_attention_modules(self):
        return [block.attn for block in self.blocks]
