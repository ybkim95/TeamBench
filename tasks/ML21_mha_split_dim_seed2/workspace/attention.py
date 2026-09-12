"""Multi-head attention — contains wrong split dimension bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadAttention(nn.Module):
    """Multi-head self-attention.

    BUG: The Q/K/V reshape splits the sequence (T) dimension instead of
    the embedding dimension (C).

    Correct: reshape (B, T, C) -> (B, T, num_heads, head_dim) then transpose
             -> each head attends over ALL T positions with head_dim features

    Buggy: reshape (B, T, C) -> (B, num_heads, T//num_heads, C) then transpose
           -> each head attends over T//num_heads positions with C features
           -> completely wrong attention pattern
    """

    def __init__(self, embed_dim: int = 64, num_heads: int = 8):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x: torch.Tensor,
                mask: torch.Tensor = None) -> torch.Tensor:
        """
        Args:
            x: (B, T, embed_dim)
            mask: optional (B, T, T) boolean mask (True = masked)
        Returns:
            (B, T, embed_dim)
        """
        B, T, C = x.shape

        q = self.q_proj(x)  # (B, T, C)
        k = self.k_proj(x)
        v = self.v_proj(x)

        # BUG: splits T dimension instead of C (embed_dim)
        # This creates heads of shape (T//num_heads, C) instead of (T, head_dim)
        q = q.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
        k = k.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
        v = v.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
        # NOTE: transpose omitted because shape is already (B, num_heads, T//H, C)
        # Correct would be: reshape(B, T, num_heads, head_dim).transpose(1, 2)
        #                   -> (B, num_heads, T, head_dim)

        # scale is also wrong (should be head_dim^-0.5 not C^-0.5)
        attn = (q @ k.transpose(-2, -1)) * (C ** -0.5)

        if mask is not None:
            attn = attn.masked_fill(mask.unsqueeze(1), float("-inf"))

        attn = F.softmax(attn, dim=-1)
        out = attn @ v  # (B, num_heads, T//num_heads, C)
        out = out.reshape(B, T, C)  # BUG: reshape back drops multi-head structure
        return self.out_proj(out)
