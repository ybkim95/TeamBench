"""Shadow deployment evaluation — BUG: shadow model uses train() mode."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import DropoutClassifier


def get_data():
    torch.manual_seed(42)
    n = 628 + 323 + 221
    X = torch.randn(n, 24)
    W = torch.randn(24, 3)
    y = (X @ W).argmax(1)
    return (X[:628], y[:628],
            X[628:628+323], y[628:628+323],
            X[628+323:], y[628+323:])


def train_model(X_train, y_train, seed_offset: int = 0):
    torch.manual_seed(seed_offset)
    model = DropoutClassifier(input_dim=24, hidden_dim=48,
                               num_classes=3, dropout_rate=0.5)
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.CrossEntropyLoss()
    n = len(X_train)
    for epoch in range(17):
        model.train()
        for i in range(0, n, 64):
            xb = X_train[i:i+64]
            yb = y_train[i:i+64]
            optimizer.zero_grad()
            criterion(model(xb), yb).backward()
            optimizer.step()
    return model


def compute_metrics(model, X, y):
    """Compute accuracy and mean confidence in current model mode."""
    with torch.no_grad():
        logits = model(X)
        probs = logits.softmax(dim=-1)
        acc = (logits.argmax(1) == y).float().mean().item()
        conf = probs.max(dim=1).values.mean().item()
    return {"accuracy": round(acc, 4), "mean_confidence": round(conf, 4)}


def run_shadow_evaluation():
    """Run shadow deployment evaluation comparing production vs shadow model.

    BUG: shadow_model is placed in train() mode during evaluation.
    With dropout_rate=0.5, this degrades shadow model accuracy artificially.
    The comparison shows shadow model as worse, even if it\'s the same architecture.

    Fix: Set shadow_model.eval() before evaluation (same as prod_model).
    """
    X_train, y_train, X_test, y_test, X_shadow, y_shadow = get_data()

    print("Training production model...")
    prod_model = train_model(X_train, y_train, seed_offset=0)
    print("Training shadow model...")
    shadow_model = train_model(X_train, y_train, seed_offset=1)

    # Production model: correct eval mode
    prod_model.eval()

    # BUG: shadow model in train mode — dropout active during evaluation
    shadow_model.train()  # BUG: should be shadow_model.eval()

    prod_metrics = compute_metrics(prod_model, X_shadow, y_shadow)
    shadow_metrics = compute_metrics(shadow_model, X_shadow, y_shadow)

    # Check if shadow model wins (if dropout is active, it should lose unfairly)
    shadow_wins = shadow_metrics["accuracy"] > prod_metrics["accuracy"]

    # Correct evaluation (for reference)
    shadow_model.eval()
    shadow_metrics_correct = compute_metrics(shadow_model, X_shadow, y_shadow)
    shadow_model.train()  # restore buggy state

    results = {
        "production": prod_metrics,
        "shadow_buggy": shadow_metrics,       # with dropout (unfair)
        "shadow_correct": shadow_metrics_correct,  # without dropout (fair)
        "shadow_wins_unfair": shadow_wins,
        "shadow_wins_fair": shadow_metrics_correct["accuracy"] > prod_metrics["accuracy"],
        "eval_mode_match": False,  # BUG: should be True
        "prod_in_eval": True,
        "shadow_in_eval": False,   # BUG: should be True
    }
    with open("shadow_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Production  (eval): acc={prod_metrics['accuracy']:.4f}, conf={prod_metrics['mean_confidence']:.4f}")
    print(f"Shadow (train/BUG): acc={shadow_metrics['accuracy']:.4f}, conf={shadow_metrics['mean_confidence']:.4f}")
    print(f"Shadow  (eval/ref): acc={shadow_metrics_correct['accuracy']:.4f}, conf={shadow_metrics_correct['mean_confidence']:.4f}")
    print(f"Eval mode match: {results['eval_mode_match']}")
    return results


if __name__ == "__main__":
    run_shadow_evaluation()
