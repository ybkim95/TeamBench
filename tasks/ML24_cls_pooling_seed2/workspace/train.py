"""Fine-tuning script for BERT-style classifier."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import BertClassifier


CLS_TOKEN_ID = 1
PAD_TOKEN_ID = 0
MAX_SEQ_LEN = 16  # +1 for CLS, +1 buffer


def get_data():
    torch.manual_seed(42)
    # Generate sequences with CLS token prepended
    raw = torch.randint(2, 96, (528, 14))
    # Prepend CLS token
    cls = torch.full((528, 1), CLS_TOKEN_ID, dtype=torch.long)
    sequences = torch.cat([cls, raw], dim=1)  # (N, seq_len+1)
    # Attention mask: all real tokens
    mask = torch.ones_like(sequences)

    # Labels: based on CLS-position feature (simulates pretraining signal)
    # The CLS token embedding at position 0 captures sequence-level info
    # Class = sum of first 3 real tokens mod num_classes
    labels = (raw[:, :3].sum(dim=1) % 3).long()

    n_train = int(528 * 0.8)
    return (sequences[:n_train], mask[:n_train], labels[:n_train],
            sequences[n_train:], mask[n_train:], labels[n_train:])


def train():
    torch.manual_seed(0)
    X_tr, mask_tr, y_tr, X_v, mask_v, y_v = get_data()
    model = BertClassifier(
        vocab_size=96, embed_dim=64,
        num_heads=4, num_layers=3,
        num_classes=3, max_seq_len=MAX_SEQ_LEN
    )
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_tr)
    history = []
    for epoch in range(21):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = indices[i:i + 16]
            xb, mb, yb = X_tr[idx], mask_tr[idx], y_tr[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb, mb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_acc = (model(X_v, mask_v).argmax(1) == y_v).float().mean().item()

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
