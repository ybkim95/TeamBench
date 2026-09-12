"""A/B test data generator for search_algorithm experiment."""
import json
import numpy as np


def generate_ab_data(seed: int = 42) -> dict:
    """Generate daily A/B test metrics with novelty effect.

    Treatment group experiences:
    - Days 0-9 (novelty period): base_ctr + 0.06 boost (novelty effect)
    - Days 10-34 (steady state): base_ctr + -0.02 delta (real effect)

    Control group: base_ctr throughout (no novelty, no algorithm change)
    """
    rng = np.random.RandomState(seed)
    n_days = 35
    novelty_window = 10
    base_ctr = 0.05
    n_users_per_day = 6000

    control_daily = []
    treatment_daily = []

    for day in range(n_days):
        # Control: stable around base_ctr
        control_successes = rng.binomial(n_users_per_day, base_ctr)
        control_ctr = control_successes / n_users_per_day

        # Treatment: novelty boost early, true delta later
        if day < novelty_window:
            # Novelty effect: users engage more with new algorithm just because it's new
            true_rate = base_ctr + 0.06
        else:
            # Steady state: algorithm actually underperforms
            true_rate = base_ctr + -0.02

        true_rate = max(0.001, min(0.999, true_rate))
        treatment_successes = rng.binomial(n_users_per_day, true_rate)
        treatment_ctr = treatment_successes / n_users_per_day

        control_daily.append({
            "day": day,
            "group": "control",
            "ctr": round(control_ctr, 6),
            "n_users": n_users_per_day,
            "period": "novelty" if day < novelty_window else "steady_state",
        })
        treatment_daily.append({
            "day": day,
            "group": "treatment",
            "ctr": round(treatment_ctr, 6),
            "n_users": n_users_per_day,
            "period": "novelty" if day < novelty_window else "steady_state",
        })

    data = {
        "control": control_daily,
        "treatment": treatment_daily,
        "metadata": {
            "n_days": n_days,
            "novelty_window": novelty_window,
            "base_ctr": base_ctr,
            "novelty_boost": 0.06,
            "steady_state_delta": -0.02,
            "metric": "click_through_rate",
        },
    }
    with open("ab_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {n_days} days of A/B data (novelty window: {novelty_window} days)")
    return data


if __name__ == "__main__":
    generate_ab_data()
