"""Sinusoidal positional encoding — contains frequency step bug."""
import torch
import torch.nn as nn
import math


class SinusoidalPE(nn.Module):
    """Sinusoidal positional encoding (Vaswani et al., 2017).

    BUG: The frequency arange uses step=1 instead of step=2.

    Correct: positions 2i and 2i+1 share the same frequency 1/10000^(2i/d_model)
      -> arange(0, d_model, step=2) gives indices [0, 2, 4, ..., d_model-2]
         each index i gives frequency 1/10000^(i/d_model)

    Buggy: step=1 gives arange [0, 1, 2, ..., d_model-1]
      -> every dimension gets a different frequency 1/10000^(i/d_model)
      -> sin/cos pairs are NOT at the same frequency
      -> positional encoding does not have the correct geometric frequency structure
    """

    def __init__(self, embed_dim: int = 64, max_len: int = 64,
                 dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, embed_dim)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)

        # BUG: step=1 — every dim gets unique frequency instead of sin/cos pairs
        # Correct: step=2 so that dim 2i and 2i+1 share frequency i
        div_term = torch.exp(
            torch.arange(0, embed_dim, step=1).float()  # BUG: should be step=2
            * (-math.log(10000.0) / embed_dim)
        )

        # BUG: With step=1, div_term has embed_dim elements but we assign to
        # alternating positions — this creates wrong frequency bands
        pe[:, 0::2] = torch.sin(position * div_term[:embed_dim // 2 + embed_dim % 2])
        pe[:, 1::2] = torch.cos(position * div_term[:embed_dim // 2])

        pe = pe.unsqueeze(0)  # (1, max_len, embed_dim)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, seq_len, embed_dim)"""
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)
