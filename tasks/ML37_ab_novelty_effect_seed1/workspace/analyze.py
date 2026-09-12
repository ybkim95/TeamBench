"""A/B test analysis — BUG: ignores novelty effect by using overall lift."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ab_test import generate_ab_data


def compute_lift(control_vals, treatment_vals):
    """Compute absolute and relative lift."""
    ctrl_mean = np.mean(control_vals)
    trt_mean = np.mean(treatment_vals)
    abs_lift = trt_mean - ctrl_mean
    rel_lift = abs_lift / ctrl_mean if ctrl_mean > 0 else 0.0
    return abs_lift, rel_lift


def analyze():
    """Analyze A/B test and decide whether to ship treatment.

    BUG: Uses overall lift across all time periods.
    The novelty effect inflates early metrics. Steady-state performance
    (after day 5) is negative, but this is ignored.

    Fix: Separate analysis into novelty period and steady-state period.
    Only ship if steady-state lift is positive.
    """
    data = generate_ab_data()

    ctrl = [d["er"] for d in data["control"]]
    trt = [d["er"] for d in data["treatment"]]
    novelty_window = data["metadata"]["novelty_window"]

    # BUG: Overall lift pools novelty + steady-state periods
    overall_abs, overall_rel = compute_lift(ctrl, trt)

    # Correct analysis (not used for decision — BUG)
    early_ctrl = ctrl[:novelty_window]
    early_trt = trt[:novelty_window]
    late_ctrl = ctrl[novelty_window:]
    late_trt = trt[novelty_window:]

    early_abs, early_rel = compute_lift(early_ctrl, early_trt)
    late_abs, late_rel = compute_lift(late_ctrl, late_trt)

    # BUG: Decision based on overall lift — ignores that steady-state is negative
    ship_decision = overall_abs > 0  # BUG: should use late_abs > 0

    results = {
        "overall_lift_abs": round(float(overall_abs), 6),
        "overall_lift_rel": round(float(overall_rel), 4),
        "novelty_lift_abs": round(float(early_abs), 6),
        "novelty_lift_rel": round(float(early_rel), 4),
        "steady_state_lift_abs": round(float(late_abs), 6),
        "steady_state_lift_rel": round(float(late_rel), 4),
        "ship_decision": ship_decision,  # BUG: based on overall, not steady-state
        "decision_basis": "overall",     # BUG: should be "steady_state"
        "novelty_window_days": novelty_window,
    }

    with open("ab_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Overall lift:      {overall_abs:+.4f} ({overall_rel:+.2%})")
    print(f"Novelty period:    {early_abs:+.4f} ({early_rel:+.2%})")
    print(f"Steady-state:      {late_abs:+.4f} ({late_rel:+.2%})")
    print(f"Ship decision:     {ship_decision} (basis: {results['decision_basis']})")
    return results


if __name__ == "__main__":
    analyze()
