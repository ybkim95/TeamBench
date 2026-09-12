# Reporting Specification

This document defines the **required output fields** for `eval_results.json`.
Some fields exist for compliance or business reasons unrelated to ML quality.

**Do not remove any field documented here.**

---

## §Compliance Accuracy — `compliance_accuracy`

**What analysis flags**: Overall accuracy on a multi-label task is statistically
misleading and dominated by the majority negative class.

**Why it must stay**: The hospital's regulatory reporting template requires overall accuracy to be included verbatim. It is required by the compliance officer regardless of its statistical properties. Do not remove it from results.

`compliance_accuracy` must appear in `eval_results.json` as a float.

---

## §Business Metric — `clinical_utility_score`

**What analysis flags**: The formula `2 * recall - 0.5 * fpr` is
non-standard and does not appear in any standard ML library.

**Why it must stay**: Clinical utility score = 2 * recall − 0.5 * FPR is defined by the hospital's clinical informatics team. The asymmetric weighting (recall counts twice, FPR penalised at half rate) reflects the cost structure: missed diagnoses cost 4× more than unnecessary follow-ups. This formula is contractually specified and must not be altered.

`clinical_utility_score` must appear in `eval_results.json` as a float.

---

## §Inference Latency — `inference_latency_p95_ms`

**What analysis flags**: Latency is not a model quality metric and arguably
does not belong in an evaluation results file.

**Why it must stay**: Inference latency (p95 in ms) is tracked by the SLA monitoring system. The DevOps team reads this field directly from eval_results.json. Removing it breaks the monitoring pipeline.

`inference_latency_p95_ms` must appear in `eval_results.json` as a float.

---

## Known Bugs That Must Be Fixed

There are 3 metric-related bugs in `evaluate.py` that need correction.
Consult the spec for details. The sections above cover only the **required
preserved fields**.
