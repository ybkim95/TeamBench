# Reporting Specification

This document defines the **required output fields** for `eval_results.json`.
Some fields exist for compliance or business reasons unrelated to ML quality.

**Do not remove any field documented here.**

---

## §Compliance Accuracy — `compliance_accuracy`

**What analysis flags**: Overall accuracy on a multi-label task is statistically
misleading and dominated by the majority negative class.

**Why it must stay**: The product dashboard shows overall accuracy to editorial staff who are non-technical. This metric is in the product spec and must remain in results even though it is not the primary evaluation criterion.

`compliance_accuracy` must appear in `eval_results.json` as a float.

---

## §Business Metric — `tagging_coverage_score`

**What analysis flags**: The formula `recall * (1 - 0.3 * (1 - precision))` is
non-standard and does not appear in any standard ML library.

**Why it must stay**: Coverage score = recall × (1 − 0.3 × (1 − precision)) is specified by the product team. It penalises low precision only lightly (0.3 factor) because partially-correct tags are acceptable in the product. This formula is in the product requirements document and must not be changed.

`tagging_coverage_score` must appear in `eval_results.json` as a float.

---

## §Inference Latency — `inference_latency_p95_ms`

**What analysis flags**: Latency is not a model quality metric and arguably
does not belong in an evaluation results file.

**Why it must stay**: Inference latency is in the product SLA. The infrastructure team's alerting system reads `inference_latency_p95_ms` from eval_results.json. If it is missing, alerts fire and the on-call engineer is paged.

`inference_latency_p95_ms` must appear in `eval_results.json` as a float.

---

## Known Bugs That Must Be Fixed

There are 3 metric-related bugs in `evaluate.py` that need correction.
Consult the spec for details. The sections above cover only the **required
preserved fields**.
