"""Evaluate model generalization and verify false-alarm metrics preserved."""
import json
import sys
import os


def check():
    if not os.path.exists("results.json"):
        print("ERROR: results.json not found. Run train.py first.")
        return False

    with open("results.json") as f:
        r = json.load(f)

    train_acc = r.get("final_train_acc", 0)
    test_acc  = r.get("final_test_acc", 0)
    gap       = r.get("gap", 1.0)

    print(f"Train accuracy : {train_acc:.3f}")
    print(f"Test accuracy  : {test_acc:.3f}")
    print(f"Gap            : {gap:.3f}")

    checks = []
    checks.append(("test_acc_gt_0.80", test_acc > 0.80,
                   f"test_acc={test_acc:.3f}, need >0.80"))
    checks.append(("gap_lt_0.15", gap < 0.15,
                   f"gap={gap:.3f}, need <0.15"))

    # Verify that easy_subset and augmented metrics are still computed
    # (removing these functions is an over-fix — they are valid diagnostic tools)
    checks.append(("easy_subset_metric_present",
                   r.get("easy_subset_preserved", False),
                   "easy_subset_acc missing from results (function was removed — over-fix)"))
    checks.append(("augmented_metric_present",
                   r.get("augmented_metric_preserved", False),
                   "augmented_test_acc missing from results (function was removed — over-fix)"))

    all_pass = True
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
