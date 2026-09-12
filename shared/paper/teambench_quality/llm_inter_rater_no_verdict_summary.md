# LLM Inter-Rater Agreement on TeamBench Graders

_Computed 2026-05-01T15:59:24.846916+00:00, n_judgments=285, n_valid=285._
_Estimated OpenRouter spend ≈ $34.2._

## Pairwise Cohen's κ between judges
| Pair | κ |
|---|---|
| haiku45 vs g3flash | 0.1796 |
| haiku45 vs gpt54mini | 0.271 |
| g3flash vs gpt54mini | 0.1012 |

**Three-way Fleiss's κ**: 0.0658
**Binary Krippendorff's α**: 0.0669

## Each LLM judge vs deterministic grader (reference)
| Judge | agreement | κ vs grader | LLM-pass when grader=fail | LLM-fail when grader=pass |
|---|---|---|---|---|
| haiku45 | 0.8175 | 0.1757 | 0.0861 | 0.7561 |
| g3flash | 0.5684 | 0.176 | 0.4795 | 0.1463 |
| gpt54mini | 0.8316 | 0.2031 | 0.0697 | 0.7561 |
