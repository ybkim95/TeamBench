"""BERT-style classifier — contains wrong pooling strategy bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class BertEncoder(nn.Module):
    """Pretrained BERT-style encoder.

    Pretraining uses CLS token (position 0) for sequence-level tasks.
    The CLS token is specially trained to aggregate sequence information.
    """

    def __init__(self, vocab_size: int = 80, embed_dim: int = 48,
                 num_heads: int = 4, num_layers: int = 2,
                 max_seq_len: int = 22):
        super().__init__()
        # CLS token is prepended at position 0 during pretraining
        self.token_emb = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.pos_emb = nn.Embedding(max_seq_len, embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads,
            dim_feedforward=embed_dim * 2, batch_first=True, dropout=0.0
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(embed_dim)

        # CLS token embedding (index 1 in vocab, reserved)
        self.cls_token_id = 1

    def forward(self, input_ids: torch.Tensor,
                attention_mask: torch.Tensor = None) -> torch.Tensor:
        """
        Args:
            input_ids: (B, seq_len) token ids — first token is CLS (id=1)
            attention_mask: (B, seq_len) — 1 for real tokens, 0 for padding
        Returns:
            (B, seq_len, embed_dim) encoder output
        """
        B, T = input_ids.shape
        pos = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = self.token_emb(input_ids) + self.pos_emb(pos)

        if attention_mask is not None:
            # TransformerEncoder expects key_padding_mask: True = masked (pad)
            key_padding_mask = (attention_mask == 0)
        else:
            key_padding_mask = None

        x = self.encoder(x, src_key_padding_mask=key_padding_mask)
        return self.norm(x)


class BertClassifier(nn.Module):
    """Fine-tuned BERT classifier.

    BUG: Uses mean pooling over all tokens instead of CLS token (position 0).

    The pretrained encoder was trained with CLS token at position 0 aggregating
    sequence-level information. Fine-tuning MUST use CLS token pooling to
    leverage the pretrained representation.

    Mean pooling:
    - Averages ALL token representations including padding tokens
    - Dilutes the CLS signal with non-representative token embeddings
    - The pooled vector was never seen during pretraining

    Correct: pooled = encoder_output[:, 0, :]  # CLS token
    """

    def __init__(self, vocab_size: int = 80, embed_dim: int = 48,
                 num_heads: int = 4, num_layers: int = 2,
                 num_classes: int = 5, max_seq_len: int = 22):
        super().__init__()
        self.encoder = BertEncoder(vocab_size, embed_dim, num_heads, num_layers, max_seq_len)
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.Tanh(),
            nn.Linear(embed_dim, num_classes),
        )

    def forward(self, input_ids: torch.Tensor,
                attention_mask: torch.Tensor = None) -> torch.Tensor:
        """
        Args:
            input_ids: (B, seq_len) — first token is CLS (id=1)
            attention_mask: (B, seq_len)
        Returns:
            (B, num_classes) logits
        """
        enc_out = self.encoder(input_ids, attention_mask)  # (B, T, D)

        # BUG: mean pooling — wrong for CLS-pretrained model
        # Should be: pooled = enc_out[:, 0, :]  # CLS token at position 0
        if attention_mask is not None:
            # Mean pool over non-padding tokens (still wrong for CLS model)
            mask = attention_mask.unsqueeze(-1).float()
            pooled = (enc_out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        else:
            pooled = enc_out.mean(dim=1)  # BUG: should be enc_out[:, 0, :]

        return self.classifier(pooled)
