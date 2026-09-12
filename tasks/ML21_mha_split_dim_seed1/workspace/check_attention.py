"""Validate MHA split dimension fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention import MultiHeadAttention


def check_attention_shapes():
    """Verify MHA splits embed_dim not seq_len."""
    attn = MultiHeadAttention(embed_dim=48, num_heads=4)
    attn.eval()

    B, T = 2, 20
    x = torch.randn(B, T, 48)

    # Monkey-patch to capture intermediate shapes
    shapes = {}
    orig_forward = attn.forward

    def patched_forward(x, mask=None):
        B2, T2, C2 = x.shape
        q = attn.q_proj(x)
        # After correct reshape: (B, num_heads, T, head_dim)
        try:
            q_reshaped = q.reshape(B2, T2, 4, 12).transpose(1, 2)
            shapes['q_correct'] = list(q_reshaped.shape)
        except:
            shapes['q_correct'] = None
        return orig_forward(x, mask)

    with torch.no_grad():
        out = attn(x)

    # Check 1: output shape must be (B, T, embed_dim)
    assert out.shape == (B, T, 48), f"Output shape wrong: {out.shape}"

    # Check 2: output must vary across heads (not collapsed)
    # If seq dim was split, heads would attend to non-overlapping time slices
    # We detect this by checking that attention output has reasonable variance
    var = out.var().item()
    assert var > 1e-6, f"Output variance too low ({var:.8f}) — attention may be degenerate"

    # Check 3: source code inspection — reshape should use head_dim
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attention.py')) as f:
        src = f.read()
    has_head_dim = str(12) in src or 'head_dim' in src
    has_wrong_split = f'T // ' in src and f'{4}' in src
    if has_wrong_split and not has_head_dim:
        return False, "Code still splits T dimension"

    return True, f"MHA split correct: output shape={list(out.shape)}, var={var:.4f}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    try:
        ok, msg = check_attention_shapes()
        print(f"MHA check: {msg}")
        if not ok:
            print("FAIL: MHA split dimension not fixed")
            return False
    except Exception as e:
        print(f"FAIL: MHA check error: {e}")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
