"""Validate drift detector fix — must monitor P(X) not P(Y_hat)."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("drift_results.json"):
        return False, "drift_results.json not found"
    return True, "drift_results.json exists"


def check_monitor_type_is_features():
    """monitor_type must be \'features\' not \'predictions\'."""
    with open("drift_results.json") as f:
        res = json.load(f)
    mt = res.get("monitor_type", "unknown")
    if mt == "predictions":
        return False, "monitor_type=\'predictions\' — still monitoring P(Y_hat)"
    if "feature" not in mt:
        return False, f"monitor_type=\'{mt}\' — expected \'features\'"
    return True, f"monitor_type=\'{mt}\'"


def check_drift_detected():
    """With a 2.0-sigma shift, feature drift must be detected."""
    with open("drift_results.json") as f:
        res = json.load(f)
    detected = res.get("drift_detected", False)
    if not detected:
        return False, f"drift_detected=False — 2.0-sigma shift should be detected"
    return True, "drift_detected=True (covariate shift correctly flagged)"


def check_no_prediction_ks_in_code():
    """detect_drift should not compute KS on model predictions."""
    with open("drift_detector.py") as f:
        src = f.read()
    func_match = re.search(r"def detect_drift.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "detect_drift function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    still_pred_ks = bool(re.search(r"ks_2samp\s*\([^)]*preds", active_src))
    if still_pred_ks:
        return False, "detect_drift still runs KS test on prediction distributions"
    return True, "detect_drift no longer uses prediction-based KS"


def check_feature_ks_in_code():
    """detect_drift should compute KS on input features."""
    with open("drift_detector.py") as f:
        src = f.read()
    func_match = re.search(r"def detect_drift.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "detect_drift function not found"

    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    has_feature_ks = bool(re.search(r"ks_2samp.*\[:.*\]|ref_np.*j|curr_np.*j|feature_ks|\.numpy\(\).*j", active_src))
    if not has_feature_ks:
        return False, "detect_drift does not iterate over features for KS test"
    return True, "detect_drift computes feature-level KS statistics"


def check_feature_drift_is_primary_signal():
    """The primary drift_detected flag should use feature-level KS, not prediction KS."""
    with open("drift_results.json") as f:
        res = json.load(f)
    # drift_detected should be True (features are shifted)
    detected = res.get("drift_detected", False)
    feature_drift = res.get("feature_drift_detected", False)

    if not detected:
        return False, "drift_detected=False even though features are shifted"
    if not feature_drift:
        return False, "feature_drift_detected=False — check shift implementation"
    return True, f"drift_detected={detected} matches feature_drift_detected={feature_drift}"


def check_ks_stat_strong():
    """KS statistic on features should be large for a 2.0-sigma shift."""
    with open("drift_results.json") as f:
        res = json.load(f)
    ks = res.get("ks_statistic", 0.0)
    feature_ks = res.get("feature_ks_max", 0.0)

    if feature_ks < 0.2:
        return False, f"feature_ks_max={feature_ks:.4f} low — feature shift should be strong"
    if ks < 0.2:
        return False, f"ks_statistic={ks:.4f} low — should reflect feature distribution, not predictions"
    return True, f"ks_statistic={ks:.4f}, feature_ks_max={feature_ks:.4f} (strong signal)"


def check_p_value_significant():
    """P-value should be very small for a 2.0-sigma covariate shift."""
    with open("drift_results.json") as f:
        res = json.load(f)
    p = res.get("p_value", 1.0)
    if p >= 0.1:
        return False, f"p_value={p:.6f} >= 0.1 threshold — drift not significant"
    return True, f"p_value={p:.6f} < 0.1 (significant drift)"


def check_shift_magnitude_recorded():
    with open("drift_results.json") as f:
        res = json.load(f)
    sm = res.get("shift_magnitude", None)
    if sm is None:
        return False, "shift_magnitude not in results"
    if abs(sm - 2.0) > 0.01:
        return False, f"shift_magnitude={sm} (expected 2.0)"
    return True, f"shift_magnitude=2.0 recorded"


def check_both_reference_and_current_used():
    """detect_drift must use both reference_x and current_x numpy arrays."""
    with open("drift_detector.py") as f:
        src = f.read()
    func_match = re.search(r"def detect_drift.*?(?=\ndef |\nclass |\Z)", src, re.DOTALL)
    if not func_match:
        return False, "detect_drift function not found"
    func_body = func_match.group(0)
    active_lines = [l for l in func_body.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    has_ref_np = bool(re.search(r"ref_np|reference_x\.numpy|reference.*numpy", active_src))
    has_curr_np = bool(re.search(r"curr_np|current_x\.numpy|current.*numpy", active_src))
    if not has_ref_np or not has_curr_np:
        return False, "detect_drift does not convert both reference and current to numpy"
    return True, "detect_drift uses numpy arrays of both reference and current features"


def check():
    checks = [
        check_results_exist,
        check_monitor_type_is_features,
        check_drift_detected,
        check_no_prediction_ks_in_code,
        check_feature_ks_in_code,
        check_feature_drift_is_primary_signal,
        check_ks_stat_strong,
        check_p_value_significant,
        check_shift_magnitude_recorded,
        check_both_reference_and_current_used,
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
