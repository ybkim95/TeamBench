"""Head pruning pipeline — BUG: prunes by weight magnitude, not importance."""
import json
import sys
import os
import copy
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import AttentionClassifier


def get_data():
    torch.manual_seed(42)
    n = 528 + 223 + 110
    X = torch.randn(n, 10, 8)
    centers = torch.randn(5, 8)
    dists = torch.cdist(X.mean(1), centers)
    y = dists.argmin(1)
    return (X[:528], y[:528],
            X[528:528+223], y[528:528+223],
            X[528+223:], y[528+223:])


def train_model(X_train, y_train):
    torch.manual_seed(0)
    model = AttentionClassifier(
        input_dim=8, embed_dim=64, num_heads=8,
        num_layers=2, num_classes=5, seq_len=10
    )
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.CrossEntropyLoss()
    n = len(X_train)
    for epoch in range(17):
        model.train()
        idx = torch.randperm(n)
        for i in range(0, n, 32):
            xb = X_train[idx[i:i+32]]
            yb = y_train[idx[i:i+32]]
            optimizer.zero_grad()
            criterion(model(xb), yb).backward()
            optimizer.step()
        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                acc = (model(X_train).argmax(1) == y_train).float().mean().item()
            print(f"Epoch {epoch+1}/{17} | acc={acc:.4f}")
    return model


def compute_head_importance_magnitude(model) -> list:
    """Compute head importance by weight L2 norm.

    BUG: Weight magnitude is a poor proxy for functional importance.
    Important heads may have small weights; unimportant heads may have large weights.
    Use gradient-based attribution instead.
    """
    importances = []
    for layer_idx, attn in enumerate(model.get_all_attention_modules()):
        norms = attn.get_head_weight_norms()
        for head_idx, norm in enumerate(norms):
            importances.append({
                "layer": layer_idx,
                "head": head_idx,
                "importance": norm.item(),
                "method": "magnitude",  # BUG: should be "gradient_attribution"
            })
    return importances


def compute_head_importance_gradient(model, X_calib, y_calib, criterion) -> list:
    """Compute head importance by gradient-weighted attribution (correct method).

    Importance score for head h = sum_i |grad(L, head_h_output_i) * head_h_output_i|
    This measures how much the loss changes when head h\'s output varies.
    Heads with high gradient-output product are important; prune those with low scores.
    """
    importances_grad = [{} for _ in range(16)]
    head_outputs = {}

    # Register hooks to capture head outputs and gradients
    hooks = []
    for layer_idx, attn in enumerate(model.get_all_attention_modules()):
        def make_hook(l_idx):
            def hook(module, inp, out):
                out.retain_grad()
                head_outputs[l_idx] = out
            return hook
        hooks.append(attn.register_forward_hook(make_hook(layer_idx)))

    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=0)  # no update, just grads
    optimizer.zero_grad()

    n_batches = min(4, len(X_calib) // 32 + 1)
    total_loss = 0
    for i in range(0, min(n_batches * 32, len(X_calib)), 32):
        xb = X_calib[i:i+32]
        yb = y_calib[i:i+32]
        loss = criterion(model(xb), yb)
        loss.backward()
        total_loss += loss.item()

    for h in hooks:
        h.remove()

    importances = []
    for layer_idx, attn in enumerate(model.get_all_attention_modules()):
        # Use gradient of q_proj weights as proxy for head importance
        q_grad = attn.q_proj.weight.grad
        if q_grad is None:
            for head_idx in range(8):
                importances.append({"layer": layer_idx, "head": head_idx,
                                     "importance": 0.0, "method": "gradient_attribution"})
            continue
        head_dim = attn.head_dim
        for head_idx in range(8):
            grad_h = q_grad[head_idx * head_dim:(head_idx + 1) * head_dim, :]
            score = grad_h.abs().sum().item()
            importances.append({
                "layer": layer_idx,
                "head": head_idx,
                "importance": score,
                "method": "gradient_attribution",
            })

    model.eval()
    return importances


def prune_model(model, importances: list, n_prune: int) -> list:
    """Prune the n_prune least important heads."""
    sorted_heads = sorted(importances, key=lambda x: x["importance"])
    heads_pruned = []
    attn_modules = model.get_all_attention_modules()
    for entry in sorted_heads[:n_prune]:
        layer, head = entry["layer"], entry["head"]
        attn_modules[layer].prune_heads([head])
        heads_pruned.append((layer, head))
    return heads_pruned


def evaluate(model, X, y):
    model.eval()
    with torch.no_grad():
        acc = (model(X).argmax(1) == y).float().mean().item()
    return acc


def run():
    X_train, y_train, X_test, y_test, X_calib, y_calib = get_data()
    criterion = nn.CrossEntropyLoss()

    print("Training model...")
    model = train_model(X_train, y_train)
    base_acc = evaluate(model, X_test, y_test)
    print(f"Base accuracy: {base_acc:.4f}")

    # Magnitude-based pruning (buggy)
    model_mag = copy.deepcopy(model)
    importances_mag = compute_head_importance_magnitude(model_mag)
    pruned_mag = prune_model(model_mag, importances_mag, n_prune=8)
    acc_mag = evaluate(model_mag, X_test, y_test)
    drop_mag = base_acc - acc_mag

    # Gradient-based pruning (reference — not used in main results — BUG)
    model_grad = copy.deepcopy(model)
    importances_grad = compute_head_importance_gradient(model_grad, X_calib, y_calib, criterion)
    pruned_grad = prune_model(model_grad, importances_grad, n_prune=8)
    acc_grad = evaluate(model_grad, X_test, y_test)
    drop_grad = base_acc - acc_grad

    print(f"Magnitude pruning: acc={acc_mag:.4f}, drop={drop_mag:+.4f}")
    print(f"Gradient pruning:  acc={acc_grad:.4f}, drop={drop_grad:+.4f}")

    results = {
        "base_accuracy": round(base_acc, 4),
        "magnitude_pruned_accuracy": round(acc_mag, 4),
        "gradient_pruned_accuracy": round(acc_grad, 4),
        "magnitude_drop": round(drop_mag, 4),
        "gradient_drop": round(drop_grad, 4),
        "n_heads_pruned": 8,
        "total_heads": 16,
        "pruning_method": "magnitude",    # BUG: should be "gradient_attribution"
        "pruning_ok": drop_mag < drop_grad,  # BUG: magnitude drop >= gradient drop
    }
    with open("pruning_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    run()
