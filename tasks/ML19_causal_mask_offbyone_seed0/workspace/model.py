"""Causal transformer model — contains causal mask off-by-one bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class CausalSelfAttention(nn.Module):
    """Causal multi-head self-attention.

    BUG: The causal mask uses torch.triu(diagonal=0) which also masks the
    diagonal — preventing each token from attending to itself.

    Correct: torch.triu(diagonal=1) masks only strictly future positions,
    allowing self-attention on the current position.
    """

    def __init__(self, embed_dim: int, num_heads: int, seq_len: int):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

        # BUG: diagonal=0 masks the diagonal (self-attention blocked)
        # Correct: diagonal=1 — mask only future positions
        mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=0).bool()
        self.register_buffer("causal_mask", mask)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = (q @ k.transpose(-2, -1)) * self.scale
        # Apply causal mask — masked positions set to -inf
        mask = self.causal_mask[:T, :T]
        attn = attn.masked_fill(mask.unsqueeze(0).unsqueeze(0), float("-inf"))
        attn = F.softmax(attn, dim=-1)
        # Handle NaN from all-masked rows (diagonal=0 bug can cause this at pos 0)
        attn = torch.nan_to_num(attn, nan=0.0)

        out = attn @ v
        out = out.transpose(1, 2).reshape(B, T, C)
        return self.proj(out)


class TransformerBlock(nn.Module):
    def __init__(self, embed_dim: int, num_heads: int, seq_len: int):
        super().__init__()
        self.attn = CausalSelfAttention(embed_dim, num_heads, seq_len)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, 4 * embed_dim),
            nn.GELU(),
            nn.Linear(4 * embed_dim, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x


class CausalLM(nn.Module):
    """Causal language model (decoder-only transformer)."""

    def __init__(self, vocab_size: int = 64, embed_dim: int = 32,
                 num_heads: int = 4, num_layers: int = 2,
                 seq_len: int = 16):
        super().__init__()
        self.seq_len = seq_len
        self.token_emb = nn.Embedding(vocab_size, embed_dim)
        self.pos_emb = nn.Embedding(seq_len, embed_dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, seq_len)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device).unsqueeze(0)
        x = self.token_emb(idx) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        return self.lm_head(x)
