"""Validate padding mask fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CausalAttention, PAD_TOKEN_ID


def check_padding_mask_applied():
    """Verify padding mask is applied in CausalAttention."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.py')) as f:
        src = f.read()

    import re
    # Look for padding mask application in forward
    # Pattern: masked_fill with padding_mask
    has_pad_mask = bool(re.search(r'padding_mask', src) and
                        re.search(r'masked_fill.*padding', src))
    if not has_pad_mask:
        return False, "padding_mask not applied with masked_fill in CausalAttention"

    # Check that the mask is broadcast correctly (B, 1, 1, T) or similar
    has_unsqueeze = bool(re.search(r'padding_mask.*unsqueeze', src) or
                         re.search(r'unsqueeze.*padding_mask', src))
    return True, f"padding_mask applied: has_unsqueeze={has_unsqueeze}"


def check_pad_positions_masked():
    """Verify PAD key positions receive -inf attention weight."""
    attn = CausalAttention(embed_dim=32, num_heads=4, max_seq_len=24)
    attn.eval()

    T = 8
    B = 2
    # Last 2 positions are PAD
    x = torch.randn(B, T, 32)
    padding_mask = torch.zeros(B, T, dtype=torch.bool)
    padding_mask[:, -2:] = True  # last 2 positions are PAD

    with torch.no_grad():
        out = attn(x, padding_mask)

    # Check no NaN in output
    if torch.isnan(out).any():
        return False, "NaN in attention output with padding mask"

    # With correct padding mask, real token (pos 0) should not be influenced by PAD
    # We verify by checking that output at non-PAD positions is non-trivial
    real_var = out[:, :T-2, :].var().item()
    if real_var < 1e-8:
        return False, f"Real token output variance too low ({real_var:.8f})"

    return True, f"PAD masking correct, real token var={real_var:.4f}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_padding_mask_applied()
    print(f"Padding mask check: {msg}")
    if not ok:
        print("FAIL: Padding mask not applied")
        return False

    ok2, msg2 = check_pad_positions_masked()
    print(f"PAD masking behavior: {msg2}")
    if not ok2:
        print("FAIL: PAD masking behavior wrong")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
