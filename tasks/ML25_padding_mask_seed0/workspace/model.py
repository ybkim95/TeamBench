"""Causal LM with padded batches — missing padding mask bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


PAD_TOKEN_ID = 0


class CausalAttention(nn.Module):
    """Causal self-attention for padded variable-length batches.

    BUG: Only the causal mask is applied. The padding mask is missing.

    Without a padding mask:
    - PAD tokens attend to real tokens (and get gradients)
    - This pollutes the representation of real tokens near padding
    - Training loss includes PAD positions, diluting the learning signal

    The fix requires BOTH masks:
    1. Causal mask: prevent attending to future positions
    2. Padding mask: prevent attending to PAD tokens (and mask PAD positions in loss)
    """

    def __init__(self, embed_dim: int = 32, num_heads: int = 4,
                 max_seq_len: int = 24):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=False)
        self.proj = nn.Linear(embed_dim, embed_dim, bias=False)

        # Correct causal mask (diagonal=1 — only future positions masked)
        causal = torch.triu(torch.ones(max_seq_len, max_seq_len), diagonal=1).bool()
        self.register_buffer("causal_mask", causal)

    def forward(self, x: torch.Tensor,
                padding_mask: torch.Tensor = None) -> torch.Tensor:
        """
        Args:
            x: (B, T, embed_dim)
            padding_mask: (B, T) — True where token is PAD (should be masked)
        Returns:
            (B, T, embed_dim)
        """
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, H, T, T)

        # Apply causal mask (correct)
        causal = self.causal_mask[:T, :T]
        attn = attn.masked_fill(causal.unsqueeze(0).unsqueeze(0), float("-inf"))

        # BUG: padding mask NOT applied
        # Fix: if padding_mask is not None:
        #          # padding_mask: (B, T) -> expand to (B, 1, 1, T) to mask key positions
        #          pad = padding_mask.unsqueeze(1).unsqueeze(2)  # (B, 1, 1, T)
        #          attn = attn.masked_fill(pad, float("-inf"))

        attn = F.softmax(attn, dim=-1)
        # BUG: attn may have NaN when all keys are masked (all-inf row -> NaN after softmax)
        attn = torch.nan_to_num(attn, nan=0.0)

        out = attn @ v
        out = out.transpose(1, 2).reshape(B, T, C)
        return self.proj(out)


class TransformerBlock(nn.Module):
    def __init__(self, embed_dim: int = 32, num_heads: int = 4,
                 max_seq_len: int = 24):
        super().__init__()
        self.attn = CausalAttention(embed_dim, num_heads, max_seq_len)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, 2 * embed_dim), nn.GELU(),
            nn.Linear(2 * embed_dim, embed_dim),
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x, padding_mask=None):
        x = x + self.attn(self.norm1(x), padding_mask)
        x = x + self.ff(self.norm2(x))
        return x


class CausalLM(nn.Module):
    def __init__(self, vocab_size: int = 64, embed_dim: int = 32,
                 num_heads: int = 4, num_layers: int = 2,
                 max_seq_len: int = 24):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_TOKEN_ID)
        self.pos_emb = nn.Embedding(max_seq_len, embed_dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, max_seq_len)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)

    def forward(self, input_ids: torch.Tensor,
                padding_mask: torch.Tensor = None) -> torch.Tensor:
        B, T = input_ids.shape
        pos = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = self.token_emb(input_ids) + self.pos_emb(pos)
        for block in self.blocks:
            x = block(x, padding_mask)
        x = self.norm(x)
        return self.lm_head(x)
