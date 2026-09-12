"""NT-Xent (SimCLR) contrastive loss -- contains positive-in-negatives bug."""
import torch
import torch.nn.functional as F


def nt_xent_loss(z1: torch.Tensor, z2: torch.Tensor, temperature: float = 0.1) -> torch.Tensor:
    """NT-Xent loss for SimCLR.

    Args:
        z1: (N, D) projections for first augmentation
        z2: (N, D) projections for second augmentation
        temperature: softmax temperature

    BUG: The positive pair is included in the negative denominator.
    The mask only removes the diagonal (self-similarity) but keeps
    z1[i] vs z2[i] (and z2[i] vs z1[i]) as negatives when computing
    the denominator for the other view.

    Correct behavior: for sample i's positive pair (i, i+N), BOTH
    the diagonal and the positive partner must be excluded from the denominator.
    """
    N = z1.size(0)

    # Normalize
    z1 = F.normalize(z1, dim=1)
    z2 = F.normalize(z2, dim=1)

    # Concatenate: [z1; z2] shape (2N, D)
    z = torch.cat([z1, z2], dim=0)

    # Similarity matrix (2N, 2N)
    sim = torch.mm(z, z.t()) / temperature

    # Positive pair indices:
    # For i in [0, N): positive is i + N
    # For i in [N, 2N): positive is i - N
    pos_mask = torch.zeros(2 * N, 2 * N, dtype=torch.bool, device=z.device)
    for i in range(N):
        pos_mask[i, i + N] = True
        pos_mask[i + N, i] = True

    # BUG: Negative mask only excludes diagonal (self-similarity)
    # It does NOT exclude the positive pair, so positives are treated as negatives
    neg_mask = ~torch.eye(2 * N, dtype=torch.bool, device=z.device)
    # CORRECT would be:
    # neg_mask = ~torch.eye(2*N, dtype=torch.bool, device=z.device) & ~pos_mask

    # Numerator: similarity to positive pair
    pos_sim = sim[pos_mask].view(2 * N)  # (2N,)

    # Denominator: sum over negatives (BUG: includes positive partner)
    neg_sim = sim * neg_mask.float()  # zero out self
    denom = torch.logsumexp(neg_sim + (~neg_mask).float() * (-1e9), dim=1)

    loss = -(pos_sim - denom).mean()
    return loss
