"""Check that serving output matches training output."""
import json
import sys
import os


def check():
    # First ensure training artifacts exist
    if not os.path.exists("model.pkl"):
        print("ERROR: model.pkl not found. Run train_model.py first.")
        return False

    if not os.path.exists("serving_results.json"):
        print("ERROR: serving_results.json not found. Run serve.py first.")
        return False

    with open("serving_results.json") as f:
        r = json.load(f)

    checks = []

    # Check agreement > 95%
    agreement = r.get("agreement_with_training", 0)
    checks.append(("agreement_high",
                   agreement > 0.95,
                   f"agreement={agreement:.3f}, must be >0.95"))

    # Check predictions_match flag
    checks.append(("predictions_match_flag",
                   r.get("predictions_match", False),
                   "predictions_match flag is False"))

    # Check preprocessing_artifacts loaded
    if os.path.exists("preprocessing_artifacts.json"):
        with open("preprocessing_artifacts.json") as f:
            arts = json.load(f)
        checks.append(("artifacts_loaded", True, "preprocessing_artifacts.json present"))
    else:
        checks.append(("artifacts_loaded", False, "preprocessing_artifacts.json missing"))

    # Check n_samples reasonable
    n = r.get("n_samples", 0)
    checks.append(("samples_processed",
                   n > 0,
                   f"n_samples={n}"))

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
