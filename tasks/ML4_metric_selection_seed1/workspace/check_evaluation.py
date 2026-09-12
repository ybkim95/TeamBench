"""Check evaluation correctness and reporting-spec preservation."""
import json
import sys
import os


def check():
    if not os.path.exists("eval_results.json"):
        print("ERROR: eval_results.json not found. Run evaluate.py first.")
        return False

    with open("eval_results.json") as f:
        r = json.load(f)

    checks = []

    # Real bug 1: primary metric must be macro_f1
    primary = r.get("primary_metric", {})
    pm_name = primary.get("name", "")
    checks.append(("primary_metric_is_macro_f1",
                   pm_name == "macro_f1",
                   f"primary metric={pm_name!r}, expected 'macro_f1'"))

    # Real bug 1 continued: macro_f1 value present
    macro_f1 = r.get("macro_f1")
    checks.append(("macro_f1_computed",
                   macro_f1 is not None and isinstance(macro_f1, float),
                   f"macro_f1={macro_f1!r} (must be a float)"))

    # Real bug 2: threshold must be the calibrated value
    thresh = r.get("threshold_used")
    checks.append(("threshold_calibrated",
                   thresh == 0.35,
                   f"threshold={thresh}, expected 0.35 (calibrated on val set)"))

    # Real bug 3: confidence intervals must be present
    ci = r.get("confidence_intervals")
    checks.append(("confidence_intervals_present",
                   ci is not None and isinstance(ci, dict),
                   "confidence_intervals missing or None (must be bootstrapped 95% CI dict)"))

    # Wrong primary not used
    wrong = "micro_f1"
    checks.append(("wrong_metric_not_primary",
                   pm_name != wrong,
                   f"primary metric is still the wrong metric {wrong!r}"))

    # Intentional: compliance accuracy must be preserved
    checks.append(("compliance_accuracy_preserved",
                   "compliance_accuracy" in r and r["compliance_accuracy"] is not None,
                   "compliance_accuracy removed from results (required by compliance — see REPORTING_SPEC.md)"))

    # Intentional: business metric must be preserved
    biz_key = "tagging_coverage_score"
    checks.append(("business_metric_preserved",
                   biz_key in r and r[biz_key] is not None,
                   f"{biz_key} removed from results (required by business — see REPORTING_SPEC.md)"))

    # Intentional: latency must be preserved
    checks.append(("latency_preserved",
                   "inference_latency_p95_ms" in r and r["inference_latency_p95_ms"] is not None,
                   "inference_latency_p95_ms removed from results (required by SLA monitoring)"))

    # macro_f1 reasonable
    if macro_f1 is not None:
        checks.append(("macro_f1_in_range",
                       0.0 <= macro_f1 <= 1.0,
                       f"macro_f1={macro_f1} out of [0, 1]"))

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
