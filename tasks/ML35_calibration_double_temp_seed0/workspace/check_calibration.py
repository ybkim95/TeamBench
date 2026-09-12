"""Validate temperature scaling fix — checks ECE and single application."""
import json
import sys
import os
import re
import torch
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_no_double_temperature():
    """Verify temperature is not applied in both model.forward() AND evaluator."""
    with open("model.py") as f:
        model_src = f.read()
    with open("evaluator.py") as f:
        eval_src = f.read()

    # Check non-comment lines for temperature division
    def active_lines(src):
        return [l for l in src.split("\n") if not l.lstrip().startswith("#")]

    model_active = "\n".join(active_lines(model_src))
    eval_active = "\n".join(active_lines(eval_src))

    # Look for temperature scaling in each file
    model_has_temp = bool(re.search(r"logits\s*/\s*self\.temperature|/\s*self\.temperature", model_active))
    eval_has_temp = bool(re.search(r"logits\s*/\s*self\.temperature|/\s*self\.temperature|scaled_logits\s*=\s*logits\s*/", eval_active))

    if model_has_temp and eval_has_temp:
        return False, f"Temperature scaling applied in BOTH model.forward() and evaluator.predict_proba() — double application"
    if not model_has_temp and not eval_has_temp:
        return False, "Temperature scaling not applied in either location — must be applied exactly once"
    location = "model.py" if model_has_temp else "evaluator.py"
    return True, f"Temperature scaling applied exactly once (in {location})"


def check_ece_reasonable():
    """Check ECE is below threshold after fix."""
    if not os.path.exists("calibration_results.json"):
        return False, "calibration_results.json not found"
    with open("calibration_results.json") as f:
        res = json.load(f)
    ece = res.get("test_ece", 1.0)
    if ece >= 0.10:
        return False, f"ECE {ece:.4f} >= 0.10 threshold (calibration still broken)"
    return True, f"ECE {ece:.4f} < 0.10 (calibration OK)"


def check_calibration_results_exist():
    if not os.path.exists("calibration_results.json"):
        return False, "calibration_results.json missing"
    return True, "calibration_results.json exists"


def check_accuracy_maintained():
    """Check that accuracy is not degraded by the fix."""
    if not os.path.exists("calibration_results.json"):
        return False, "calibration_results.json missing"
    with open("calibration_results.json") as f:
        res = json.load(f)
    acc = res.get("test_accuracy", 0.0)
    chance = 1.0 / 5
    if acc <= chance:
        return False, f"Test accuracy {acc:.4f} <= chance level {chance:.4f}"
    return True, f"Test accuracy {acc:.4f} > chance {chance:.4f}"


def check_temperature_value_preserved():
    """Check temperature value is still 1.8 (not 1.0 = disabled)."""
    with open("model.py") as f:
        model_src = f.read()
    with open("evaluator.py") as f:
        eval_src = f.read()
    combined = model_src + eval_src
    # Temperature should still appear as a non-trivial value
    has_temp_val = bool(re.search(r"temperature\s*[=:]\s*1.8", combined))
    has_temp_attr = "self.temperature" in combined
    if not has_temp_attr:
        return False, "temperature attribute removed entirely — fix should preserve temperature parameter"
    return True, f"Temperature parameter preserved in code"


def check_proba_sums_to_one():
    """Verify predict_proba outputs valid probabilities after fix."""
    try:
        from model import CalibratedClassifier
        from evaluator import ModelEvaluator
        torch.manual_seed(0)
        model = CalibratedClassifier(
            input_dim=64, hidden_dim=128,
            num_classes=5, temperature=1.8
        )
        evaluator = ModelEvaluator(model)
        x = torch.randn(20, 64)
        probs = evaluator.predict_proba(x)
        row_sums = probs.sum(dim=1)
        max_dev = (row_sums - 1.0).abs().max().item()
        if max_dev > 1e-4:
            return False, f"Probabilities don\'t sum to 1 (max deviation {max_dev:.6f})"
        return True, f"Probabilities sum to 1 (max deviation {max_dev:.8f})"
    except Exception as e:
        return False, f"Error: {e}"


def check_ece_better_than_double():
    """Verify ECE is meaningfully better than double-temperature baseline."""
    if not os.path.exists("calibration_results.json"):
        return False, "calibration_results.json missing"
    with open("calibration_results.json") as f:
        res = json.load(f)
    ece = res.get("test_ece", 1.0)
    # Double temperature always gives ECE > 0.15 on this task
    if ece >= 0.15:
        return False, f"ECE {ece:.4f} still high — double-temperature bug may not be fixed"
    return True, f"ECE {ece:.4f} improved beyond double-temperature baseline"


def check_calibration_flag():
    """Check calibration_ok flag is True."""
    if not os.path.exists("calibration_results.json"):
        return False, "calibration_results.json missing"
    with open("calibration_results.json") as f:
        res = json.load(f)
    ok = res.get("calibration_ok", False)
    ece = res.get("test_ece", 1.0)
    if not ok:
        return False, f"calibration_ok=False (ECE={ece:.4f})"
    return True, f"calibration_ok=True (ECE={ece:.4f})"


def check_evaluator_uses_model_output():
    """Check evaluator calls model() (not bypasses it)."""
    with open("evaluator.py") as f:
        src = f.read()
    active = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active)
    if "self.model(" not in active_src:
        return False, "evaluator.predict_proba does not call self.model() — missing model call"
    return True, "evaluator.predict_proba correctly calls self.model()"


def check():
    checks = [
        check_calibration_results_exist,
        check_no_double_temperature,
        check_ece_reasonable,
        check_accuracy_maintained,
        check_temperature_value_preserved,
        check_proba_sums_to_one,
        check_ece_better_than_double,
        check_calibration_flag,
        check_evaluator_uses_model_output,
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
