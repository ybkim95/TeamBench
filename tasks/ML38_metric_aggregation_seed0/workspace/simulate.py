"""Simulate A/B test data with Simpson\'s paradox setup."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics import compare_groups, compute_ctr, compute_ctr_correct


def simulate_sessions(n_sessions: int, heavy_frac: float,
                      heavy_imp_range: tuple, normal_imp_range: tuple,
                      heavy_ctr: float, normal_ctr: float,
                      rng: np.random.RandomState) -> tuple:
    """Generate session-level data with two user types.

    Heavy users: many impressions per session, low CTR
    Normal users: few impressions per session, high CTR
    """
    clicks, impressions = [], []
    n_heavy = int(n_sessions * heavy_frac)

    for i in range(n_sessions):
        if i < n_heavy:
            # Heavy user: many impressions, low CTR
            imp = rng.randint(heavy_imp_range[0], heavy_imp_range[1] + 1)
            rate = heavy_ctr
        else:
            # Normal user: few impressions, high CTR
            imp = rng.randint(normal_imp_range[0], normal_imp_range[1] + 1)
            rate = normal_ctr

        clk = rng.binomial(imp, rate)
        clicks.append(int(clk))
        impressions.append(int(imp))

    return clicks, impressions


def run_simulation():
    rng_ctrl = np.random.RandomState(42)
    rng_trt = np.random.RandomState(43)

    # Control group
    ctrl_clicks, ctrl_impressions = simulate_sessions(
        n_sessions=2000,
        heavy_frac=0.1,
        heavy_imp_range=(50, 200),
        normal_imp_range=(2, 10),
        heavy_ctr=0.03,
        normal_ctr=0.15,
        rng=rng_ctrl,
    )

    # Treatment group: slightly more heavy users (causes Simpson\'s paradox in raw CTR)
    # Treatment normal_ctr is actually LOWER than control
    trt_clicks, trt_impressions = simulate_sessions(
        n_sessions=2000,
        heavy_frac=0.200,   # more heavy users in treatment
        heavy_imp_range=(50, 200),
        normal_imp_range=(2, 10),
        heavy_ctr=0.03,
        normal_ctr=0.1275,     # treatment actually worse for normal users
        rng=rng_trt,
    )

    # Compute with buggy raw-count method
    comparison = compare_groups(ctrl_clicks, ctrl_impressions, trt_clicks, trt_impressions)

    # Compute correct per-session method for reference
    ctrl_ctr_correct = compute_ctr_correct(ctrl_clicks, ctrl_impressions)
    trt_ctr_correct = compute_ctr_correct(trt_clicks, trt_impressions)
    honest_lift = trt_ctr_correct - ctrl_ctr_correct

    results = {
        "raw_count": comparison,
        "per_session": {
            "control_ctr": round(ctrl_ctr_correct, 6),
            "treatment_ctr": round(trt_ctr_correct, 6),
            "absolute_lift": round(honest_lift, 6),
            "relative_lift": round(honest_lift / ctrl_ctr_correct if ctrl_ctr_correct > 0 else 0, 4),
            "method": "per_session_average",
        },
        "simpson_paradox_present": comparison["absolute_lift"] > 0 and honest_lift < 0,
        "n_sessions_per_group": 2000,
        "heavy_user_fraction": 0.1,
    }

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Raw-count CTR:   ctrl={comparison['control_ctr']:.4f}, "
          f"trt={comparison['treatment_ctr']:.4f}, lift={comparison['absolute_lift']:+.4f}")
    print(f"Per-session CTR: ctrl={ctrl_ctr_correct:.4f}, "
          f"trt={trt_ctr_correct:.4f}, lift={honest_lift:+.4f}")
    print(f"Simpson\'s paradox present: {results['simpson_paradox_present']}")
    return results


if __name__ == "__main__":
    run_simulation()
