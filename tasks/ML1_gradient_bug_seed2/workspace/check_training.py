"""Check training outcome."""
import json
import os
import re
import sys


def check():
    # ── 1. training_results.json ───────────────────────────────────────────
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found. Run train.py first.")
        return False

    with open("training_results.json") as f:
        results = json.load(f)

    metric    = results.get("final_val_metric", 0)
    converged = results.get("converged", False)

    print(f"Final val metric : {metric:.4f}")
    print(f"Converged (>0.70): {converged}")

    checks = []
    checks.append(("convergence", converged,
                   f"val_metric={metric:.4f}, need >0.70"))

    # ── 2. Verify train.py preserves #  choices ───────────
    if os.path.exists("train.py"):
        with open("train.py") as f:
            train_src = f.read()
        if os.path.exists("model.py"):
            with open("model.py") as f:
                model_src = f.read()
        else:
            model_src = ""
        full_src = train_src + model_src

        # Must preserve: xavier_uniform_ with gain=2.0
        has_gain2 = bool(re.search(r"xavier_uniform_.*gain\s*=\s*2\.0", full_src))
        checks.append(("preserves_xavier_gain_2",
                       has_gain2,
                       "xavier_uniform_ gain=2.0 was modified/removed"))

        has_wd = bool(re.search(r"weight_decay\s*=\s*0\.1", train_src))
        checks.append(("preserves_weight_decay_0.1",
                       has_wd,
                       "weight_decay=0.1 was modified/removed"))

        has_schedule = "CosineAnnealingWarmRestarts" in train_src
        checks.append(("preserves_cosine_warm_restart",
                       has_schedule,
                       "CosineAnnealingWarmRestarts was removed/replaced"))

    # ── 3. Verify real bugs were fixed (train.py) ─────────────────────────
    if os.path.exists("train.py"):
        with open("train.py") as f:
            src = f.read()

        # Loss function bug: must use nn.MSELoss()
        has_correct_loss = "nn.MSELoss" in src
        checks.append(("correct_loss_function",
                       has_correct_loss,
                       f"Loss function not fixed (expected nn.MSELoss())"))

        # LR bug: must not use the buggy lr value
        has_bug_lr = f"lr=10.0" in src or f"lr=10" in src
        checks.append(("lr_not_too_high",
                       not has_bug_lr,
                       f"Learning rate still 10.0 (must be ~0.001)"))

        # BatchNorm eval mode: evaluate() must call model.eval()
        # Check that model.train() is NOT inside evaluate()
        eval_fn_match = re.search(r"def evaluate\(.*?
(?:.*?
)*?(?=def |\Z)", src)
        if eval_fn_match:
            eval_body = eval_fn_match.group(0)
            has_eval_mode = "model.eval()" in eval_body
            checks.append(("eval_uses_model_eval",
                           has_eval_mode,
                           "evaluate() still uses model.train() instead of model.eval()"))

    all_pass = True
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    if all_pass:
        print("\nAll checks passed.")
    else:
        print("\nSome checks failed.")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
