"""Validate CTR metric aggregation fix."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("simulation_results.json"):
        return False, "simulation_results.json not found"
    return True, "simulation_results.json exists"


def check_method_is_per_session():
    """compare_groups should use per_session_average method."""
    with open("simulation_results.json") as f:
        res = json.load(f)
    method = res.get("raw_count", {}).get("method", "raw_counts")
    if method == "raw_counts":
        return False, "compare_groups still uses raw_counts method"
    method2 = res.get("raw_count", {}).get("method", "")
    if "per_session" not in method2 and "per_session" not in str(res.get("per_session", {}).get("method", "")):
        return False, f"method not updated to per_session_average (got: {method})"
    return True, f"method updated to per_session ({method})"


def check_no_raw_count_bug():
    """compute_ctr should use per-session averaging, not raw counts."""
    with open("metrics.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    # Check that compute_ctr no longer uses total_clicks / total_impressions as return
    still_raw = bool(re.search(r"return\s+total_clicks\s*/\s*total_impressions", active_src))
    if still_raw:
        return False, "compute_ctr still returns total_clicks / total_impressions (raw count)"
    return True, "compute_ctr no longer uses raw count formula"


def check_per_session_formula_used():
    """compute_ctr should compute per-session rates and average them."""
    with open("metrics.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    has_per_session = bool(re.search(
        r"per_session|np\.mean\s*\(|sum.*zip|for.*zip|c\s*/\s*i|clicks.*impressions.*zip",
        active_src
    ))
    if not has_per_session:
        return False, "compute_ctr does not appear to compute per-session rates"
    return True, "compute_ctr uses per-session rate computation"


def check_compare_groups_uses_correct_method():
    """compare_groups should call compute_ctr (fixed version)."""
    with open("metrics.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)

    # compare_groups should set method to per_session_average
    uses_per_session_method = bool(re.search(r'"per_session_average"', active_src))
    if not uses_per_session_method:
        return False, "compare_groups still sets method to raw_counts"
    return True, "compare_groups sets method to per_session_average"


def check_simpsons_paradox_detected():
    """Simulation should still detect Simpson\'s paradox (raw count gives wrong sign)."""
    with open("simulation_results.json") as f:
        res = json.load(f)
    sp = res.get("simpson_paradox_present", None)
    if sp is None:
        return False, "simpson_paradox_present not in results"
    if not sp:
        return False, "simpson_paradox_present=False — simulation data should exhibit paradox"
    return True, "simpson_paradox_present=True (raw CTR misled, per-session correct)"


def check_per_session_lift_negative():
    """Per-session CTR lift should be negative (treatment is worse for most users)."""
    with open("simulation_results.json") as f:
        res = json.load(f)
    per_sess = res.get("per_session", {})
    lift = per_sess.get("absolute_lift", 0.0)
    if lift >= 0:
        return False, f"per_session absolute_lift={lift:.4f} >= 0 (expected negative)"
    return True, f"per_session absolute_lift={lift:.4f} < 0 (treatment is worse per session)"


def check_raw_count_lift_positive():
    """Raw count CTR lift should be positive (deceiving — that\'s the bug)."""
    with open("simulation_results.json") as f:
        res = json.load(f)
    raw = res.get("raw_count", {})
    lift = raw.get("absolute_lift", 0.0)
    if lift <= 0:
        return False, f"raw_count absolute_lift={lift:.4f} <= 0 (expected positive to show paradox)"
    return True, f"raw_count absolute_lift={lift:.4f} > 0 (raw count misleads)"


def check_simulation_ran():
    """Check simulation produced valid session counts."""
    with open("simulation_results.json") as f:
        res = json.load(f)
    n = res.get("n_sessions_per_group", 0)
    if n != 2000:
        return False, f"n_sessions_per_group={n} (expected 2000)"
    return True, f"n_sessions_per_group=2000"


def check():
    checks = [
        check_results_exist,
        check_no_raw_count_bug,
        check_per_session_formula_used,
        check_compare_groups_uses_correct_method,
        check_method_is_per_session,
        check_simpsons_paradox_detected,
        check_per_session_lift_negative,
        check_raw_count_lift_positive,
        check_simulation_ran,
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
