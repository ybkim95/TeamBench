"""Training script for causal LM with padded batches."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CausalLM, PAD_TOKEN_ID


def get_data():
    torch.manual_seed(42)
    period = 8
    seqs = []
    lengths = []
    max_len = 32
    for i in range(468):
        # Variable length: min_len to max_len
        length = torch.randint(max_len // 2, max_len, (1,)).item()
        start = torch.randint(0, period, (1,)).item()
        seq = [(start + t) % period + 1 for t in range(length + 1)]  # +1 offset to avoid PAD=0
        # Pad to max_len
        padded = seq[:max_len + 1] + [PAD_TOKEN_ID] * max(0, max_len + 1 - len(seq))
        seqs.append(padded[:max_len + 1])
        lengths.append(min(length, max_len))
    data = torch.tensor(seqs, dtype=torch.long)
    lengths = torch.tensor(lengths, dtype=torch.long)

    x_data = data[:, :-1]
    y_data = data[:, 1:]
    # Padding mask: True where token is PAD
    pad_mask = (x_data == PAD_TOKEN_ID)

    n_train = int(468 * 0.8)
    return (x_data[:n_train], y_data[:n_train], pad_mask[:n_train], lengths[:n_train],
            x_data[n_train:], y_data[n_train:], pad_mask[n_train:], lengths[n_train:])


def masked_ce_loss(logits, targets, pad_mask):
    """Cross-entropy loss masking PAD target positions."""
    B, T, V = logits.shape
    loss_flat = nn.functional.cross_entropy(
        logits.reshape(B * T, V), targets.reshape(B * T),
        ignore_index=PAD_TOKEN_ID, reduction='mean'
    )
    return loss_flat


def train():
    torch.manual_seed(0)
    x_tr, y_tr, mask_tr, len_tr, x_v, y_v, mask_v, len_v = get_data()
    model = CausalLM(
        vocab_size=80, embed_dim=48,
        num_heads=4, num_layers=2, max_seq_len=32
    )
    optimizer = optim.Adam(model.parameters(), lr=0.002)

    n_train = len(x_tr)
    history = []
    for epoch in range(24):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = indices[i:i + 16]
            xb, yb, mb = x_tr[idx], y_tr[idx], mask_tr[idx]
            optimizer.zero_grad()
            logits = model(xb, mb)
            loss = masked_ce_loss(logits, yb, mb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(x_v, mask_v)
            B, T, V = val_logits.shape
            preds = val_logits.argmax(-1)
            real = y_v != PAD_TOKEN_ID
            val_acc = (preds[real] == y_v[real]).float().mean().item() if real.sum() > 0 else 0.0

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{24} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.50,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
