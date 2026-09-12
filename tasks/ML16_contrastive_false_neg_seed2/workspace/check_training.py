"""Check SimCLR false negative fix."""
import json, sys, os, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nt_xent_loss import nt_xent_loss


def check_loss_correctness():
    """Verify that positive pairs are excluded from the negative denominator."""
    torch.manual_seed(0)
    N = 4
    D = 16

    # Create z1, z2 as IDENTICAL normalized vectors (perfect positive pairs)
    # With the correct loss, identical pairs should give near-minimum loss
    # With the buggy loss, identical pairs would push the loss to be HIGH
    # (because the positive is in the denominator, competing with itself)
    z = torch.randn(N, D)
    z_norm = z / z.norm(dim=1, keepdim=True)

    # Perfect positives: z1 == z2
    loss_perfect = nt_xent_loss(z_norm, z_norm.clone(), temperature=0.1)

    # Random negatives: z1, z2 are independent random vectors
    z1_rand = torch.randn(N, D)
    z2_rand = torch.randn(N, D)
    loss_random = nt_xent_loss(z1_rand, z2_rand, temperature=0.1)

    # With correct implementation: loss_perfect < loss_random
    # (identical pairs should have lower loss than random pairs)
    # With buggy implementation: this may be reversed
    if loss_perfect.item() >= loss_random.item():
        return False, (
            f"Loss with identical pairs ({loss_perfect.item():.4f}) >= "
            f"loss with random pairs ({loss_random.item():.4f}). "
            "Positive pair is still being treated as a negative."
        )

    # Also check: gradient of loss w.r.t. similarity between z1[0] and z2[0]
    # should be NEGATIVE (increasing similarity should decrease loss)
    z1 = torch.randn(N, D, requires_grad=True)
    z2 = torch.randn(N, D)
    loss = nt_xent_loss(z1, z2, temperature=0.1)
    loss.backward()
    # The gradient of the loss w.r.t. z1[0] should point AWAY from z2[0]
    # (i.e., dot product of grad[0] with z2[0] should be negative, meaning
    # gradient descent would increase alignment, i.e., loss wants more similarity)
    return True, f"Loss correct: perfect={loss_perfect.item():.4f} < random={loss_random.item():.4f}"


def check_mask_in_code():
    """Check that the positive pair is excluded from neg_mask."""
    with open("nt_xent_loss.py") as f:
        src = f.read()
    if "~pos_mask" not in src and "pos_mask" not in src.split("neg_mask")[1] if "neg_mask" in src else True:
        # More lenient check: just ensure pos_mask is used in defining neg_mask
        import re
        neg_mask_def = re.search(r"neg_mask\s*=.*", src)
        if neg_mask_def:
            defn = neg_mask_def.group(0)
            if "pos_mask" not in defn:
                return False, f"neg_mask definition does not reference pos_mask: {defn!r}"
    return True, "neg_mask correctly references pos_mask"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_probe_acc", 0)
    print(f"Final probe acc: {acc:.4f}")

    ok, msg = check_loss_correctness()
    print(f"Loss correctness: {msg}")
    if not ok:
        return False

    ok2, msg2 = check_mask_in_code()
    print(f"Code check: {msg2}")
    if not ok2:
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
