"""Validate A/B novelty effect analysis fix."""
import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_results_exist():
    if not os.path.exists("ab_results.json"):
        return False, "ab_results.json not found"
    return True, "ab_results.json exists"


def check_decision_basis_is_steady_state():
    """Check decision is based on steady-state, not overall lift."""
    with open("ab_results.json") as f:
        res = json.load(f)
    basis = res.get("decision_basis", "unknown")
    if basis != "steady_state":
        return False, f"decision_basis=\'{basis}\' (expected \'steady_state\')"
    return True, "decision_basis=\'steady_state\'"


def check_no_ship_due_to_negative_steady_state():
    """Treatment should NOT be shipped — steady-state lift is negative."""
    with open("ab_results.json") as f:
        res = json.load(f)
    ship = res.get("ship_decision", True)
    ss_lift = res.get("steady_state_lift_abs", 0.0)
    if ship and ss_lift < 0:
        return False, f"ship_decision=True despite steady_state_lift={ss_lift:.4f} < 0 (novelty effect bug)"
    if not ship:
        return True, f"ship_decision=False (correct — steady_state_lift={ss_lift:.4f})"
    return True, f"ship_decision=False or steady_state_lift >= 0 ({ss_lift:.4f})"


def check_steady_state_lift_computed():
    """Steady-state lift should be computed and negative."""
    with open("ab_results.json") as f:
        res = json.load(f)
    ss = res.get("steady_state_lift_abs", None)
    if ss is None:
        return False, "steady_state_lift_abs not in results"
    if ss >= 0:
        return False, f"steady_state_lift_abs={ss:.4f} >= 0 (expected negative — test data has negative steady-state)"
    return True, f"steady_state_lift_abs={ss:.4f} < 0 (correct)"


def check_overall_lift_positive():
    """Overall lift should be positive (novelty effect inflates it)."""
    with open("ab_results.json") as f:
        res = json.load(f)
    overall = res.get("overall_lift_abs", None)
    if overall is None:
        return False, "overall_lift_abs not in results"
    if overall <= 0:
        return False, f"overall_lift_abs={overall:.4f} <= 0 (expected positive due to novelty)"
    return True, f"overall_lift_abs={overall:.4f} > 0 (novelty inflates overall)"


def check_novelty_window_correct():
    """Novelty window should be 5 days."""
    with open("ab_results.json") as f:
        res = json.load(f)
    nw = res.get("novelty_window_days", None)
    if nw is None:
        return False, "novelty_window_days not in results"
    if nw != 5:
        return False, f"novelty_window_days={nw} (expected 5)"
    return True, f"novelty_window_days={nw} correct"


def check_code_uses_late_lift_for_decision():
    """analyze.py should use late/steady-state lift for ship decision."""
    with open("analyze.py") as f:
        src = f.read()
    active_lines = [l for l in src.split("\n") if not l.lstrip().startswith("#")]
    active_src = "\n".join(active_lines)
    uses_late = bool(re.search(r"ship_decision\s*=\s*late_abs|ship_decision\s*=\s*steady_state", active_src))
    if not uses_late:
        return False, "ship_decision not based on late_abs or steady_state lift"
    return True, "ship_decision correctly uses steady-state lift"


def check_novelty_lift_also_reported():
    """Novelty lift should still be reported (not deleted)."""
    with open("ab_results.json") as f:
        res = json.load(f)
    nl = res.get("novelty_lift_abs", None)
    if nl is None:
        return False, "novelty_lift_abs not in results (should still be reported)"
    return True, f"novelty_lift_abs={nl:.4f} present"


def check_ab_data_exists():
    if not os.path.exists("ab_data.json"):
        return False, "ab_data.json not found"
    with open("ab_data.json") as f:
        data = json.load(f)
    n_ctrl = len(data.get("control", []))
    n_trt = len(data.get("treatment", []))
    if n_ctrl != 21 or n_trt != 21:
        return False, f"Expected 21 days, got control={n_ctrl}, treatment={n_trt}"
    return True, f"ab_data.json has 21 days for each group"


def check():
    checks = [
        check_results_exist,
        check_decision_basis_is_steady_state,
        check_no_ship_due_to_negative_steady_state,
        check_steady_state_lift_computed,
        check_overall_lift_positive,
        check_novelty_window_correct,
        check_code_uses_late_lift_for_decision,
        check_novelty_lift_also_reported,
        check_ab_data_exists,
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
