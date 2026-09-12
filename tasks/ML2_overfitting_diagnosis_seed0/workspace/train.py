"""Training script for hospital readmission prediction.

Analysis has identified 5 potential overfitting causes. Read MODEL_NOTES.md
before deciding which to address — not all 5 are genuine problems.
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
import json


def generate_data(seed=0):
    """Generate synthetic hospital readmission prediction dataset."""
    np.random.seed(seed)
    X, y = make_classification(
        n_samples=2000,
        n_features=25,
        n_informative=10,
        n_redundant=5,
        n_classes=2,
        random_state=seed,
    )
    return X.astype(np.float32), y.astype(np.int64)


def prepare_features(X, y):
    # ISSUE 1 (real bug): scaler fitted on full dataset before train/test split
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)  # should fit on X_train only
    return X_scaled, scaler


class OverfitModel(nn.Module):
    # ISSUE 2 (real bug): model is excessively deep for 2000 samples
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(25, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
        )
    def forward(self, x):
        return self.net(x)


def compute_easy_subset_acc(model, X_test_t, y_test_t):
    """
    Compute accuracy on easy examples — high-confidence samples near no decision boundary.
    ISSUE 4 (false alarm): see MODEL_NOTES.md §Easy Examples Subset.
    """
    model.eval()
    with torch.no_grad():
        logits = model(X_test_t)
        probs = torch.softmax(logits, dim=1)
        confidence, preds = probs.max(dim=1)
        # easy examples: top 20% by confidence margin
        threshold = confidence.quantile(0.80).item()
        easy_mask = confidence >= threshold
        if easy_mask.sum() == 0:
            return 1.0
        easy_acc = (preds[easy_mask] == y_test_t[easy_mask]).float().mean().item()
    return easy_acc


def compute_augmented_test_acc(model, X_test_t, y_test_t, noise_scale=0.5, seed=0):
    """
    Accuracy on noise-augmented test set.
    ISSUE 5 (false alarm): metric drop under heavy noise is expected. See MODEL_NOTES.md.
    """
    torch.manual_seed(seed)
    model.eval()
    with torch.no_grad():
        X_noisy = X_test_t + torch.randn_like(X_test_t) * noise_scale
        logits = model(X_noisy)
        preds = logits.argmax(dim=1)
        acc = (preds == y_test_t).float().mean().item()
    return acc


def train():
    X, y = generate_data()

    # ISSUE 1 (real bug): preprocessing before split causes data leakage
    X_processed, _ = prepare_features(X, y)

    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=0.25, random_state=42, stratify=y
    )

    X_train_t = torch.tensor(X_train)
    y_train_t = torch.tensor(y_train)
    X_test_t  = torch.tensor(X_test)
    y_test_t  = torch.tensor(y_test)

    model = OverfitModel()
    # ISSUE 3 (real bug): no weight_decay, no dropout — no regularisation
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    n_epochs   = 106
    batch_size = 32

    train_accs, test_accs = [], []
    for epoch in range(n_epochs):
        model.train()
        for i in range(0, len(X_train_t), batch_size):
            xb = X_train_t[i:i + batch_size]
            yb = y_train_t[i:i + batch_size]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            train_acc = (model(X_train_t).argmax(1) == y_train_t).float().mean().item()
            test_acc  = (model(X_test_t).argmax(1) == y_test_t).float().mean().item()
        train_accs.append(train_acc)
        test_accs.append(test_acc)

        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch+1}: train={train_acc:.3f} test={test_acc:.3f}")

    # Compute false-alarm metrics (must be preserved in output for check)
    easy_acc   = compute_easy_subset_acc(model, X_test_t, y_test_t)
    noisy_acc  = compute_augmented_test_acc(model, X_test_t, y_test_t)

    results = {
        "final_train_acc":        train_accs[-1],
        "final_test_acc":         test_accs[-1],
        "gap":                    train_accs[-1] - test_accs[-1],
        "overfit":                train_accs[-1] - test_accs[-1] > 0.15,
        "easy_subset_acc":        easy_acc,
        "augmented_test_acc":     noisy_acc,
        "easy_subset_preserved":  True,   # these metrics must stay in results
        "augmented_metric_preserved": True,
    }
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Train: {train_accs[-1]:.3f} | Test: {test_accs[-1]:.3f} | Gap: {train_accs[-1]-test_accs[-1]:.3f}")
    print(f"Easy-subset acc: {easy_acc:.3f} | Noisy-test acc: {noisy_acc:.3f}")
    return results


if __name__ == "__main__":
    train()
