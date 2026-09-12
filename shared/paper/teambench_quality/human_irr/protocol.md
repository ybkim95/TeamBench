# TeamBench Human Inter-Rater Protocol

## Sample
- N = 285 (task, condition, run) tuples drawn from the LB100 ablation runs
- Stratified by (LB100 category, condition) using random.Random(seed=0).shuffle
- Same sample as scripts/llm_inter_rater.py, allowing direct human-vs-LLM comparison

## Raters
- Target: ≥ 2 independent human raters for κ statistics
- Each rater independently completes all 285 rows
- Optional: stratify the 285 across raters if time-constrained, but report
  pairwise agreement only on overlapping subset

## Scoring scheme
- PASS / FAIL / UNSURE (UNSURE excluded from κ computation)
- Independent of the deterministic grader and LLM judges
- One-sentence human-reason logged per row

## Statistics computed
- Pairwise Cohen's κ between humans (if ≥ 2)
- Pairwise Cohen's κ between each human and each of:
  - the deterministic grader
  - each of the 3 LLM judges (haiku45, g3flash, gpt54mini)
- Three-way Fleiss's κ (humans + grader if 2+ humans, or each LLM-vs-human pair)
- Binary Krippendorff's α with UNSURE treated as missing

## Threshold for paper
- Cohen's κ ≥ 0.6 (substantial agreement, Landis & Koch 1977) between
  humans and the deterministic grader is sufficient to claim the grader
  reproduces human judgment.
- κ < 0.4 on any task category indicates the grader needs review
  in that category.

## Reproducibility
- The 285-row CSV is reproducible from llm_inter_rater.json by re-running
  scripts/export_human_irr_csv.py
- The seed for the LLM-rater sampling was 0 (in scripts/llm_inter_rater.py)
