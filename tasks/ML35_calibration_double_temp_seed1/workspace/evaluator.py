"""Evaluator / inference pipeline — BUG: applies temperature scaling again."""
import torch
import torch.nn.functional as F
import numpy as np
from model import CalibratedClassifier


class ModelEvaluator:
    """Evaluator that computes calibration metrics.

    BUG: This class applies temperature scaling to model outputs,
    but model.forward() already scales by temperature. Double scaling
    makes probabilities over-smooth (too uniform), increasing ECE.

    Fix: Remove the temperature division from either model.forward()
    OR from this evaluator's predict_proba() method.
    """

    def __init__(self, model: CalibratedClassifier):
        self.model = model
        self.temperature = model.temperature

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Get calibrated probabilities.

        BUG: Divides by self.temperature again even though model.forward()
        already divided by temperature.
        """
        self.model.eval()
        with torch.no_grad():
            logits = self.model(x)  # already divided by T in model.forward()
            # BUG: dividing by temperature again → effective temperature = T^2
            scaled_logits = logits / self.temperature
            return F.softmax(scaled_logits, dim=-1)

    def compute_ece(self, x: torch.Tensor, y: torch.Tensor, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error (ECE)."""
        probs = self.predict_proba(x)
        confidences, predictions = probs.max(dim=1)
        accuracies = predictions.eq(y)

        ece = 0.0
        bin_boundaries = torch.linspace(0, 1, n_bins + 1)
        for i in range(n_bins):
            lower, upper = bin_boundaries[i], bin_boundaries[i + 1]
            in_bin = (confidences > lower) & (confidences <= upper)
            prop_in_bin = in_bin.float().mean()
            if prop_in_bin > 0:
                acc_in_bin = accuracies[in_bin].float().mean()
                avg_conf_in_bin = confidences[in_bin].mean()
                ece += (avg_conf_in_bin - acc_in_bin).abs() * prop_in_bin
        return ece.item()

    def compute_accuracy(self, x: torch.Tensor, y: torch.Tensor) -> float:
        probs = self.predict_proba(x)
        preds = probs.argmax(dim=1)
        return (preds == y).float().mean().item()
