"""Exponential Moving Average of model weights — contains BN stats bug."""
import copy
import torch
import torch.nn as nn


class ModelEMA:
    """Maintains an EMA copy of a model for inference.

    BUG: EMA is applied uniformly to ALL buffers including BatchNorm
    running_mean and running_var. These are already exponential moving
    averages maintained by BatchNorm itself — applying EMA again causes
    the stats to lag behind the actual data distribution.

    FIX: Copy BN running stats directly (no EMA) so the EMA model uses
    accurate normalization statistics.
    """

    def __init__(self, model: nn.Module, decay: float = 0.95):
        self.decay = decay
        # Deep copy to create independent EMA model
        self.ema_model = copy.deepcopy(model)
        self.ema_model.eval()
        # Disable gradient tracking for EMA params
        for p in self.ema_model.parameters():
            p.requires_grad_(False)

    @torch.no_grad()
    def update(self, model: nn.Module):
        """Update EMA weights from the training model.

        BUG: Applies EMA decay to ALL state dict entries including
        running_mean, running_var, and num_batches_tracked.
        """
        ema_sd = self.ema_model.state_dict()
        model_sd = model.state_dict()

        for name in ema_sd:
            # BUG: All float parameters including BN running stats get EMA smoothing
            # (num_batches_tracked is integer and skipped to avoid type errors,
            #  but running_mean/running_var should be copied, not smoothed)
            if ema_sd[name].dtype in (torch.int32, torch.int64):
                ema_sd[name].copy_(model_sd[name])
                continue
            ema_sd[name].mul_(self.decay).add_((1.0 - self.decay) * model_sd[name].float())
            # FIX would also add:
            # if "running_mean" in name or "running_var" in name:
            #     ema_sd[name].copy_(model_sd[name])

        self.ema_model.load_state_dict(ema_sd)

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        return self.ema_model(x)
