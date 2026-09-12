"""Validate causal mask fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CausalSelfAttention


def check_causal_mask():
    """Verify the causal mask allows self-attention and blocks future tokens."""
    attn = CausalSelfAttention(embed_dim=64, num_heads=4, seq_len=12)
    mask = attn.causal_mask

    T = 12
    # Check 1: diagonal must be False (not masked) — token can attend to itself
    diag_masked = mask.diagonal().any().item()
    if diag_masked:
        return False, f"Diagonal is masked (diagonal=0 bug): token cannot attend to itself"

    # Check 2: upper triangle (future, i<j) must be True (masked)
    rows, cols = torch.triu_indices(T, T, offset=1)
    future_unmasked = not mask[rows, cols].all().item()
    if future_unmasked:
        return False, "Future positions are not fully masked"

    # Check 3: lower triangle (past, i>j) must be False (unmasked)
    rows2, cols2 = torch.tril_indices(T, T, offset=-1)
    past_masked = mask[rows2, cols2].any().item()
    if past_masked:
        return False, "Past positions are incorrectly masked"

    return True, f"Causal mask correct: shape={mask.shape}, diagonal unmasked, future masked"


def check_self_attention_flow():
    """Verify token can attend to itself by checking output is non-trivial."""
    import torch.nn as nn
    from model import CausalLM
    torch.manual_seed(0)
    model = CausalLM(vocab_size=96, embed_dim=64,
                     num_heads=4, num_layers=1, seq_len=12)
    model.eval()
    with torch.no_grad():
        x = torch.randint(0, 96, (2, 12))
        logits = model(x)
        # Output should have non-trivial variance across positions
        var = logits.var(dim=-1).mean().item()
        if var < 1e-6:
            return False, f"Model output variance too low ({var:.8f}) — possible all-zero attn"
    return True, f"Model output variance={var:.4f} OK"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_causal_mask()
    print(f"Causal mask: {msg}")
    if not ok:
        print("FAIL: Causal mask not fixed")
        return False

    ok2, msg2 = check_self_attention_flow()
    print(f"Self-attention flow: {msg2}")
    if not ok2:
        print("FAIL: Self-attention flow broken")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
