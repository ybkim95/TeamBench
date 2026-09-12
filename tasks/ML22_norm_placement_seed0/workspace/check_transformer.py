"""Validate LayerNorm placement fix."""
import json
import sys
import os
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformer import TransformerBlock


def check_norm_placement():
    """Verify LayerNorm is consistently pre-norm or post-norm."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transformer.py')) as f:
        src = f.read()

    # Check for consistent pre-norm pattern:
    # pre-norm: x = x + attn(norm(x)) and x = x + ff(norm(x))
    # or post-norm: x = norm(x + attn(x)) and x = norm(x + ff(x))

    # Find TransformerBlock.forward
    import ast
    tree = ast.parse(src)

    # Code inspection: check that both sublayers use same norm style
    # Pre-norm signature: "norm" appears inside "attn(" call
    # Post-norm signature: "norm(" wraps the entire residual

    # Simpler check: forward should have matching patterns for attn and ff
    # Neither should have mixed post/pre norm

    # Check that the buggy mixed pattern is gone:
    # Buggy: "norm1(x + self.attn(x))" AND "x + self.ff(self.norm2(x))"
    has_post_attn = ("norm1(x + " in src or "norm1(x+" in src)
    has_pre_ff = ("x + self.ff(self.norm" in src or "x+self.ff(self.norm" in src)
    if has_post_attn and has_pre_ff:
        return False, "Still has broken hybrid: post-norm attn + pre-norm ff"

    # Check that output is sensible (no NaN/Inf)
    block = TransformerBlock(embed_dim=32, num_heads=4)
    block.eval()
    with torch.no_grad():
        x = torch.randn(2, 8, 32)
        out = block(x)
    if torch.isnan(out).any() or torch.isinf(out).any():
        return False, "TransformerBlock produces NaN/Inf"

    return True, "LayerNorm placement consistent (no mixed pre/post norm)"


def check_gradient_flow():
    """Verify gradients flow properly through the block."""
    from transformer import TransformerBlock
    block = TransformerBlock(embed_dim=32, num_heads=4)
    x = torch.randn(2, 8, 32, requires_grad=True)
    out = block(x)
    loss = out.mean()
    loss.backward()
    grad_norm = x.grad.norm().item()
    if grad_norm < 1e-8 or grad_norm > 1e4:
        return False, f"Gradient norm {grad_norm:.6f} suggests instability"
    return True, f"Gradient norm {grad_norm:.4f} OK"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_norm_placement()
    print(f"Norm placement: {msg}")
    if not ok:
        print("FAIL: LayerNorm placement not fixed")
        return False

    ok2, msg2 = check_gradient_flow()
    print(f"Gradient flow: {msg2}")
    if not ok2:
        print("FAIL: Gradient flow broken")
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
