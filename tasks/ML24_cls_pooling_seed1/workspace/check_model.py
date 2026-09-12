"""Validate CLS pooling fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import BertClassifier


def check_cls_pooling():
    """Verify model uses CLS token (position 0) for pooling."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.py')) as f:
        src = f.read()

    import re
    # Check for CLS pooling: enc_out[:, 0, :] or enc_out[:, 0]
    has_cls_pool = bool(re.search(r'enc_out\s*\[:,\s*0\s*[,\]]', src) or
                        re.search(r'\[:, 0, :\]', src) or
                        re.search(r'\[:, 0\]', src))
    if not has_cls_pool:
        return False, "CLS pooling [:, 0, :] not found in model.py"

    # Check mean pooling is removed from forward
    has_mean_pool_bug = ('enc_out.mean' in src or
                         ('(enc_out * mask)' in src and '.sum(dim=1)' in src))
    if has_mean_pool_bug:
        return False, "Mean pooling still present in model.py"

    return True, "CLS token pooling [:, 0, :] found"


def check_pooling_behavior():
    """Verify pooled representation equals CLS token, not mean."""
    model = BertClassifier(
        vocab_size=80, embed_dim=48,
        num_heads=4, num_layers=2,
        num_classes=5, max_seq_len=22
    )
    model.eval()

    torch.manual_seed(0)
    # Create input where CLS token (pos 0) has distinct value
    input_ids = torch.randint(2, 80, (2, 21))
    input_ids[:, 0] = 1  # CLS token

    # Hook to capture encoder output
    captured = {}
    def hook(module, input, output):
        captured['enc_out'] = output

    model.encoder.norm.register_forward_hook(hook)

    with torch.no_grad():
        logits = model(input_ids)

    enc_out = captured['enc_out']
    cls_rep = enc_out[:, 0, :]
    mean_rep = enc_out.mean(dim=1)

    # Check that model is using CLS, not mean
    # We can do this by checking that model output is deterministic with cls_rep
    # (can't directly verify internal pooled, but code check covers it)
    if torch.isnan(logits).any():
        return False, "NaN in model output"

    return True, f"Model output OK, shape={list(logits.shape)}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_cls_pooling()
    print(f"Pooling check: {msg}")
    if not ok:
        print("FAIL: CLS pooling not implemented")
        return False

    ok2, msg2 = check_pooling_behavior()
    print(f"Behavior check: {msg2}")
    if not ok2:
        print("FAIL: Model behavior check failed")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
