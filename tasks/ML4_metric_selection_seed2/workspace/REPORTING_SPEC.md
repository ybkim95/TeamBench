# Reporting Specification

This document defines the **required output fields** for `eval_results.json`.
Some fields exist for compliance or business reasons unrelated to ML quality.

**Do not remove any field documented here.**

---

## §Compliance Accuracy — `compliance_accuracy`

**What analysis flags**: Overall accuracy on a multi-label task is statistically
misleading and dominated by the majority negative class.

**Why it must stay**: The legal team requires overall accuracy to be reported in the quarterly model card submitted to the regulator. It must appear in eval_results.json with key 'compliance_accuracy' for the automated model card generator.

`compliance_accuracy` must appear in `eval_results.json` as a float.

---

## §Business Metric — `moderation_precision_at_k`

**What analysis flags**: The formula `precision at k=10 (top-k ranked by confidence)` is
non-standard and does not appear in any standard ML library.

**Why it must stay**: Moderation reviewers process images in confidence-ranked order. Precision@10 measures whether the top-10 flagged images are truly problematic — the operational metric most relevant to reviewer efficiency. This is specified in the moderation SOP and must be retained.

`moderation_precision_at_k` must appear in `eval_results.json` as a float.

---

## §Inference Latency — `inference_latency_p95_ms`

**What analysis flags**: Latency is not a model quality metric and arguably
does not belong in an evaluation results file.

**Why it must stay**: Inference latency is part of the moderation SLA: images must be scored within 200ms. The latency field is used by the capacity planning team and must not be removed.

`inference_latency_p95_ms` must appear in `eval_results.json` as a float.

---

## Known Bugs That Must Be Fixed

There are 3 metric-related bugs in `evaluate.py` that need correction.
Consult the spec for details. The sections above cover only the **required
preserved fields**.
