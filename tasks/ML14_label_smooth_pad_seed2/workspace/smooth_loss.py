"""Label smoothing loss — contains PAD token bug."""
import torch
import torch.nn as nn
import torch.nn.functional as F


class LabelSmoothingLoss(nn.Module):
    """Cross-entropy with label smoothing.

    BUG 1: Smoothing mass is distributed over ALL vocab tokens including PAD (index 0).
            PAD is not a real output token and should receive 0 probability.

    BUG 2: Loss is NOT masked at positions where target == PAD_IDX.
            PAD positions should contribute 0 to the total loss.

    The effect: the model is trained to assign non-zero probability to PAD
    as an output token, and PAD target positions pollute the loss signal.
    """

    def __init__(self, vocab_size: int = 60, pad_idx: int = 0,
                 epsilon: float = 0.15):
        super().__init__()
        self.vocab_size = vocab_size
        self.pad_idx = pad_idx
        self.epsilon = epsilon

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: (batch * seq_len, vocab_size) raw logits
            targets: (batch * seq_len,) integer token ids
        Returns:
            scalar loss
        """
        B = logits.size(0)
        log_probs = F.log_softmax(logits, dim=-1)

        # BUG: smooth_dist assigns mass to ALL tokens including PAD
        # Correct: smooth_dist should be 0 at pad_idx position
        smooth_dist = torch.full(
            (B, self.vocab_size),
            self.epsilon / (self.vocab_size - 1),  # BUG: should be vocab_size - 2 (exclude PAD)
            device=logits.device
        )
        smooth_dist.scatter_(1, targets.unsqueeze(1), 1.0 - self.epsilon)
        # BUG: smooth_dist[pad_idx] is non-zero — should be zeroed out
        # smooth_dist[:, self.pad_idx] = 0.0  # <-- missing fix

        loss = -(smooth_dist * log_probs).sum(dim=-1)  # (B,)

        # BUG: loss is NOT masked at PAD target positions
        # pad_mask = (targets != self.pad_idx).float()  # <-- missing
        # loss = (loss * pad_mask).sum() / pad_mask.sum().clamp(min=1)  # <-- missing
        return loss.mean()
