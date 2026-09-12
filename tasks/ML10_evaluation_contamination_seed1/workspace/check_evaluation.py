"""Check that evaluation has no test set contamination."""
import json
import sys
import os


def check():
    if not os.path.exists("eval_results.json"):
        print("ERROR: eval_results.json not found. Run evaluate.py first.")
        return False

    with open("eval_results.json") as f:
        r = json.load(f)

    checks = []

    flag = r.get("scaler_on_full_data", True)
    checks.append(("no_scaler_on_full_data",
                   not flag,
                   "scaler_on_full_data contamination still present"))
    flag = r.get("pca_on_full_data", True)
    checks.append(("no_pca_on_full_data",
                   not flag,
                   "pca_on_full_data contamination still present"))
    flag = r.get("outlier_removal_on_test", True)
    checks.append(("no_outlier_removal_on_test",
                   not flag,
                   "outlier_removal_on_test contamination still present"))

    # Check test accuracy is present
    acc = r.get("test_accuracy")
    checks.append(("test_accuracy_present",
                   acc is not None and isinstance(acc, float),
                   f"test_accuracy={acc!r}"))

    # Check accuracy is in valid range
    if acc is not None:
        checks.append(("test_accuracy_valid_range",
                       0.0 <= acc <= 1.0,
                       f"test_accuracy={acc} out of [0,1]"))

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
