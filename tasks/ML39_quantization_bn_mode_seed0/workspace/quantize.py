"""Quantization pipeline — BUG: model.train() during calibration."""
import json
import sys
import os
import copy
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import BNClassifier


def get_data():
    torch.manual_seed(42)
    n_total = 797 + 197 + 307
    X = torch.randn(n_total, 3, 16, 16)
    # Labels based on first conv feature
    W = torch.randn(3 * 16 * 16, 5)
    flat = X.view(n_total, -1)
    y = (flat @ W).argmax(1)
    return (X[:797], y[:797],
            X[797:797+197], y[797:797+197],
            X[797+197:], y[797+197:])


def train_model(X_train, y_train):
    torch.manual_seed(0)
    model = BNClassifier(num_classes=5, in_channels=3,
                          hidden_channels=32)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()
    n = len(X_train)
    for epoch in range(18):
        model.train()
        for i in range(0, n, 16):
            xb = X_train[i:i+16]
            yb = y_train[i:i+16]
            optimizer.zero_grad()
            criterion(model(xb), yb).backward()
            optimizer.step()
        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                acc = (model(X_train).argmax(1) == y_train).float().mean().item()
            print(f"Epoch {epoch+1}/{18} | train_acc={acc:.4f}")
    return model


def simulate_quantization(model, calib_x):
    """Simulate PTQ by clipping activations to estimated ranges (simplified)."""
    # Record activation ranges during calibration
    ranges = {}
    hooks = []

    def make_hook(name):
        def hook(module, inp, out):
            with torch.no_grad():
                ranges[name] = (out.min().item(), out.max().item())
        return hook

    for name, module in model.named_modules():
        if isinstance(module, (nn.ReLU, nn.BatchNorm2d, nn.BatchNorm1d)):
            hooks.append(module.register_forward_hook(make_hook(name)))

    with torch.no_grad():
        for i in range(0, len(calib_x), 16):
            model(calib_x[i:i+16])

    for h in hooks:
        h.remove()

    # Apply simulated quantization: clip+round activations to 8-bit grid
    quant_model = copy.deepcopy(model)
    quant_model.eval()

    def make_quant_hook(rng_min, rng_max):
        def hook(module, inp, out):
            scale = (rng_max - rng_min) / 255.0 if rng_max != rng_min else 1e-6
            quantized = torch.clamp(out, rng_min, rng_max)
            quantized = torch.round(quantized / scale) * scale
            return quantized
        return hook

    for name, module in quant_model.named_modules():
        if name in ranges and isinstance(module, (nn.ReLU, nn.BatchNorm2d, nn.BatchNorm1d)):
            rng_min, rng_max = ranges[name]
            module.register_forward_hook(make_quant_hook(rng_min, rng_max))

    return quant_model, ranges


def calibrate_model(model, calib_x):
    """Calibrate model for quantization.

    BUG: Model is put in train() mode during calibration.
    BatchNorm layers use batch statistics (noisy) instead of running statistics (stable).
    This makes activation ranges inaccurate, degrading quantized model accuracy.

    Fix: Use model.eval() before calibration loop.
    """
    # BUG: train mode during calibration — BN uses noisy batch stats
    model.train()  # BUG: should be model.eval()
    return simulate_quantization(model, calib_x)


def evaluate(model, X, y):
    model.eval()
    with torch.no_grad():
        acc = (model(X).argmax(1) == y).float().mean().item()
    return acc


def run():
    X_train, y_train, X_calib, y_calib, X_test, y_test = get_data()

    print("Training model...")
    model = train_model(X_train, y_train)

    fp32_acc = evaluate(model, X_test, y_test)
    print(f"FP32 test accuracy: {fp32_acc:.4f}")

    print("Calibrating for quantization...")
    quant_model, ranges = calibrate_model(model, X_calib)

    quant_acc = evaluate(quant_model, X_test, y_test)
    print(f"Quantized test accuracy: {quant_acc:.4f}")

    acc_drop = fp32_acc - quant_acc
    print(f"Accuracy drop: {acc_drop:+.4f}")

    results = {
        "fp32_accuracy": round(fp32_acc, 4),
        "quantized_accuracy": round(quant_acc, 4),
        "accuracy_drop": round(acc_drop, 4),
        "calibration_mode": "train",  # BUG: should be "eval"
        "quantization_ok": acc_drop < 0.10,
    }
    with open("quantization_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    run()
