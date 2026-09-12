"""Encoder-decoder cross-attention — contains Q/K/V swap bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class CrossAttention(nn.Module):
    """Encoder-decoder cross-attention.

    BUG: Q comes from encoder, K/V come from decoder — REVERSED.

    Correct behavior:
      Q = decoder_hidden (decoder queries what it needs)
      K = encoder_output (encoder keys to match against)
      V = encoder_output (encoder values to retrieve)

    Buggy behavior (current):
      Q = encoder_output (encoder queries decoder states)
      K = decoder_hidden (decoder provides keys)
      V = decoder_hidden (decoder provides values)

    This means the decoder cannot attend to encoder representations.
    Instead it attends to its own states (using encoder as query) which
    is just a form of cross-attention between encoder and decoder states,
    not the intended decoder-attends-to-encoder pattern.
    """

    def __init__(self, embed_dim: int = 48, num_heads: int = 4):
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

    def forward(self, decoder_hidden: torch.Tensor,
                encoder_output: torch.Tensor) -> torch.Tensor:
        """
        Args:
            decoder_hidden: (B, tgt_len, embed_dim) — decoder states
            encoder_output: (B, src_len, embed_dim) — encoder output
        Returns:
            (B, tgt_len, embed_dim)
        """
        B = decoder_hidden.size(0)
        tgt_len = decoder_hidden.size(1)
        src_len = encoder_output.size(1)

        # BUG: Q from encoder, K/V from decoder — WRONG sources
        # Correct: Q from decoder, K/V from encoder
        q = self.q_proj(encoder_output)    # BUG: should be decoder_hidden
        k = self.k_proj(decoder_hidden)    # BUG: should be encoder_output
        v = self.v_proj(decoder_hidden)    # BUG: should be encoder_output

        # Reshape for multi-head attention
        q = q.reshape(B, src_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.reshape(B, tgt_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.reshape(B, tgt_len, self.num_heads, self.head_dim).transpose(1, 2)

        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        out = attn @ v  # (B, num_heads, src_len, head_dim)
        out = out.transpose(1, 2).reshape(B, src_len, self.embed_dim)
        return self.out_proj(out)


class EncoderLayer(nn.Module):
    def __init__(self, embed_dim: int = 48, num_heads: int = 4):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 2), nn.ReLU(),
            nn.Linear(embed_dim * 2, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        attn_out, _ = self.self_attn(x, x, x)
        x = self.norm1(x + attn_out)
        x = self.norm2(x + self.ff(x))
        return x


class DecoderLayer(nn.Module):
    def __init__(self, embed_dim: int = 48, num_heads: int = 4):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.cross_attn = CrossAttention(embed_dim, num_heads)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 2), nn.ReLU(),
            nn.Linear(embed_dim * 2, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.norm3 = nn.LayerNorm(embed_dim)

    def forward(self, x, encoder_output):
        # Self-attention on decoder states
        attn_out, _ = self.self_attn(x, x, x)
        x = self.norm1(x + attn_out)
        # Cross-attention: attend to encoder
        # NOTE: cross_attn(decoder_hidden, encoder_output) — Q from decoder, K/V from encoder
        cross_out = self.cross_attn(x, encoder_output)  # BUG is inside CrossAttention
        # BUG makes cross_out have shape (B, src_len, embed) not (B, tgt_len, embed)
        # Crop to tgt_len to avoid shape errors
        cross_out = cross_out[:, :x.size(1), :]
        x = self.norm2(x + cross_out)
        x = self.norm3(x + self.ff(x))
        return x
