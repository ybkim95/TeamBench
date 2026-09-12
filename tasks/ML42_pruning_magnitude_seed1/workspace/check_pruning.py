"""Validate head pruning importance fix."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("pruning_results.json"):
        return False, "pruning_results.json not found"
    return True, "pruning_results.json exists"


def check_pruning_method_is_gradient():
    """pruning_method must be \'gradient_attribution\' not \'magnitude\'."""
    with open("pruning_results.json") as f:
        res = json.load(f)
    method = res.get("pruning_method", "unknown")
    if method == "magnitude":
        return False, "pruning_method=\'magnitude\' — still using weight magnitude"
    if "gradient" not in method:
        return False, f"pruning_method=\'{method}\' — expected \'gradient_attribution\'"
    return True, f"pruning_method=\'{method}\'"


def check_gradient_drop_less_than_magnitude():
    """Gradient pruning should cause less accuracy drop than magnitude pruning."""
    with open("pruning_results.json") as f:
        res = json.load(f)
    mag_drop = res.get("magnitude_drop", 1.0)
    grad_drop = res.get("gradient_drop", 1.0)
    if grad_drop >= mag_drop and mag_drop > 0.001:
        return False, f"gradient_drop={grad_drop:.4f} >= magnitude_drop={mag_drop:.4f} — gradient not better"
    return True, f"gradient_drop={grad_drop:.4f} <= magnitude_drop={mag_drop:.4f} (gradient better)"


def check_pruning_ok_flag():
    """pruning_ok should be True after fix."""
    with open("pruning_results.json") as f:
        res = json.load(f)
    ok = res.get("pruning_ok", False)
    if not ok:
        return False, "pruning_ok=False — gradient pruning not better than magnitude"
    return True, "pruning_ok=True"


def check_no_magnitude_in_main_pipeline():
    """run() should use gradient attribution, not magnitude."""
    with open("prune.py") as f:
        src = f.read()
    func_match = re.search(r"def run\(\).*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "run() function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    uses_magnitude_as_primary = bool(re.search(
        r"importances\s*=\s*compute_head_importance_magnitude",
        active_src
    ))
    if uses_magnitude_as_primary:
        return False, "run() still uses compute_head_importance_magnitude as primary"
    return True, "run() does not use magnitude importance as primary method"


def check_gradient_attribution_as_primary():
    """run() should call compute_head_importance_gradient for primary pruning."""
    with open("prune.py") as f:
        src = f.read()
    func_match = re.search(r"def run\(\).*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "run() function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    has_grad_primary = bool(re.search(
        r"importances\s*=\s*compute_head_importance_gradient",
        active_src
    ))
    if not has_grad_primary:
        return False, "run() does not call compute_head_importance_gradient as primary"
    return True, "run() uses compute_head_importance_gradient as primary"


def check_n_heads_pruned():
    with open("pruning_results.json") as f:
        res = json.load(f)
    n = res.get("n_heads_pruned", 0)
    if n != 6:
        return False, f"n_heads_pruned={n} (expected 6)"
    return True, f"n_heads_pruned=6 correct"


def check_base_accuracy_reasonable():
    with open("pruning_results.json") as f:
        res = json.load(f)
    base = res.get("base_accuracy", 0.0)
    chance = 1.0 / 3
    if base <= chance:
        return False, f"base_accuracy={base:.4f} <= chance ({chance:.4f})"
    return True, f"base_accuracy={base:.4f} > chance ({chance:.4f})"


def check_gradient_accuracy_not_catastrophic():
    """Gradient pruning should not lose more than 30% accuracy."""
    with open("pruning_results.json") as f:
        res = json.load(f)
    base = res.get("base_accuracy", 1.0)
    grad_acc = res.get("gradient_pruned_accuracy", 0.0)
    if base > 0 and grad_acc / base < 0.7:
        return False, f"Gradient pruned accuracy too low: {grad_acc:.4f} (base={base:.4f})"
    return True, f"Gradient pruned accuracy reasonable: {grad_acc:.4f} (base={base:.4f})"


def check_total_heads_correct():
    with open("pruning_results.json") as f:
        res = json.load(f)
    total = res.get("total_heads", 0)
    if total != 12:
        return False, f"total_heads={total} (expected 12)"
    return True, f"total_heads=12 correct"


def check():
    checks = [
        check_results_exist,
        check_pruning_method_is_gradient,
        check_gradient_drop_less_than_magnitude,
        check_pruning_ok_flag,
        check_no_magnitude_in_main_pipeline,
        check_gradient_attribution_as_primary,
        check_n_heads_pruned,
        check_base_accuracy_reasonable,
        check_gradient_accuracy_not_catastrophic,
        check_total_heads_correct,
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
