"""Multi-task trainer with inverse-loss weighting — contains instability bug."""
import torch
import torch.nn as nn


class MultiTaskTrainer:
    """Trainer using 1/loss weighting for automatic task balancing.

    The idea: tasks with smaller loss (already mastered) get lower weight,
    so the model focuses on harder tasks. But this creates a bug:

    BUG: When task_loss -> 0, weight = 1/task_loss -> inf.
    This causes gradient explosion and NaN losses.

    Additionally, using the LIVE loss (not detached) for weighting
    creates a pathological gradient path: the weight itself depends on
    the loss, creating a higher-order gradient term that's unstable.

    Fix: use 1/(task_loss.detach() + epsilon) to:
    1. Detach from gradient graph (weights are constants, not differentiable)
    2. Add epsilon to prevent division by zero
    """

    def __init__(self, n_tasks: int = 2, epsilon: float = 0.1):
        self.n_tasks = n_tasks
        self.epsilon = epsilon

    def weighted_loss(self, task_losses: list) -> torch.Tensor:
        """Combine task losses with inverse-loss weighting.

        Args:
            task_losses: list of scalar tensors, one per task

        BUG: uses 1/loss without epsilon and without detaching.
        This explodes when any task_loss approaches 0.
        """
        weights = []
        for loss in task_losses:
            # BUG: no epsilon, no detach — explodes as loss -> 0
            w = 1.0 / loss
            # CORRECT would be:
            # w = 1.0 / (loss.detach() + self.epsilon)
            weights.append(w)

        # Normalize weights so they sum to n_tasks
        weight_sum = sum(weights)
        weights = [w / weight_sum * self.n_tasks for w in weights]

        total = sum(w * l for w, l in zip(weights, task_losses))
        return total
