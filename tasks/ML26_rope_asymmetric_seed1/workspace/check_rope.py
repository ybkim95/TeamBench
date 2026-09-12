"""Validate RoPE symmetric application fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rope_attention import RoPEAttention, apply_rope, build_rope_cache


def check_rope_applied_to_both():
    """Verify RoPE is applied to both Q and K."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rope_attention.py')) as f:
        src = f.read()

    import re
    # Find the forward method — check non-commented lines only
    non_comment_lines = [l for l in src.split('\n') if not l.lstrip().startswith('#')]
    non_comment_src = '\n'.join(non_comment_lines)

    q_rotated = bool(re.search(r'q\s*=\s*apply_rope\s*\(\s*q', non_comment_src))
    k_rotated = bool(re.search(r'k\s*=\s*apply_rope\s*\(\s*k', non_comment_src))

    if not q_rotated:
        return False, "apply_rope not applied to q (queries not rotated)"
    if not k_rotated:
        return False, "apply_rope not applied to k (keys not rotated)"

    # Also check that the BUG comment is gone or q_rotated line is uncommented
    has_bug_skip = bool(re.search(r'#\s*q\s*=\s*apply_rope', src))
    if has_bug_skip:
        return False, "q = apply_rope line is still commented out"

    return True, "RoPE applied symmetrically to both Q and K"


def check_rope_relative_position():
    """Verify RoPE gives relative position signal."""
    cos, sin = build_rope_cache(64, 12)
    # RoPE property: (R_m * q) @ (R_n * k) depends only on (n - m)
    # Test: q at pos 0 vs k at pos 2 should give same score as q at pos 1 vs k at pos 3
    torch.manual_seed(0)
    q = torch.randn(1, 12)
    k = torch.randn(1, 12)

    def rope_score(q_pos, k_pos):
        cos_q = cos[q_pos].unsqueeze(0)
        sin_q = sin[q_pos].unsqueeze(0)
        cos_k = cos[k_pos].unsqueeze(0)
        sin_k = sin[k_pos].unsqueeze(0)
        from rope_attention import rotate_half
        q_rot = q * cos_q + rotate_half(q) * sin_q
        k_rot = k * cos_k + rotate_half(k) * sin_k
        return (q_rot * k_rot).sum().item()

    # At same relative distance (2), scores should be close
    s02 = rope_score(0, 2)
    s13 = rope_score(1, 3)
    s24 = rope_score(2, 4)
    diffs = [abs(s02 - s13), abs(s13 - s24)]
    max_diff = max(diffs)
    if max_diff > 0.5:
        return False, f"RoPE relative position property violated: diffs={diffs}"
    return True, f"RoPE relative position OK: scores≈{s02:.3f},{s13:.3f},{s24:.3f}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_rope_applied_to_both()
    print(f"RoPE symmetry: {msg}")
    if not ok:
        print("FAIL: RoPE not applied to both Q and K")
        return False

    ok2, msg2 = check_rope_relative_position()
    print(f"RoPE relative pos: {msg2}")
    if not ok2:
        print("FAIL: RoPE relative position property broken")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
