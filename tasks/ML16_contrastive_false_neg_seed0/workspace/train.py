"""SimCLR-style contrastive pretraining + linear probe evaluation."""
import json, sys, os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nt_xent_loss import nt_xent_loss


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(32, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
        )
        self.projector = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
        )

    def forward(self, x):
        h = self.backbone(x)
        z = self.projector(h)
        return h, z


def augment(X, strength=0.1):
    """Simple augmentation: add Gaussian noise."""
    return X + strength * torch.randn_like(X)


def get_data():
    torch.manual_seed(42)
    # Labeled data with class structure for downstream evaluation
    centers = torch.randn(4, 32)
    X_list, y_list = [], []
    per_class = 697 // 4
    for c in range(4):
        X_list.append(centers[c] + 0.5 * torch.randn(per_class, 32))
        y_list.append(torch.full((per_class,), c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    perm = torch.randperm(len(X))
    X, y = X[perm], y[perm]
    n_train = int(len(X) * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def linear_probe_eval(encoder, X_train, y_train, X_val, y_val):
    """Evaluate learned representations with a linear classifier."""
    encoder.eval()
    with torch.no_grad():
        h_train, _ = encoder(X_train)
        h_val, _ = encoder(X_val)

    probe = nn.Linear(128, 4)
    opt = optim.LBFGS(probe.parameters(), lr=0.1, max_iter=100)
    criterion = nn.CrossEntropyLoss()

    def closure():
        opt.zero_grad()
        loss = criterion(probe(h_train.detach()), y_train)
        loss.backward()
        return loss

    opt.step(closure)

    with torch.no_grad():
        acc = (probe(h_val).argmax(1) == y_val).float().mean().item()
    return acc


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    encoder = Encoder()
    optimizer = optim.Adam(encoder.parameters(), lr=1e-3, weight_decay=1e-4)

    n_train = len(X_train)
    history = []
    for epoch in range(33):
        encoder.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb = X_train[idx]
            x1, x2 = augment(xb), augment(xb)
            optimizer.zero_grad()
            _, z1 = encoder(x1)
            _, z2 = encoder(x2)
            loss = nt_xent_loss(z1, z2, temperature=0.1)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        # Linear probe every 5 epochs
        if (epoch + 1) % 5 == 0:
            probe_acc = linear_probe_eval(encoder, X_train, y_train, X_val, y_val)
            history.append({"epoch": epoch+1, "loss": epoch_loss, "probe_acc": probe_acc})
            print(f"Epoch {epoch+1}/{33} loss={epoch_loss:.4f} probe_acc={probe_acc:.4f}")
        else:
            history.append({"epoch": epoch+1, "loss": epoch_loss, "probe_acc": None})

    final_acc = linear_probe_eval(encoder, X_train, y_train, X_val, y_val)
    results = {
        "final_probe_acc": final_acc,
        "converged": final_acc > 0.55,
        "history": [h for h in history if h["probe_acc"] is not None],
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final probe acc: {final_acc:.4f}")
    return results


if __name__ == "__main__":
    train()
