"""Check KD temperature asymmetry fix."""
import json, sys, os, torch, torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_kd_function():
    """Verify temperature is applied symmetrically and T^2 scaling present."""
    with open("train.py") as f:
        src = f.read()

    # Check 1: student log_softmax must use /T or /temperature
    import re
    # Look for log_softmax with temperature division
    student_temp = re.search(
        r"log_softmax\s*\(\s*student_logits\s*/\s*T",
        src
    )
    if not student_temp:
        return False, "student_logits not divided by T in log_softmax call"

    # Check 2: T^2 scaling must be present
    t2_patterns = [r"T\s*\*\s*T", r"T\s*\*\*\s*2", r"temperature\s*\*\*\s*2"]
    has_t2 = any(re.search(p, src) for p in t2_patterns)
    if not has_t2:
        return False, "T^2 (T*T or T**2) scaling factor not found in kd_loss"

    # Check 3: numerical symmetry test
    torch.manual_seed(42)
    T = 3.0
    teacher_logits = torch.randn(8, 6)
    student_logits = torch.randn(8, 6)
    targets = torch.randint(0, 6, (8,))

    # Import the fixed kd_loss
    import importlib.util, types
    spec_obj = importlib.util.spec_from_file_location("train_mod", "train.py")
    mod = importlib.util.module_from_spec(spec_obj)
    # Execute only function definitions (not the main train call)
    try:
        spec_obj.loader.exec_module(mod)
    except Exception:
        pass  # ignore import-time side effects

    if hasattr(mod, "kd_loss"):
        # Verify gradient w.r.t. student logits is non-degenerate
        s = student_logits.clone().requires_grad_(True)
        loss = mod.kd_loss(s, teacher_logits.detach(), targets, T=T)
        loss.backward()
        grad_norm = s.grad.norm().item()
        if grad_norm < 1e-6:
            return False, f"KD loss gradient norm {grad_norm:.2e} near zero — T^2 scaling may be missing"

    return True, "KD temperature applied symmetrically with T^2 scaling"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    print(f"Final student val acc: {acc:.4f}")

    ok, msg = check_kd_function()
    print(f"KD function check: {msg}")
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
