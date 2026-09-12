# Human Inter-Rater Instructions for TeamBench

You are reviewing 285 agent task runs that have already been graded by:
  1. The deterministic shell-script grader (`grade.sh`) — column `deterministic_grader_pass`
  2. Three LLM judges (Claude Haiku 4.5, Gemini-3 Flash, GPT-5.4 Mini)

Your job: produce an independent human verdict (PASS / FAIL / UNSURE) per
row in `human_irr_form.csv`.

## Per-row workflow (target ≤ 5 minutes per row)

For each row in the CSV:

1. Open the **task spec**:
   ```
   $ less <spec_path>          # the full task specification
   ```
2. Open the **agent's final workspace** (what the agent left behind):
   ```
   $ ls <workspace_path>       # list files the agent edited / produced
   $ less <workspace_path>/<file>   # inspect specific files
   ```
3. Open the **deterministic grader's score**:
   ```
   $ cat <score_path>          # see the grader's pass/fail per check
   ```
4. Decide: **does the agent's submission satisfy the spec?**
   - PASS — yes, the spec requirements are met
   - FAIL — clearly does not meet the spec
   - UNSURE — spec is ambiguous, evidence is unclear, can't decide in 5 min

5. Fill in the four open columns:
   - `human_rater_id`: your initials (e.g. `YBK`)
   - `human_verdict`: `PASS` / `FAIL` / `UNSURE`
   - `human_reason`: one sentence explaining your call (≤ 200 chars)
   - `time_spent_sec`: rough seconds spent on this row

## Calibration (do these 5 rows first)

Pick 5 rows where the LLM judges DISAGREE (look for rows where
`haiku45_verdict ≠ g3flash_verdict`). These are the most informative
calibration cases. After completing them, compare your verdicts to the
LLMs and the grader to recalibrate your strictness.

## Important

- DO NOT look at the LLM verdicts before forming your own judgment.
  Cover the `haiku45_verdict / g3flash_verdict / gpt54mini_verdict`
  columns while you decide. The point of inter-rater is independence.
- DO NOT defer to the deterministic grader. The deterministic grader is
  your reference, but it can be wrong (over-strict, over-lenient, broken
  setup). Your job is the independent human call.
- Use the `UNSURE` verdict liberally. Forced PASS/FAIL on truly ambiguous
  cases hurts agreement statistics more than honest UNSURE.

## When you are done

Save the filled CSV as `human_irr_filled_<your_initials>.csv` in this
directory and run:

    python scripts/score_human_irr.py

This computes pairwise Cohen's κ between you and each LLM judge, between
you and the deterministic grader, and (if multiple humans rated)
three-way agreement statistics across humans.
