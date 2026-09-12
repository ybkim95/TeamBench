"""Model with dropout for shadow deployment evaluation."""
import torch
import torch.nn as nn


class DropoutClassifier(nn.Module):
    """Classifier with dropout layers.

    IMPORTANT: This model behaves differently in train() vs eval() mode:
    - train() mode: dropout is ACTIVE (random neuron deactivation)
    - eval() mode: dropout is DISABLED (deterministic, full capacity)

    Shadow evaluation MUST use eval() mode for fair comparison with production.
    """

    def __init__(self, input_dim: int = 24, hidden_dim: int = 48,
                 num_classes: int = 3, dropout_rate: float = 0.5):
        super().__init__()
        self.dropout_rate = dropout_rate
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def is_in_eval_mode(self) -> bool:
        return not self.training
