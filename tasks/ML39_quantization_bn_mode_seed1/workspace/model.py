"""CNN model with BatchNorm layers for quantization task."""
import torch
import torch.nn as nn


class BNClassifier(nn.Module):
    """CNN classifier with BatchNorm — used for quantization calibration demo.

    The BatchNorm layers are critical: in train() mode they use batch statistics
    (noisy), in eval() mode they use running statistics (stable).
    Quantization calibration MUST be done in eval() mode.
    """

    def __init__(self, num_classes: int = 4,
                 in_channels: int = 3,
                 hidden_channels: int = 24):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, hidden_channels, 3, padding=1),
            nn.BatchNorm2d(hidden_channels),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(hidden_channels, hidden_channels * 2, 3, padding=1),
            nn.BatchNorm2d(hidden_channels * 2),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(768, hidden_channels * 2),
            nn.BatchNorm1d(hidden_channels * 2),
            nn.ReLU(),
            nn.Linear(hidden_channels * 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))
