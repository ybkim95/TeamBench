"""Check curriculum pacing function fix."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curriculum import pacing_function


def check_pacing():
    """Verify pacing function goes from start_fraction to 1.0."""
    sf = 0.3
    total = 50

    pace_start = pacing_function(0, total, sf)
    pace_end = pacing_function(total - 1, total, sf)
    pace_mid = pacing_function(total // 2, total, sf)

    # At epoch 0: should be close to start_fraction
    if pace_start > sf + 0.05:
        return False, (
            f"Pacing at epoch 0 = {pace_start:.4f}, expected ~{sf:.4f}. "
            f"Function is inverted (starts at 1.0 instead of {sf:.4f})."
        )

    # At final epoch: should be close to 1.0
    if pace_end < 0.95:
        return False, (
            f"Pacing at final epoch = {pace_end:.4f}, expected ~1.0. "
            f"Curriculum should use all data by the end."
        )

    # Should be monotonically increasing
    paces = [pacing_function(e, total, sf) for e in range(total)]
    is_increasing = all(paces[i] <= paces[i+1] + 1e-9 for i in range(len(paces)-1))
    if not is_increasing:
        return False, f"Pacing function is not monotonically increasing: {paces[:5]} ... {paces[-3:]}"

    return True, f"Pacing correct: start={pace_start:.3f} mid={pace_mid:.3f} end={pace_end:.3f}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    metric = res.get("final_val_metric", 0)
    pacing_start = res.get("pacing_start", None)
    pacing_end = res.get("pacing_end", None)
    print(f"Final val metric: {metric:.4f}")
    if pacing_start is not None:
        print(f"Pacing: start={pacing_start:.3f} end={pacing_end:.3f}")

    ok, msg = check_pacing()
    print(f"Pacing check: {msg}")
    if not ok:
        return False

    if not res.get("converged", False):
        print(f"FAIL: Did not converge (metric={metric:.4f})")
        return False

    print("PASS")
    return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
