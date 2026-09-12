"""LR scheduler with warmup + cosine decay."""
import math


class WarmupCosineScheduler:
    """Linear warmup followed by cosine annealing.

    BUG: The warmup and cosine decay are composed in the wrong order.
    The cosine decay is computed over total_steps, then warmup scaling
    is applied on top — this means after warmup ends, the LR jumps
    discontinuously and never decays smoothly from base_lr.
    """

    def __init__(self, optimizer, base_lr: float, warmup_steps: int, total_steps: int):
        self.optimizer = optimizer
        self.base_lr = base_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self._step = 0

    def step(self):
        self._step += 1
        lr = self.get_lr()
        for pg in self.optimizer.param_groups:
            pg["lr"] = lr

    def get_lr(self) -> float:
        step = self._step
        # BUG: Cosine decay computed over ALL steps first,
        # then warmup factor applied — wrong composition order.
        cosine_lr = 0.5 * self.base_lr * (
            1 + math.cos(math.pi * step / max(self.total_steps, 1))
        )
        if step < self.warmup_steps:
            # During warmup: scale the already-decayed value
            # This means warmup starts from ~base_lr (not 0) and ramps *down*
            return cosine_lr * (step / max(self.warmup_steps, 1))
        return cosine_lr

    def get_last_lr(self) -> float:
        return self.get_lr()

    @property
    def last_epoch(self):
        return self._step
