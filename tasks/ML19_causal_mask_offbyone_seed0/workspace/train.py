"""Training script for causal language model."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CausalLM


def get_data():
    torch.manual_seed(42)
    # Simple pattern: predict next token in repeating sequences
    # Tokens follow a deterministic pattern: token[t+1] = (token[t] + 1) % period
    period = 8
    seqs = []
    for i in range(597):
        start = torch.randint(0, period, (1,)).item()
        seq = [(start + t) % period for t in range(16 + 1)]
        seqs.append(seq)
    data = torch.tensor(seqs, dtype=torch.long)
    n_train = int(597 * 0.8)
    return data[:n_train, :-1], data[:n_train, 1:], data[n_train:, :-1], data[n_train:, 1:]


def compute_accuracy(logits, targets):
    preds = logits.argmax(-1)
    return (preds == targets).float().mean().item()


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = CausalLM(
        vocab_size=64, embed_dim=32,
        num_heads=4, num_layers=2, seq_len=16
    )
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    history = []
    for epoch in range(21):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = indices[i:i + 16]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            logits = model(xb)
            B, T, V = logits.shape
            loss = criterion(logits.reshape(B * T, V), yb.reshape(B * T))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            B, T, V = val_logits.shape
            val_acc = compute_accuracy(val_logits.reshape(B * T, V), y_val.reshape(B * T))

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{21} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.55,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
