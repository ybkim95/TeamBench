"""Check distributed training correctness."""
import json
import sys
import os


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found.")
        return False

    with open("training_results.json") as f:
        r = json.load(f)

    checks = []

    # Check 1: training ran (history exists)
    hist = r.get("history", [])
    checks.append(("history_present",
                   len(hist) >= 5,
                   f"history has {len(hist)} entries, expected >= 5"))

    # Check 2: loss decreased (converged)
    if len(hist) >= 2:
        first_loss = hist[0].get("loss", float("inf"))
        last_loss = hist[-1].get("loss", float("inf"))
        checks.append(("loss_decreased",
                       last_loss < first_loss * 0.9,
                       f"loss did not decrease: first={first_loss:.4f} last={last_loss:.4f}"))

    # Check 3: no NaN in losses
    import math
    nan_entries = [h for h in hist if math.isnan(h.get("loss", 0))]
    checks.append(("no_nan_loss",
                   len(nan_entries) == 0,
                   f"{len(nan_entries)} epochs with NaN loss"))

    # Check 4: converged flag
    checks.append(("converged",
                   r.get("converged", False),
                   "converged flag is False"))

    # Check 5: final loss below 1.0
    final_loss = r.get("final_loss", float("inf"))
    checks.append(("final_loss_reasonable",
                   final_loss < 1.0,
                   f"final_loss={final_loss:.4f} >= 1.0"))

    all_pass = True
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_pass = False

    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
