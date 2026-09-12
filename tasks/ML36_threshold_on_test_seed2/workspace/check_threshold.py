"""Validate threshold selection fix — threshold must come from validation set."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("threshold_results.json"):
        return False, "threshold_results.json not found"
    return True, "threshold_results.json exists"


def check_threshold_source_is_val():
    """Check threshold_source reports val_set (not test_set)."""
    with open("threshold_results.json") as f:
        res = json.load(f)
    source = res.get("threshold_source", "unknown")
    if source != "val_set":
        return False, f"threshold_source=\'{source}\' (expected \'val_set\')"
    return True, "threshold_source=\'val_set\' (correct)"


def check_no_circular_evaluation():
    """Verify code does not use y_test for threshold selection."""
    with open("evaluate.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    # find_best_threshold should not be called with test variables
    test_threshold_calls = re.findall(
        r"find_best_threshold\s*\([^)]*(?:test_probs|y_test|X_test)[^)]*\)",
        active_src
    )
    if test_threshold_calls:
        return False, f"Threshold still found using test set: {test_threshold_calls}"
    return True, "Threshold selection does not use test set data"


def check_val_threshold_used_for_test():
    """Check code uses val_threshold (not best_threshold from test) for test eval."""
    with open("evaluate.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    # Should find val threshold application on test set
    val_thresh_on_test = bool(re.search(
        r"test_probs\s*>=\s*val_threshold|best_threshold.*val_probs.*y_val",
        active_src
    ))
    if not val_thresh_on_test:
        return False, "val_threshold not applied to test set predictions"
    return True, "val_threshold correctly applied to test set"


def check_inflation_near_zero():
    """After fix, inflation (reported - honest F1) should be near zero."""
    with open("threshold_results.json") as f:
        res = json.load(f)
    inflation = res.get("inflation", 1.0)
    if abs(inflation) > 0.02:
        return False, f"F1 inflation={inflation:+.4f} (expected ~0 when threshold is from val set)"
    return True, f"F1 inflation={inflation:+.4f} (near zero — no circular evaluation)"


def check_f1_is_realistic():
    """Reported F1 should be a realistic value (not inflated to 1.0)."""
    with open("threshold_results.json") as f:
        res = json.load(f)
    f1 = res.get("reported_f1", 0.0)
    if f1 > 0.98:
        return False, f"Reported F1={f1:.4f} suspiciously high — may still be using test set"
    if f1 < 0.01:
        return False, f"Reported F1={f1:.4f} too low — threshold evaluation broken"
    return True, f"Reported F1={f1:.4f} is realistic"


def check_val_f1_computed():
    """Check val_threshold is computed in the code."""
    with open("evaluate.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)
    has_val_thresh = bool(re.search(r"find_best_threshold\s*\([^)]*val_probs[^)]*y_val[^)]*\)|find_best_threshold\s*\([^)]*y_val[^)]*\)", active_src))
    if not has_val_thresh:
        return False, "find_best_threshold not called with val_probs/y_val"
    return True, "find_best_threshold called with validation data"


def check_honest_f1_in_results():
    """Honest F1 (with val-selected threshold) should be in results."""
    with open("threshold_results.json") as f:
        res = json.load(f)
    honest = res.get("honest_f1", None)
    if honest is None:
        return False, "honest_f1 not in results"
    if honest < 0.01:
        return False, f"honest_f1={honest:.4f} too low — val-threshold evaluation broken"
    return True, f"honest_f1={honest:.4f} present and reasonable"


def check_threshold_value_reasonable():
    """Threshold should be between 0.1 and 0.9."""
    with open("threshold_results.json") as f:
        res = json.load(f)
    t = res.get("best_threshold", 0.5)
    if not (0.05 < t < 0.95):
        return False, f"best_threshold={t} out of reasonable range"
    return True, f"best_threshold={t} in reasonable range"


def check():
    checks = [
        check_results_exist,
        check_threshold_source_is_val,
        check_no_circular_evaluation,
        check_val_threshold_used_for_test,
        check_inflation_near_zero,
        check_f1_is_realistic,
        check_val_f1_computed,
        check_honest_f1_in_results,
        check_threshold_value_reasonable,
    ]
    passed = 0
    total = len(checks)
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {fn.__name__}: {msg}")
        if ok:
            passed += 1

    score = round(passed / total, 4)
    print(f"\nResult: {passed}/{total} = {score}")
    return passed == total


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
