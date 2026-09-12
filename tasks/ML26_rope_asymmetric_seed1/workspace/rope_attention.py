"""RoPE (Rotary Position Embedding) attention — asymmetric rotation bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


def build_rope_cache(seq_len: int, head_dim: int,
                     base: float = 10000.0) -> tuple:
    """Build RoPE cos/sin cache for positions 0..seq_len-1.

    Returns:
        cos: (seq_len, head_dim)
        sin: (seq_len, head_dim)
    """
    # Frequencies: theta_i = 1 / base^(2i/d)
    theta = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
    positions = torch.arange(seq_len).float()
    freqs = torch.outer(positions, theta)  # (seq_len, head_dim//2)
    # Expand to head_dim by repeating: [f0, f1, ..., fk, f0, f1, ..., fk]
    freqs_full = torch.cat([freqs, freqs], dim=-1)  # (seq_len, head_dim)
    return freqs_full.cos(), freqs_full.sin()


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate the last dimension by half: [-x1, x0] for (x0, x1) pairs."""
    half = x.shape[-1] // 2
    x1 = x[..., :half]
    x2 = x[..., half:]
    return torch.cat([-x2, x1], dim=-1)


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Apply rotary embedding to x.

    Args:
        x: (..., T, head_dim)
        cos: (T, head_dim)
        sin: (T, head_dim)
    """
    return x * cos + rotate_half(x) * sin


class RoPEAttention(nn.Module):
    """Multi-head self-attention with Rotary Position Embeddings.

    BUG: RoPE is applied to keys (K) but NOT to queries (Q).

    Correct: both Q and K must be rotated with their respective positions.
    The relative position signal comes from the interaction q_rot @ k_rot:
      (R_m * q) · (R_n * k) = q · (R_{n-m} * k)
    This works only when BOTH are rotated. Without rotating Q:
      q · (R_n * k)  — absolute position of K, but no position in Q
    The model loses the relative position property entirely.
    """

    def __init__(self, embed_dim: int = 48, num_heads: int = 4,
                 max_seq_len: int = 64):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

        # Precompute RoPE cache
        cos, sin = build_rope_cache(max_seq_len, self.head_dim)
        self.register_buffer("rope_cos", cos)  # (max_seq_len, head_dim)
        self.register_buffer("rope_sin", sin)  # (max_seq_len, head_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        # q, k, v: (B, num_heads, T, head_dim)

        # Get RoPE encodings for positions 0..T-1
        cos = self.rope_cos[:T].unsqueeze(0).unsqueeze(0)  # (1, 1, T, head_dim)
        sin = self.rope_sin[:T].unsqueeze(0).unsqueeze(0)  # (1, 1, T, head_dim)

        # BUG: only K is rotated, Q is NOT rotated
        # Both should be rotated: q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)   # keys rotated
        # q = apply_rope(q, cos, sin)  # BUG: missing — queries NOT rotated

        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, T, C)
        return self.proj(out)
