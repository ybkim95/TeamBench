"""Training loop for sequence token-type classification with label smoothing."""
import json, sys, os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smooth_loss import LabelSmoothingLoss

# Token type classification: each token maps to a class based on its value.
# PAD tokens (index 0) should be ignored in both input and loss.
NUM_CLASSES = 5


class TokenClassifier(nn.Module):
    """Classifies each token position into one of NUM_CLASSES types."""
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(80, 96, padding_idx=0)
        self.lstm = nn.LSTM(96, 96, batch_first=True)
        self.proj = nn.Linear(96, NUM_CLASSES)

    def forward(self, x):
        emb = self.embed(x)
        out, _ = self.lstm(emb)
        return self.proj(out)


def get_data():
    torch.manual_seed(42)
    # Sequences with PAD padding at the end
    X = torch.randint(1, 80, (568, 16))
    for i in range(568):
        pad_start = torch.randint(16//2, 16, (1,)).item()
        X[i, pad_start:] = 0
    # Labels: deterministic token type = (token_value - 1) // (80 // NUM_CLASSES)
    # PAD positions get label 0 (will be masked in loss)
    y = torch.clamp((X - 1) // max(1, (80 - 1) // NUM_CLASSES), 0, NUM_CLASSES - 1)
    y[X == 0] = 0  # mark PAD positions with pad_idx as target
    n_train = int(568 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def compute_accuracy(logits_flat, targets_flat, pad_idx):
    """Accuracy ignoring PAD positions."""
    mask = targets_flat != pad_idx
    if mask.sum() == 0:
        return 0.0
    preds = logits_flat.argmax(-1)
    return (preds[mask] == targets_flat[mask]).float().mean().item()


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = TokenClassifier()
    criterion = LabelSmoothingLoss(vocab_size=NUM_CLASSES, pad_idx=0, epsilon=0.1)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    n_train = len(X_train)
    history = []
    for epoch in range(22):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            logits = model(xb)  # (B, seq_len, NUM_CLASSES)
            B, S, V = logits.shape
            loss = criterion(logits.view(B*S, V), yb.view(B*S))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            B, S, V = val_logits.shape
            val_acc = compute_accuracy(val_logits.view(B*S, V), y_val.view(B*S), 0)

        history.append({"epoch": epoch+1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch+1) % 5 == 0:
            print(f"Epoch {epoch+1}/{22} loss={epoch_loss:.4f} val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.60,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
