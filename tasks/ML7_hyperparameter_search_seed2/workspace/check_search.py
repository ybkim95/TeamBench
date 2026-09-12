"""Check that hyperparameter search uses valid combinations only."""
import json
import sys
import os


def check():
    if not os.path.exists("search_results.json"):
        print("ERROR: search_results.json not found.")
        return False

    with open("search_results.json") as f:
        r = json.load(f)

    checks = []

    # Check no invalid combos tried
    invalid = r.get("invalid_combos_tried", 999)
    checks.append(("no_invalid_combos",
                   invalid == 0,
                   f"{invalid} invalid combinations tried (should be 0)"))

    # Check best accuracy is reasonable (>50% for classification)
    best_acc = r.get("best_accuracy", 0)
    checks.append(("best_accuracy_reasonable",
                   best_acc > 0.5,
                   f"best_accuracy={best_acc:.3f} <= 0.5 (still using bad params)"))

    # Check n_trials matches expected
    n_trials = r.get("n_trials", 0)
    checks.append(("sufficient_trials",
                   n_trials >= 5,
                   f"only {n_trials} trials run"))

    # Check best_params present
    bp = r.get("best_params")
    checks.append(("best_params_present",
                   bp is not None and isinstance(bp, dict),
                   "best_params missing or not a dict"))

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
