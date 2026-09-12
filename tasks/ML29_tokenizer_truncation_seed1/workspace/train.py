"""Training script for sentence-pair classification."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tokenizer import batch_encode_pairs, CLS_ID, SEP_ID, PAD_ID, MAX_LEN, VOCAB_SIZE


def make_dataset(n: int = 468, seed: int = 42):
    """Generate synthetic semantic textual similarity sentence pairs."""
    rng = np.random.RandomState(seed)
    pairs = []
    labels = []
    for i in range(n):
        # Variable length sentences — many will exceed max_len when combined
        len_a = rng.randint(8, 22)
        len_b = rng.randint(8, 22)
        sent_a = rng.randint(3, 100, size=len_a).tolist()
        sent_b = rng.randint(3, 100, size=len_b).tolist()
        pairs.append((sent_a, sent_b))
        # Label based on first token of each sentence
        labels.append((sent_a[0] + sent_b[0]) % 2)
    return pairs, np.array(labels, dtype=np.int64)


class PairClassifier(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int, num_classes: int, max_len: int):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_ID)
        self.type_emb = nn.Embedding(2, embed_dim)
        self.pos_emb = nn.Embedding(max_len, embed_dim)
        self.encoder = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=4, dim_feedforward=embed_dim * 2,
            batch_first=True, dropout=0.0
        )
        self.classifier = nn.Linear(embed_dim, num_classes)

    def forward(self, input_ids, token_type_ids, attention_mask):
        B, T = input_ids.shape
        pos = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = (self.token_emb(input_ids) +
             self.type_emb(token_type_ids) +
             self.pos_emb(pos))
        key_pad_mask = (attention_mask == 0)
        x = self.encoder(x, src_key_padding_mask=key_pad_mask)
        cls_rep = x[:, 0, :]  # CLS token
        return self.classifier(cls_rep)


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    pairs, labels = make_dataset(n=468, seed=42)
    enc = batch_encode_pairs(pairs, max_len=MAX_LEN)

    input_ids = torch.tensor(enc["input_ids"], dtype=torch.long)
    token_types = torch.tensor(enc["token_type_ids"], dtype=torch.long)
    attn_mask = torch.tensor(enc["attention_mask"], dtype=torch.long)
    y = torch.tensor(labels, dtype=torch.long)

    n = len(y)
    n_train = int(n * 0.8)
    perm = torch.randperm(n)
    tr_idx, val_idx = perm[:n_train], perm[n_train:]

    model = PairClassifier(vocab_size=VOCAB_SIZE, embed_dim=32,
                           num_classes=2, max_len=MAX_LEN)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    history = []
    for epoch in range(24):
        model.train()
        epoch_loss = 0.0
        ep_perm = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = tr_idx[ep_perm[i:i + 16]]
            optimizer.zero_grad()
            loss = criterion(model(input_ids[idx], token_types[idx], attn_mask[idx]), y[idx])
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(idx)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_acc = (model(input_ids[val_idx], token_types[val_idx],
                             attn_mask[val_idx]).argmax(1) == y[val_idx]).float().mean().item()
        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{24} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.45,
        "truncated_correctly": enc["truncated_correctly"],
        "sep_present_rate": sum(enc["has_both_sep"]) / len(enc["has_both_sep"]),
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
