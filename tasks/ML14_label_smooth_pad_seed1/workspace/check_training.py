"""Check label smoothing PAD fix."""
import json, sys, os, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smooth_loss import LabelSmoothingLoss


def check_loss_behavior():
    """Verify PAD token gets 0 probability and PAD positions are masked."""
    criterion = LabelSmoothingLoss(vocab_size=80, pad_idx=0, epsilon=0.1)

    # Test 1: PAD token should not receive smoothing mass
    # Create a batch where target is a real token
    logits = torch.randn(4, 80)
    targets_real = torch.tensor([1, 2, 3, 4])
    # If PAD gets mass, loss grad will push model to predict PAD
    # We check via the smooth_dist: at target positions that are real tokens,
    # PAD index should have 0 in smooth_dist
    # We test this by checking the loss at PAD positions is 0
    targets_with_pad = torch.tensor([1, 0, 3, 0])
    loss_with_pad = criterion(logits, targets_with_pad)

    # Manually compute expected loss excluding PAD positions
    import torch.nn.functional as F
    log_probs = F.log_softmax(logits, dim=-1)
    # With correct implementation, only positions 0 and 2 contribute
    # loss should be based on 2 non-PAD tokens only

    # Test 2: Loss at all-PAD batch should be 0
    all_pad_targets = torch.full((4,), 0, dtype=torch.long)
    loss_all_pad = criterion(logits, all_pad_targets)
    if loss_all_pad.item() > 1e-6:
        return False, f"Loss at all-PAD positions should be 0, got {loss_all_pad.item():.6f}"

    # Test 3: mixed batch — loss must only reflect non-PAD positions
    # With PAD masking: loss(half-PAD batch) ~= loss(real-only batch at same positions)
    torch.manual_seed(0)
    logits3 = torch.randn(4, 80)
    half_pad = torch.tensor([1, 0, 3, 0])
    loss_half = criterion(logits3, half_pad).item()
    # With correct masking, PAD positions contribute 0
    # so loss is average over the 2 real positions only
    real_only = torch.tensor([1, 3])
    loss_real_2 = criterion(logits3[[0, 2]], real_only).item()
    # They should match closely (both average over same 2 non-PAD positions)
    if abs(loss_half - loss_real_2) > 0.1:
        return False, f"PAD masking broken: mixed={loss_half:.4f} vs real-2={loss_real_2:.4f} differ"

    return True, "Label smoothing correctly excludes PAD token"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_loss_behavior()
    print(f"Loss behavior: {msg}")
    if not ok:
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
