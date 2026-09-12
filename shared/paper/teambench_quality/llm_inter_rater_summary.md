# LLM Inter-Rater Agreement on TeamBench Graders

_Computed 2026-04-30T17:10:19.925533+00:00, n_judgments=285, n_valid=285._
_Estimated OpenRouter spend ≈ $34.2._

## Pairwise Cohen's κ between judges
| Pair | κ |
|---|---|
| haiku45 vs g3flash | 0.6603 |
| haiku45 vs gpt54mini | 0.9068 |
| g3flash vs gpt54mini | 0.6998 |

**Three-way Fleiss's κ**: 0.7423
**Binary Krippendorff's α**: 0.7426

## Each LLM judge vs deterministic grader (reference)
| Judge | agreement | κ vs grader | LLM-pass when grader=fail | LLM-fail when grader=pass |
|---|---|---|---|---|
| haiku45 | 0.9895 | 0.9577 | 0.0082 | 0.0244 |
| g3flash | 0.8842 | 0.6478 | 0.1352 | 0.0 |
| gpt54mini | 0.9649 | 0.8657 | 0.0328 | 0.0488 |
