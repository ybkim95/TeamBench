"""Training script for encoder-decoder model."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cross_attention import EncoderLayer, DecoderLayer


class EncoderDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.src_embed = nn.Embedding(32, 32)
        self.tgt_embed = nn.Embedding(32, 32)
        self.encoder = nn.ModuleList([EncoderLayer() for _ in range(2)])
        self.decoder = nn.ModuleList([DecoderLayer() for _ in range(2)])
        self.lm_head = nn.Linear(32, 32)

    def forward(self, src, tgt):
        enc = self.src_embed(src)
        for layer in self.encoder:
            enc = layer(enc)
        dec = self.tgt_embed(tgt)
        for layer in self.decoder:
            dec = layer(dec, enc)
        return self.lm_head(dec)


def get_data():
    torch.manual_seed(42)
    # Copy task: target = source (shifted by 1, reversed prefix)
    period = 8
    src = torch.randint(1, period, (597, 12))
    # Target is first tgt_len tokens of src in reverse
    tgt_in = src[:, ::-1][:, :8]
    tgt_out = torch.cat([tgt_in[:, 1:], torch.ones(597, 1, dtype=torch.long)], dim=1)
    n_train = int(597 * 0.8)
    return (src[:n_train], tgt_in[:n_train], tgt_out[:n_train],
            src[n_train:], tgt_in[n_train:], tgt_out[n_train:])


def train():
    torch.manual_seed(0)
    src_tr, tgt_in_tr, tgt_out_tr, src_v, tgt_in_v, tgt_out_v = get_data()
    model = EncoderDecoder()
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss(ignore_index=0)

    n_train = len(src_tr)
    history = []
    for epoch in range(26):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = indices[i:i + 16]
            src_b, tgt_in_b, tgt_out_b = src_tr[idx], tgt_in_tr[idx], tgt_out_tr[idx]
            optimizer.zero_grad()
            logits = model(src_b, tgt_in_b)
            B, T, V = logits.shape
            loss = criterion(logits.reshape(B * T, V), tgt_out_b.reshape(B * T))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(src_b)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(src_v, tgt_in_v)
            B, T, V = val_logits.shape
            preds = val_logits.argmax(-1)
            mask = tgt_out_v != 0
            val_acc = (preds[mask] == tgt_out_v[mask]).float().mean().item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{26} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.40,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
