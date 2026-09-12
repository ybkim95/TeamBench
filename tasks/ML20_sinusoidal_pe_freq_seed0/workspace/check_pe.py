"""Validate sinusoidal PE frequency fix."""
import json
import sys
import os
import torch
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from positional_encoding import SinusoidalPE


def check_pe_frequencies():
    """Verify that PE uses correct step=2 frequency bands."""
    pe = SinusoidalPE(embed_dim=32, max_len=128, dropout=0.0)
    pe_matrix = pe.pe[0]  # (max_len, embed_dim)

    # Check 1: Dimensions 2i and 2i+1 must have the same frequency (sin/cos pair)
    # At position 1: pe[1, 2i] = sin(1 * f_i), pe[1, 2i+1] = cos(1 * f_i)
    # sin^2 + cos^2 = 1, so pe[1,2i]^2 + pe[1,2i+1]^2 should be close to 1
    pos1 = pe_matrix[1]  # (embed_dim,)
    paired_sum = (pos1[0::2] ** 2 + pos1[1::2] ** 2)
    if not (paired_sum > 0.8).all().item():
        return False, f"sin^2 + cos^2 != 1 for pairs — step=2 not used"

    # Check 2: Different positions should have different PE values
    pos2 = pe_matrix[2]
    pos4 = pe_matrix[4]
    if torch.allclose(pos2, pos4, atol=1e-4):
        return False, "PE is same for positions 2 and 4 — frequencies may be wrong"

    # Check 3: Frequency ratio between consecutive pairs should be 10000^(2/d)
    # pe[p, 0] = sin(p * freq_0), pe[p, 2] = sin(p * freq_1)
    # freq_0 / freq_1 = 10000^(2/d)
    expected_ratio = 10000 ** (2 / 32)
    p = 1.0
    # Use arcsin carefully — check that phase difference corresponds to freq ratio
    f0_val = pe_matrix[1, 0].item()
    f1_val = pe_matrix[1, 2].item()
    if abs(f0_val) < 0.1 or abs(f1_val) < 0.1:
        # Near 0, hard to test ratio — skip
        pass
    else:
        actual_ratio = math.asin(max(-1, min(1, f0_val))) / max(1e-10, math.asin(max(-1, min(1, f1_val))))
        if abs(actual_ratio - expected_ratio) > expected_ratio * 0.5:
            return False, f"Frequency ratio wrong: got {actual_ratio:.3f}, expected ~{expected_ratio:.3f}"

    return True, f"PE frequencies correct: embed_dim=32, paired sin^2+cos^2=1"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_pe_frequencies()
    print(f"PE check: {msg}")
    if not ok:
        print("FAIL: Sinusoidal PE not fixed")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
