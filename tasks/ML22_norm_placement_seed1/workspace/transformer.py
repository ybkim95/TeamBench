"""Transformer model — contains broken hybrid LayerNorm placement."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class SimpleSelfAttention(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, T, C)
        return self.proj(out)


class TransformerBlock(nn.Module):
    """Transformer block with broken hybrid normalization.

    BUG: Inconsistent mix of pre-norm and post-norm:
      - Attention uses POST-norm: norm(x + attn(x))
      - FFN uses PRE-norm style but without proper residual: x + ff(norm(x))

    This is NEITHER pure pre-norm NOR pure post-norm — it creates:
    1. Gradient instability (post-norm attention has exploding/vanishing gradients)
    2. Distribution mismatch (FFN gets post-normed input but attn gets raw input)

    Correct pre-norm:  x = x + attn(norm(x));  x = x + ff(norm(x))
    Correct post-norm: x = norm(x + attn(x));  x = norm(x + ff(x))
    """

    def __init__(self, embed_dim: int, num_heads: int):
        super().__init__()
        self.attn = SimpleSelfAttention(embed_dim, num_heads)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, 4 * embed_dim),
            nn.GELU(),
            nn.Linear(4 * embed_dim, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        # BUG: post-norm for attention (norm AFTER residual add)
        x = self.norm1(x + self.attn(x))   # post-norm: norm(x + attn(x))
        # BUG: pre-norm style for FFN but applied inconsistently
        x = x + self.ff(self.norm2(x))     # pre-norm: x + ff(norm(x))
        # The mix means:
        # - attn block: output of norm1 feeds into ff block
        # - ff block: gets normalized input (fine) but adds to already-normed x
        # Correct pre-norm would be:
        #   residual = x; x = self.norm1(x); x = residual + self.attn(x)
        #   residual = x; x = self.norm2(x); x = residual + self.ff(x)
        return x


class TransformerClassifier(nn.Module):
    def __init__(self, input_dim: int = 8, embed_dim: int = 48,
                 num_heads: int = 4, num_layers: int = 3,
                 num_classes: int = 5):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, embed_dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        x = self.input_proj(x)
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        return self.head(x.mean(dim=1))
