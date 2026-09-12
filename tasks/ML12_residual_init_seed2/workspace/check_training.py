"""Check residual init fix and training convergence."""
import json, sys, os, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ResNet, check_init_variance


def check():
    # Check 1: training results
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    metric = res.get("final_val_metric", 0)
    print(f"Final metric: {metric:.4f}")

    # Check 2: init variance should be low
    model = ResNet(input_dim=40, hidden_dim=80,
                   num_classes=5, num_blocks=12)
    stats = check_init_variance(model)
    max_var = stats["max_variance"]
    print(f"Max init variance: {max_var:.4f}")
    if max_var > 2.0:
        print(f"FAIL: Init variance {max_var:.4f} too high (expected < 2.0 with fix)")
        return False

    # Check 3: last layer of each block should be near-zero
    for i, block in enumerate(model.blocks):
        w_norm = block.fc2.weight.data.abs().max().item()
        if w_norm > 0.1:
            print(f"FAIL: Block {i} fc2 weight norm {w_norm:.4f} > 0.1 (not zero-initialized)")
            return False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (metric {metric:.4f} <= 0.65)")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
