"""Check AMP gradient clip order fix."""
import json, sys, os, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_code_order():
    """Verify that unscale_ comes before clip_grad_norm_ in train.py."""
    with open("train.py") as f:
        src = f.read()
    lines = src.split("\n")

    unscale_line = None
    clip_line = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "scaler.unscale_" in stripped and not stripped.startswith("#"):
            unscale_line = i
        if "clip_grad_norm_" in stripped and not stripped.startswith("#"):
            clip_line = i

    if unscale_line is None:
        return False, "scaler.unscale_() call not found in train.py"
    if clip_line is None:
        return False, "clip_grad_norm_() call not found in train.py"
    if unscale_line > clip_line:
        return False, f"unscale_ (line {unscale_line+1}) comes AFTER clip_grad_norm_ (line {clip_line+1}) — wrong order"
    return True, f"unscale_ (line {unscale_line+1}) before clip_grad_norm_ (line {clip_line+1}) — correct"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final val acc: {acc:.4f}")

    ok, msg = check_code_order()
    print(f"Code order check: {msg}")
    if not ok:
        return False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (acc={acc:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
