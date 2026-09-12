"""Validate shadow deployment eval mode fix."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("shadow_results.json"):
        return False, "shadow_results.json not found"
    return True, "shadow_results.json exists"


def check_eval_mode_match():
    """Both models must be in eval mode during comparison."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    match = res.get("eval_mode_match", False)
    if not match:
        return False, "eval_mode_match=False (shadow model not in eval mode)"
    return True, "eval_mode_match=True (both models in eval mode)"


def check_shadow_in_eval():
    """shadow_in_eval must be True."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    ok = res.get("shadow_in_eval", False)
    if not ok:
        return False, "shadow_in_eval=False (shadow model still in train mode)"
    return True, "shadow_in_eval=True"


def check_no_shadow_train_mode_in_code():
    """shadow_eval.py must not call shadow_model.train() before evaluation."""
    with open("shadow_eval.py") as f:
        src = f.read()

    # Find run_shadow_evaluation function
    func_match = re.search(r"def run_shadow_evaluation.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "run_shadow_evaluation function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    # Should not set shadow_model.train() before the comparison
    train_call = bool(re.search(r"shadow_model\.train\(\)", active_src))
    if train_call:
        return False, "shadow_model.train() still called in run_shadow_evaluation"
    return True, "shadow_model.train() not called during evaluation"


def check_shadow_model_eval_called():
    """run_shadow_evaluation must call shadow_model.eval()."""
    with open("shadow_eval.py") as f:
        src = f.read()

    func_match = re.search(r"def run_shadow_evaluation.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "run_shadow_evaluation function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    if "shadow_model.eval()" not in active_src:
        return False, "shadow_model.eval() not called in run_shadow_evaluation"
    return True, "shadow_model.eval() called before comparison"


def check_accuracy_gap_reduced():
    """Shadow accuracy with eval mode should be closer to production."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    prod_acc = res.get("production", {}).get("accuracy", 0.0)
    shadow_buggy = res.get("shadow_buggy", {}).get("accuracy", 0.0)
    shadow_correct = res.get("shadow_correct", {}).get("accuracy", 0.0)

    gap_buggy = abs(prod_acc - shadow_buggy)
    gap_correct = abs(prod_acc - shadow_correct)

    if gap_correct >= gap_buggy and gap_buggy > 0.01:
        return False, f"eval mode did not reduce accuracy gap (buggy={gap_buggy:.4f}, correct={gap_correct:.4f})"
    return True, f"eval mode reduces gap: buggy={gap_buggy:.4f} → correct={gap_correct:.4f}"


def check_dropout_effect_visible():
    """shadow_buggy should be noticeably worse than shadow_correct (dropout hurts)."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    buggy = res.get("shadow_buggy", {}).get("accuracy", 0.0)
    correct = res.get("shadow_correct", {}).get("accuracy", 0.0)
    diff = correct - buggy
    if diff < 0.01:
        return False, f"Dropout effect small (correct-buggy={diff:.4f}) — dropout_rate=0.3 should matter"
    return True, f"Dropout degrades shadow: buggy={buggy:.4f} vs correct={correct:.4f} (diff={diff:.4f})"


def check_prod_model_unaffected():
    """Production model should still be in eval mode."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    prod_eval = res.get("prod_in_eval", False)
    if not prod_eval:
        return False, "prod_in_eval=False — production model mode changed"
    return True, "prod_in_eval=True (production model unchanged)"


def check_confidence_comparable():
    """After fix, shadow confidence should be similar to production (no dropout noise)."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    prod_conf = res.get("production", {}).get("mean_confidence", 0.0)
    # shadow_correct is the reference (eval mode)
    shadow_conf = res.get("shadow_correct", {}).get("mean_confidence", 0.0)
    diff = abs(prod_conf - shadow_conf)
    if diff > 0.20:
        return False, f"Confidence gap large: prod={prod_conf:.4f}, shadow={shadow_conf:.4f} (diff={diff:.4f})"
    return True, f"Confidence comparable: prod={prod_conf:.4f}, shadow={shadow_conf:.4f}"


def check_fair_comparison_possible():
    """After fix, shadow model comparison should be valid."""
    with open("shadow_results.json") as f:
        res = json.load(f)
    # Both models should report accuracy from eval mode
    prod_acc = res.get("production", {}).get("accuracy", 0.0)
    shadow_acc = res.get("shadow_correct", {}).get("accuracy", 0.0)
    if prod_acc == 0 or shadow_acc == 0:
        return False, "accuracy values missing or zero"
    return True, f"Fair comparison: prod={prod_acc:.4f}, shadow={shadow_acc:.4f}"


def check():
    checks = [
        check_results_exist,
        check_eval_mode_match,
        check_shadow_in_eval,
        check_no_shadow_train_mode_in_code,
        check_shadow_model_eval_called,
        check_accuracy_gap_reduced,
        check_dropout_effect_visible,
        check_prod_model_unaffected,
        check_confidence_comparable,
        check_fair_comparison_possible,
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
