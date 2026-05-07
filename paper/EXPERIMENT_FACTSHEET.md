# TeamBench Experiment Fact Sheet

Authoritative paths and current numbers for the **three** main experiments.
Always re-derive paper numbers from the JSON sources below — do not trust any
hand-typed numbers in the .tex without re-checking against these files.

Paper draft: `<HOME>/TeamBench/paper/v6/neurips_2026.tex`
Last sync: 2026-05-04 (attestation-promotion regrade applied to Figure 3 and Tables 12, 13; gpt-oss-120b added to leaderboard panel; Figure 2(c) now uses objective grader-check bins); previous sync 2026-04-30 against
- `lb90_full_aggregate.json` (2026-04-30, **headline leaderboard**, 90 tasks × 20 models)
- `lb100_full_aggregate.json` (2026-04-29 21:34 UTC, parent — kept for provenance)
- `per_config_3seed.json` (2026-04-29 14:31 UTC)
- `experiments/role_enforcement_ablation/analysis/consolidated.json` (latest run; 400 runs)
- Firebase RTDB tree `teambench_new` pulled via `human_eval/firebase/count_participants.py` (2026-05-01; 30 sessions, 12 humans, 17 distinct task ids)
- `teambench_quality/canonical_pass_check.json` + `mutation_kill.json` + `task_discrimination.json` + `llm_inter_rater.json` + `unknown_triage.json`
- `teambench_verified.json` (LB100 view) + `teambench_verified_lb90.json` (LB90 view; **57 of 90 = 63.3%** is the headline)

**Headline benchmark name (final, paper-ready)**:
- **TeamBench-90** — 90 tasks (LB100 minus 10 broken-grader-post-pr GH-1000+ scrapes)
- **TeamBench-Verified** — 57 of 90 (the audited subset)
- The "TeamBench-100" name now refers to the LB100 parent and lives only in the Appendix
  derivation note. All §3 prose, Table 3, and Figure 4 use TeamBench-90 numbers.

Four experiments documented below:
1. **TeamBench-100 leaderboard** — 100 tasks × 5 conditions × 20 models, seed 0
2. **Cross-provider role mixing** — 27 configs × 25 tasks × 3 seeds, 3 commercial families
3. **Pre-registered role-enforcement ablation** — 3 conditions × 25 tasks × 2 seeds × 3 families
4. **Human evaluation study (in progress)** — 3 modes (solo / hybrid / team) on a stratified 20-task subset

Plus **task-quality artifacts** documented in `## TASK QUALITY VALIDATION (v2)`
below: canonical-solution check (SWE-Bench gold-patch analog), mutation-killing
grader (G2v2), per-task model discrimination, LLM-as-rater inter-rater
agreement (Fleiss κ=0.74 over 285 sampled judgments), and the
**TeamBench-Verified** subset built from those signals (SWE-Bench-Verified analog).

---

## TASK DISTRIBUTION (full pool + LB100 subset)

Authoritative sources:
- Full pool: `shared/teambench_dataset.json` (931 tasks, source for Figure 2 donut)
- LB100 selection: `leaderboard/data/leaderboard_100_tasks.json` (version 2.0,
  selection_date 2026-04-10, 100 tasks)

### Full pool (931 tasks, 19 dataset categories)

```
category                       easy  medium    hard  expert  total
Other                             2     640      91       0    733   ← scraped GitHub-issue pool (donut: "GitHub issues")
Security                          0       4      24       4     32
Software Eng.                     1       2      26       2     31
Incident Response                 0       1      24       1     26
Operations                        1       3      10       3     17
Data Engineering                  1       4       9       1     15
Testing                           1       3       8       0     12
Policy                            1       3       4       1      9
Information Retrieval             1       3       4       0      8
Distributed Systems               0       0       4       3      7
Adversarial                       0       0       7       0      7
Code Review                       1       2       3       0      6
Multi-language                    0       0       6       0      6
Long-Horizon                      0       0       4       2      6
Pipeline                          0       3       3       0      6
Cross-System Integration          0       0       5       0      5
Specification                     0       2       1       0      3
Integration                       0       0       1       0      1
Negotiation                       0       0       1       0      1
                              ----------------------------------
total                             9     670     235      17    931
```

The Figure 2 donut uses Hamilton largest-remainder rounding so percentages
sum to 100; the underlying counts are above. The "Other" bucket (733 of 931
≈ 79%) is the broad GitHub-issues scrape and is rendered as the "GitHub
issues" wedge in Figure 2.

### TeamBench-100 stratified subset (100 tasks, 21 leaderboard buckets)

LB100 splits the dataset's "Other" into three leaderboard buckets:
**GitHub Issues (Real-World)**, **Real Data Science**, and **Other (Misc)**.
Quotas were chosen with Hamilton largest remainder against
`leaderboard/data/leaderboard_100_tasks.json::categories`.

```
LB100 category                  | quota | sel | pool | with_ablation | difficulty mix
Other (Misc)                    |   17  |  17 |  422 |       1       | hard:4, medium:13
GitHub Issues (Real-World)      |   12  |  12 |  221 |      12       | medium:12
Real Data Science               |    8  |   8 |   90 |       0       | hard:8
Software Eng.                   |    6  |   6 |   31 |       6       | expert:2, hard:4
Incident Response               |    6  |   6 |   26 |       6       | expert:1, hard:5
Security                        |    6  |   6 |   32 |       6       | expert:4, hard:2
Operations                      |    5  |   5 |   17 |       5       | expert:3, hard:2
Data Engineering                |    5  |   5 |   15 |       5       | expert:1, hard:4
Testing                         |    4  |   4 |   12 |       4       | hard:4
Adversarial                     |    3  |   3 |    7 |       3       | hard:3
Code Review                     |    3  |   3 |    6 |       3       | hard:2, medium:1
Cross-System Integration        |    3  |   3 |    5 |       3       | hard:3
Distributed Systems             |    3  |   3 |    7 |       3       | expert:3
Information Retrieval           |    3  |   3 |    8 |       3       | hard:3
Long-Horizon                    |    3  |   3 |    6 |       3       | expert:2, hard:1
Multi-language                  |    3  |   3 |    6 |       3       | hard:3
Pipeline                        |    3  |   3 |    6 |       3       | hard:3
Policy                          |    3  |   3 |    9 |       3       | hard:3
Specification                   |    2  |   2 |    3 |       2       | hard:1, medium:1
Integration                     |    1  |   1 |    1 |       0       | hard:1
Negotiation                     |    1  |   1 |    1 |       1       | hard:1
                                  ---------------------------------
total                           |  100  | 100 |  931 |      75
```

Difficulty distribution across LB100: **hard 57, medium 27, expert 16**
(no "easy" tasks were selected). 75 of 100 LB100 tasks have an
originally-authored ablation reference (the remaining 25 are the GitHub
Issues, Real Data Science, and most-of-Other buckets that ship as
single-agent benchmarks without the 5-condition reference run).

### Discrepancies vs current draft Table 1 (distribution table)

The draft's §2.2 currently says "19 base categories at the construction
level" and "21 refined buckets" — this matches the JSONs (19 in the full
pool, 21 in LB100). Table 1 in the paper should report the LB100 quotas
above, not the full-pool counts; figure 2 reports the full-pool donut. If
Table 1 currently mixes the two, fix it.

---

## TASK QUALITY VALIDATION (v2 — strengthened to SWE-Bench / Terminal-Bench level)

A four-pillar audit was added on 2026-04-30. Each pillar has an
authoritative JSON in `shared/paper/teambench_quality/` and a
script in `scripts/` that any reviewer can re-run.

| Pillar | Script | Output JSON | Analog in prior benchmarks |
|---|---|---|---|
| Canonical-solution check | `scripts/check_canonical_solution.py` | `canonical_pass_check.json` | SWE-Bench gold-patch verification |
| Mutation-killing grader (G2v2) | `scripts/mutation_test_grader.py` | `mutation_kill.json` | SWE-Bench unused-test guard |
| Cross-model discrimination | `scripts/compute_task_discrimination.py` | `task_discrimination.json` | Terminal-Bench dual-baseline gate |
| LLM-as-rater inter-rater | `scripts/llm_inter_rater.py` | `llm_inter_rater.json` (+ summary md) | Substitute for human inter-rater |
| **TeamBench-Verified subset** | `scripts/build_verified_subset.py` | `shared/paper/teambench_verified.json` | SWE-Bench Verified |

### Pillar 1: Canonical-solution check

For each LB100 task we attempt three evidence paths in order, strongest
first; the first that returns a passing grader sets the result.

```
canonical_in_workspace : seed-0 workspace passes the grader as-is
canonical_via_llm_run  : at least one historical agent run produced a workspace
                         that the grader accepted (harvested from
                         shared/ablation_results/lb100_*.{json,jsonl})
canonical_via_pr       : GH-sourced; upstream PR diff applied to seed-0 → grader passes
canonical_unknown      : none of the above (needs PR-fetch with valid token, or repair)
```

**Current LB100 result**: 58 of 100 verified via LLM-run evidence; 42 unknown.
The 42 unknowns split into 18 GH-* recent scrapes (need a fresh GitHub
token to fetch upstream PRs at scale; the stale token in `.env` returns
401) and 24 originally-authored tasks where no model has yet produced a
passing solution. The latter need either a stronger model run, a stored
canonical-fix patch, or removal from LB100.

### Pillar 2: Mutation-killing grader (G2v2)

Replaces the broken Gate 2 in `validate_task_quality.py` (which compared
the seed-0 workspace against an empty submission, a perturbation too weak
to test grader sensitivity for tasks where seed-0 is already the canonical
fix).  The new script applies AST-level mutations to a known-passing
workspace and checks whether the grader catches them. Mutations: swap
`==`/`!=`, swap `<`/`>`, swap `True`/`False`, swap `and`/`or`, replace
`return X` with `return None`, and a few more.  `mutation_kill_rate` =
fraction of mutants where the grader's score dropped meaningfully.

Initial samples (still running on full LB100):

```
TRAP1_spec_conflict     attempts=8 kill_rate=0.00   (grader insensitive — needs hardening)
TRAP5_security_theater  attempts=8 kill_rate=0.50   (acceptable)
TRAP6_deprecated_api    attempts=8 kill_rate=1.00   (excellent)
CR4_api_review          skipped — base workspace did not pass grader
CR6_review_checklist    skipped — no historical passing workspace available
```

The first surfaced gotcha already: TRAP1_spec_conflict has a 0% mutation
kill rate. That is a real reviewer-2 finding; the grader needs hardening
before TRAP1 can be in TeamBench-Verified.

### Pillar 3: Cross-model discrimination

For each LB100 task, harvested across all `lb100_*.json` model run files,
we compute per condition `spread = max_model_pass_rate − min_model_pass_rate`
and take the max across conditions as `discrimination_score`. Tasks with
discrimination < 0.10 are flagged: every leaderboard model gets the same
outcome, so the task carries no comparative signal.

Current LB100 distribution (from `task_discrimination.json::summary`):

```
discrimination < 0.05 : 42 tasks   (no separation; same as the canonical_unknown set)
discrimination < 0.10 : 42 tasks
discrimination ≥ 0.20 : 58 tasks
discrimination ≥ 0.40 : 58 tasks
```

The `discrimination_score` and per-condition spread were appended to
the existing 79 LB100 validation reports in `shared/validation_reports/`.

### Pillar 4: LLM-as-rater inter-rater agreement

Sampled 300 (task, condition, run) tuples from the LB100 ablation runs,
stratified by category and condition. Three independent OpenRouter judges
— `anthropic/claude-haiku-4.5`, `google/gemini-3-flash-preview`,
`openai/gpt-5.4-mini` — each received the spec, a workspace summary,
the verifier attestation, and the deterministic grader's verdict, and
returned PASS or FAIL with a one-sentence reason.

Final results (n_judgments=285 valid, n_invalid=15, total spend $34.20):

```
Pairwise Cohen κ:
  haiku45  vs g3flash    = 0.66    (substantial)
  haiku45  vs gpt54mini  = 0.91    (almost perfect)
  g3flash  vs gpt54mini  = 0.70    (substantial)

Three-way Fleiss κ                     = 0.74  (substantial)
Binary Krippendorff α                  = 0.74

Each judge vs deterministic grader:
  haiku45    agreement=0.99  κ=0.96  false-accept=0.8%   false-reject=2.4%
  g3flash    agreement=0.88  κ=0.65  false-accept=13.5%  false-reject=0.0%
  gpt54mini  agreement=0.96  κ=0.87  false-accept=3.3%   false-reject=4.9%
```

Interpretation under Landis & Koch (1977): three-way Fleiss κ in [0.61,
0.80] = "substantial agreement" between the three independent LLM judges,
and Cohen κ between Haiku/GPT-mini and the deterministic grader is
"almost perfect" (≥ 0.81). Gemini-3 Flash is the most lenient judge
(13.5% LLM-PASS when grader=FAIL — same false-accept pattern we see on
the Verifier role in the role-mixing study). The deterministic grader's
accept/reject calls are not idiosyncratic; LLM judges with
diverse training reach the same call on most runs.

### Pillar 5 (synthesis): TeamBench-Verified subset

Eligibility (per `scripts/build_verified_subset.py`):

```
Required:
  canonical_solution result is one of {canonical_in_workspace, canonical_via_llm_run, canonical_via_pr}
  mutation_kill_rate ≥ 0.50  (or "no mutation result" yet — counts as pass while pillar 2 is in progress)
  discrimination_score ≥ 0.10
Informational only (NOT a hard filter):
  G1 structural status — flagged in the per-task ledger but not used to disqualify,
  because for tasks where the seed-0 workspace is intentionally buggy, G1 reports
  "grader crashed on generated workspace" with the workspace's expected-buggy
  failure modes; that is correct grader behavior, not a task defect.
```

**Final outcome (after GITHUB_TOKEN refresh, mutation-test full run, file-filter
fix, and O6 grader-output exemption)**:
**57 of 100 LB100 tasks** qualify for TeamBench-Verified under default
thresholds (mutation_kill_rate ≥ 0.50, discrimination_score ≥ 0.10,
canonical-solution evidence required, with one exemption: O6_perf_tuning's
grader scores config.json output via simulator.py rather than running the
workspace's source code, so mutation testing of source files is by-design
irrelevant; this is documented in `MUTATION_EXEMPT` in
`scripts/build_verified_subset.py`).

**On TeamBench-90 (with the 10 broken-grader-post-pr tasks dropped):**
**57 of 90 = 63.3%** qualify for TeamBench-Verified.

The TeamBench-90 task list is at
`leaderboard/data/leaderboard_90_tasks.json` (version 2.1, derived from
LB100 with documented `dropped_task_ids` and `dropped_reason`).

```
Drop reasons (sorted):
  39 × canonical=unknown + missing mutation + missing discrim
   3 × G1 structural fail + canonical=unknown + missing mutation + missing discrim
   1 × mutation_kill_rate = 0.00  (TRAP1_spec_conflict — grader insensitive)
   1 × G1 structural fail + mutation_kill_rate = 0.00  (O6_perf_tuning)
```

### Triage of the 44 LB100 tasks NOT in TeamBench-Verified

The 44 non-Verified tasks are not all "broken" — most are solvable but
fail one of the strict gates. From `scripts/triage_unknowns.py` →
`shared/paper/teambench_quality/unknown_triage.json`:

| Bucket | Count | Meaning | Recommended action |
|---|---|---|---|
| **near_miss_very_close** | 11 | Best historical partial ≥ 0.9 across 150+ runs; the grader has 1-2 over-strict checks that nobody passes | Relax those checks; would lift Verified to ~67 |
| **near_miss** | 11 | Best historical partial 0.7-0.9; solvable but harder | Run stronger oracle (Opus 4.7) and/or relax checks |
| **solvable_in_principle** | 10 | Best historical partial 0.4-0.7; partial credit but not converging | Keep in LB100; report partial scores |
| **broken_grader_post_pr** | 10 | Static workspace IS the post-PR canonical fix, but grader requires compiled numpy/scipy/etc not vendored in workspace; the GH1000-1011 + GH144_psycopg series | **Remove from LB100** or rewrite grader to skip compiled-deps |
| **needs_review** | 2 | TRAP1_spec_conflict (mutation_kill=0) and O6_perf_tuning (mutation_kill=0) — graders are insensitive to local code mutations | Harden grader; add adversarial test cases |

### Concrete recommendation for camera-ready

Drop the 10 `broken_grader_post_pr` tasks from LB100 entirely. They are
GH-1000+ recent scrapes whose graders cannot pass on the canonical fix
because the workspace has Python source files but not compiled numpy/scipy
extensions. They artificially deflate the leaderboard pass rates and
cannot contribute to TeamBench-Verified. The 90-task "LB100 v2" they
leave behind would have:

- 56 of 90 (62%) immediately Verified
- 11 near_miss_very_close that could move to Verified with grader relaxation
- Net: a defensible **TeamBench-90** with TeamBench-Verified at 56-67 of 90.

The 18 GH-* canonical_unknown tasks were re-checked WITH a fresh
GITHUB_TOKEN: PR diffs were fetched (cached at
`shared/paper/teambench_quality/pr_diffs/`) but `patch -p1` rejects them
because the generator applies seed-based identifier renaming
(`acf_x` → `acf_x_alt`, `along` → `along_alt`, etc.) that breaks the
diff hunk context. The static workspace IS at post-PR state but the
grader can't recognize a passing solution there either.

### Mutation testing — final results across LB100 (n=100)

```
9 of 100 tasks have a passing workspace available to mutate
(others skipped because no historical agent run produced a passing workspace)

Of those 9 (after script bug fix and O6 exemption):
  4 have kill_rate ≥ 0.7  (excellent: grader catches most mutations)
  7 have kill_rate ≥ 0.5  (acceptable; threshold for TeamBench-Verified)
  1 has kill_rate ∈ [0.4, 0.5) (TRAP1_spec_conflict at 0.42 — grader does detect
                                 some mutations but flag-flip mutations on
                                 unreachable code paths slip through)
  1 has kill_rate = 0.083  (O6_perf_tuning — grader scores config.json output
                            not source; exempt from mutation criterion)
```

**Two findings, both fixed in this session:**

1. **Mutation-script file-filter bug** (now fixed in
   `scripts/mutation_test_grader.py`): the original mutator walked all
   `.py` files including third-party packages installed at the workspace
   root (when agents ran `pip install --target=.` instead of using a
   venv). This caused TRAP1 to report kill_rate=0.0 when the mutations
   were actually being applied to `_pytest/_argcomplete.py`, not to the
   TRAP1 source. The fix scans for `*.dist-info` siblings and a hardcoded
   `KNOWN_INSTALLED_PACKAGES` set, then prunes them from the walk. After
   the fix, TRAP1 mutates only `app/{__init__,config,routes,validators}.py`
   and reports kill_rate=0.42 — below the 0.5 threshold but real grader
   signal.

2. **O6_perf_tuning grader-output exemption**: the O6 grader scores
   `config.json` (the agent's deliverable) via `simulator.py::compute_metrics`,
   not by running the workspace's `optimizer.py`. Mutating workspace
   Python files cannot affect the verdict by design. Exempted in
   `scripts/build_verified_subset.py::MUTATION_EXEMPT`. Future tasks
   with the same shape (grader scores deliverable artifact) should be
   added to that set.

### What we still do NOT have

- **Human inter-rater agreement on the deterministic graders.** Mitigation: the LLM-rater Fleiss κ=0.74 demonstrates the grader's verdicts are not idiosyncratic. The human-IRR pipeline is now ready: 285-row CSV at `shared/paper/teambench_quality/human_irr/human_irr_form.csv`, instructions at `INSTRUCTIONS.md`, protocol at `protocol.md`, scoring script at `scripts/score_human_irr.py`. Same 285 tuples used by the LLM rater so direct human-vs-LLM comparison is possible after raters fill the form.
- **Expert review of difficulty labels.** Author-assigned. Defer to community / camera-ready.
- **External annotator review of every task.** Defer; document as limitation.
- **Reference-solution patch stored per originally-authored task.** Closing this would let canonical-check finish without depending on prior LLM runs.

### Action items still open after this week's run

1. Refresh GITHUB_TOKEN in `.env`, then run
   `python scripts/check_canonical_solution.py --lb100` (no `--skip-pr-fetch`)
   to verify the 18 GH-* canonical_unknown tasks via upstream PR diff.
2. Wait for the mutation-test full run to complete (currently in progress);
   re-run `build_verified_subset.py` after to get the final Verified count.
3. Triage the 24 originally-authored canonical_unknown LB100 tasks by hand
   or with a stronger model (Opus 4.7 / GPT-5.4 oracle pass).
4. (Stretch) write per-task canonical-fix patches for the originally-authored
   tasks, store under `tasks/<id>/canonical/solution.diff`.

---

## TASK QUALITY VALIDATION (v1 — original 4-gate validate_task_quality.py)

The v1 pipeline (still useful as a structural lint) is described below.

### Pipeline that exists

`scripts/validate_task_quality.py` runs 4 gates per task:

| Gate | Question | Failure trigger |
|---|---|---|
| G1 structural | Does the generator emit valid files for seeds 0/1/2? Does `grade.sh` parse and run without crashing? | Missing generator, syntax error, grader crashes |
| G2 grader discrimination | Does the buggy seed-0 workspace score < 1.0? Does an empty submission score ≤ 0.1? | Buggy ≥ 1.0 (grader doesn't catch the deliberate bug) or empty > 0.1 (grader is too lenient / scoring constant) |
| G3 information asymmetry | Is `1 − overlap(spec, brief) ≥ 0.3`? | Brief duplicates the spec; relay isn't structural |
| G4 contamination | Is the per-task seed diversity ≥ 0.2? | Seeds produce near-identical workspaces; held-out seeds wouldn't resist memorization |

Per-task reports: `shared/validation_reports/<task_id>.json` (998 reports).
Aggregate: `shared/validation_full.json` (counts by recommendation).

### What the data says (full pool, 998 reports)

```
recommendation | ACCEPT 153 (15%) | REVISE 845 (85%) | REJECT 0
gates passed   | 4: 153  |  3: 351  |  2: 494
G1 structural  | fail 29   warn   0
G2 grader-disc | fail 551  warn 546   (550 tasks have buggy_score >= 1.0; only 5 tasks have grader_discriminates=True)
G3 asymmetry   | fail   0  warn   0   (977/998 strong >=0.7, 21 ok 0.5-0.7)
G4 contamination| fail 759  warn  96   (815 tasks have seed_diversity <0.2)
```

### What the data says (LB100 subset, 79 of 100 reports — the curation pays off)

```
recommendation | ACCEPT 54 (68%) | REVISE 25 (32%)
gates passed   | 4: 54  | 3: 23  | 2: 2
G1 structural  | fail 9 (11% — concerning)
G2 grader-disc | fail 1 (1.3%)   buggy_score = 0 for ALL 79 — graders DO discriminate on LB100
G4 contamination| fail 17 + warn 10 (34%)   seed-diversity 25 strong / 20 ok / 26 weak
```

The 21 LB100 tasks **without any validation report** are the recently-scraped
GitHub issues (`GH1000_numpy_19869`, `GH1003_scipy_*`, `GH1004_dask_*`, …)
that bypassed the validation pipeline. These should be either removed from
LB100 or pushed through `validate_task_quality.py` before camera-ready.

### What we DO NOT have (be ready for these reviewer questions)

| Standard quality check | In repo? | Mitigation if asked |
|---|---|---|
| Canonical / expert-fix passes the grader (SWE-Bench style) | **No** | The 5-condition reference ablation on 153 templates indirectly probes this: tasks where Solo+Restricted+Team all score 0 are likely broken, tasks where all score 1 are trivially solvable. Both extremes are flaggable from `shared/paper/lb100_full_aggregate.json`. |
| Human inter-rater agreement on grading rubrics | **No** | Graders are deterministic shell scripts, not LLM-judges, so inter-rater is N/A in the conventional sense. State this explicitly. |
| Expert review of difficulty labels | **No** | Difficulty is set per-template by the author. No external annotation. State as a limitation. |
| Public / independent annotator review | **No** | Open release of generators + graders is the standby; community can audit post-publication. State as a limitation. |
| Held-out test pool with human labels | **No** | Held-out **seeds** exist (5/6/7) for contamination resistance, but no held-out human-labeled set. |
| Reference-solution executes the test suite | **No** | Only buggy/empty are tested by G2. The seed-0 workspace already contains the reference solution for many tasks, which is why so many G2 tests return buggy_score=1.0 (the perturbation is too weak). |

### What partially defends task quality (concrete)

- **Cross-model discrimination on LB100**: Full-condition pass rate spans
  Gemma 4 31B 35.7% down to Qwen 3 8B 0.0% (`lb100_full_aggregate.json`).
  Tasks discriminate models, which is the basic empirical sanity check.
- **G3 information asymmetry passes for 977/998**: the central
  Planner→Executor relay is genuinely structural across the pool.
- **5-condition reference ablation on 153 templates** provides indirect
  calibration: tasks where every condition scores 0 or every condition
  scores 1 are flaggable.
- **650+ real GitHub bug reports** come from active OSS repos with
  maintainer-confirmed bugs; the bug and the upstream fix both exist in
  the source-of-truth repo.

### The single biggest concern (and what it really means)

**Only 5 of 998 tasks have G2 `grader_discriminates=True`.** Reading the
gate (`scripts/validate_task_quality.py:395-486`), G2 compares the seed-0
workspace (treated as "buggy") against an empty submission. For 550 of
998 tasks, the seed-0 workspace itself scores ≥ 1.0 — meaning the seed-0
workspace already contains a correct reference solution and the
"perturbation" isn't a real bug. **This is a gate-design weakness more
than a task-design weakness**: the gate would need a stronger perturbation
(delete a function body, return wrong type, swap a comparison operator)
to be a real adversarial test of the grader. LB100 doesn't have this
problem because the curated tasks include actually-broken seed-0
workspaces; the issue is concentrated in the 731 broad GitHub-scrape and
Real-Data-Science tasks where the seed-0 workspace IS the canonical
solution rather than a buggy starting point.

### Action items before submission

1. Run `validate_task_quality.py` on the 21 LB100 GH-scrape tasks that
   have no report yet.
2. Investigate the 9 LB100 tasks that fail G1 structural — these are
   real bugs in the task definitions, not gate-design artifacts.
3. Consider strengthening G2 (e.g., apply a code-mutation pass to the
   seed-0 workspace before scoring) so the gate produces a meaningful
   discrimination signal across the full pool, not just LB100.
4. Document the absence of a canonical-solution-passes-grader check
   honestly in the paper appendix.
5. State seed-diversity as a known limitation: the held-out-seed
   contamination resistance argument applies to the 9-task strict subset
   (Jaccard < 0.5) more cleanly than to the full pool.

---

## EXPERIMENT 1 — TeamBench-100 Leaderboard (5 conditions × 14+ models)

100 stratified tasks, 5 ablation conditions per model, seed 0, target ~7,000
runs. Reported in §3.2 (per-role marginal) and §3.4 (leaderboard) of the
paper, with Table 3 and Figure 4.

### Authoritative aggregates

| Path | What it is | Use for |
|---|---|---|
| `shared/paper/lb100_full_aggregate.json` | 20-row full table with per-cell `passed`/`valid_n`/`rate`/`source` for every model × condition | Table 3, all per-model claims |
| `shared/paper/lb100_partial_aggregate.json` | Same shape but partial-score (mean of [0,1]) instead of binary pass | Appendix H mean-partial-score row |
| `shared/paper/lb100_figure_data.json` | 19-row Solo + Full only; used by `paper/scripts/main_results_v2.py` | Figure 4 leaderboard bars |
| `shared/paper/lb100_table_recomputed.json` | Older 14-model snapshot from 2026-04-27 | **superseded** by `_full_aggregate` |
| `shared/paper/lb100_snapshot.json` | Per-source-file rollup with `n_files` and `rows` | Cross-checking which checkpoints fed each cell |

### Per-model raw sources (in `shared/ablation_results/`)

| Model JSON family | Notes |
|---|---|
| `lb100_haiku45_oraclefull_seed0.json` + `lb100_haiku45_3cond_seed0.json` + `lb100_haiku45_full_resume.json` | Claude Haiku 4.5; 3 files combined |
| `lb100_sonnet46_oraclefull_seed0.json` + `lb100_sonnet46_3cond_seed0.json` | Claude Sonnet 4.6 |
| `lb100_opus47_seed0.json` + `lb100_opus47_seed0.json.checkpoint.jsonl` | Claude Opus 4.7 — Full lives in the **checkpoint** because of the OpenRouter quota incident |
| `lb100_gpt54_oraclefull_seed0.json` + `lb100_gpt54_3cond_seed0.json` | GPT-5.4 |
| `lb100_gpt5mini_5cond_seed0.json` + `lb100_gpt-5.4-mini_oraclefull_seed0.json.checkpoint.jsonl` | GPT-5.4 Mini (full coverage) |
| `lb100_gpt5nano_oraclefull_seed0.json` + `lb100_gpt5nano_3cond_seed0.json` + `lb100_gpt-5.4-nano_oraclefull_seed0.json.checkpoint.jsonl` | GPT-5 Nano + GPT-5.4 Nano |
| `lb100_gemini3flash_oraclefull_seed0.json` + `lb100_g3flash_3cond_seed0.json` | Gemini-3 Flash |
| `lb100_gemini31lite_oraclefull_seed0.json` + `lb100_g31lite_3cond_seed0.json` | Gemini-3.1 Flash Lite |
| `lb100_gemini-3.1-pro-preview_seed0.json` | Gemini-3.1 Pro |
| `lb100_gemini25pro_oraclefull_seed0.json.checkpoint.jsonl` | Gemini-2.5 Pro (oracle only) |
| `lb100_gemma4-31b_seed0.json` | Gemma 4 31B (the OSS leader) |
| `lb100_qwen3-{8b,14b,32b}-or_seed0.json` + checkpoints | Qwen 3 family via OpenRouter |
| `lb100_qwen3-30b-a3b-or_seed0.json.checkpoint.jsonl` | Qwen 3 30B-A3B (oracle only) |
| `lb100_qwen3-4b_seed0.json.checkpoint.jsonl` | Qwen 3 4B |
| `lb100_qwen35-0.8b_seed0.json.checkpoint.jsonl` | Qwen 3.5 0.8B |
| `lb100_gpt-oss-{20b,120b}_seed0.json.checkpoint.jsonl` | GPT-OSS family |

Loader for figure: `_load_runs()` in `paper/scripts/main_results_v2.py`,
which prefers `.json` and falls back to `.checkpoint.jsonl` only for the
`CHECKPOINT_ONLY_FILES` whitelist (Opus 4.7 is the special case where the
checkpoint **overrides** the .json post-quota).

### Serving infrastructure (vLLM local vs OpenRouter)

Open-weight models were served two ways depending on the model size and
which path was working at the time. Filename suffix `-or` means the run
was dispatched against OpenRouter; no `-or` suffix means local vLLM on a
shared GPU node (vLLM 0.19.0 unless noted otherwise). Both
serving paths use the same agent harness, the same per-role step budgets,
and the same graders; only the model server differs.

Per-OSS-model serving used in the current `lb100_full_aggregate.json`:

| Model | Serving used in aggregate | Notes |
|---|---|---|
| gemma-4-31b | **vLLM local** (`lb100_gemma4-31b_seed0.json`) | Strongest OSS leader; vLLM with `--enable-auto-tool-choice` (the missing-flag bug bit `gemma4_e4b` previously) |
| qwen3-14b | **OpenRouter** (`lb100_qwen3-14b-or_seed0.json`) | The non-`-or` vLLM checkpoint exists but is archived (`*.archived_pre_openrouter_20260422_200227`) |
| qwen3-32b | **OpenRouter** (`lb100_qwen3-32b-or_seed0.json.checkpoint.jsonl`) | Same as 14B — vLLM run was archived in favor of OpenRouter |
| qwen3-8b | **mostly OpenRouter**, **Restricted is mixed**: aggregate combines `lb100_qwen3-8b-or_seed0.json` for 4 conditions + the vLLM `lb100_qwen3-8b_seed0.json.checkpoint.jsonl` for the Restricted cell (source label literally reads `or + vllm-checkpoint`) | The vLLM file pre-dates the Restricted path-bug fix on 2026-04-19 |
| qwen3-4b | **vLLM local** (`lb100_qwen3-4b_seed0.json.checkpoint.jsonl`) | Restricted cell missing per the bug noted above |
| qwen3-30b-a3b | **OpenRouter** (`lb100_qwen3-30b-a3b-or_seed0.json.checkpoint.jsonl`) | Solo only; the only condition that reached usable n |
| qwen3.5-0.8b | **vLLM local** (`lb100_qwen35-0.8b_seed0.json.checkpoint.jsonl`) | Tool-use floor failure — see TBA legend |
| gpt-oss-20b | **vLLM local** (`lb100_gpt-oss-20b_seed0.json.checkpoint.jsonl`) | Both 20B and 120B were also attempted via OpenRouter (`-or` logs `gpt-oss-{20b,120b}-or_lb100_20260428_032057.log`) but the aggregate uses the local vLLM checkpoint |
| gpt-oss-120b | **vLLM local** (`lb100_gpt-oss-120b_seed0.json.checkpoint.jsonl`) | Same as gpt-oss-20b: OpenRouter logs exist but aggregate uses vLLM |

Closed-source models (Claude / GPT / Gemini) all use first-party APIs
except **Claude Opus 4.7 Full** which is routed through OpenRouter after
the quota incident on the first-party API.

vLLM serving logs live under `logs/vllm_*.log` (e.g. `vllmgemma3-27b-it_*.log`,
`vllmqwen3-32b_abl.log`, `vllmgpt_oss_20b.log`); OpenRouter dispatch logs live
under `logs/*-or_lb100_*.log` (e.g. `qwen3-8b-or_lb100_FWD_20260428_185418.log`,
`gpt-oss-20b-or_lb100_20260428_032057.log`). When re-deriving any cell,
check both kinds of log to confirm which serving path produced the
consolidated file the aggregate is reading.

Two known parser-flag gotchas that produce silently invalid runs (memory
already records these): `gemma4_e4b` requires `--enable-auto-tool-choice`
on vLLM, and the `Qwen 3.5` family requires the `qwen3_xml` parser, not
`hermes`. Files affected by those bugs are archived with names ending in
`*.invalid_parser_20260419_222020` or `*.invalid_no_tool_choice_20260424_024259`
and **must not** be loaded into the aggregate.

### Current LB100 numbers (from `lb100_full_aggregate.json`, sorted by Full %)

```
model                    | oracle (Solo)  | restricted     | no_plan        | no_verify      | full
gemma-4-31b              | 15/73 = 20.5%  | 23/73 = 31.5%  | 21/62 = 33.9%  | 18/80 = 22.5%  | 20/56 = 35.7%
gpt-5-4-mini             | 17/100 = 17.0% | 21/100 = 21.0% | 22/100 = 22.0% | 22/100 = 22.0% | 27/100 = 27.0%
gemini-3-1-pro-preview   | 13/99 = 13.1%  | 18/99 = 18.2%  | 15/87 = 17.2%  | 23/98 = 23.5%  | 25/97 = 25.8%
gpt-5-4                  | 11/100 = 11.0% | 31/99 = 31.3%  | 20/99 = 20.2%  | 31/100 = 31.0% | 25/100 = 25.0%
claude-haiku-4-5         | 11/100 = 11.0% | 26/100 = 26.0% | 15/100 = 15.0% | 1/19 = 5.3%    | 23/100 = 23.0%
gemini-3-flash-preview   | 11/100 = 11.0% | 14/100 = 14.0% | 8/100 = 8.0%   | 25/100 = 25.0% | 22/100 = 22.0%
gpt-5-4-nano             | 4/100 = 4.0%   | 16/99 = 16.2%  | 9/96 = 9.4%    | 17/99 = 17.2%  | 6/33 = 18.2%
claude-opus-4-7          | 18/100 = 18.0% | 21/100 = 21.0% | 28/100 = 28.0% | 30/100 = 30.0% | 11/64 = 17.2%
claude-sonnet-4-6        | 7/100 = 7.0%   | 25/100 = 25.0% | 7/53 = 13.2%   | 6/39 = 15.4%   | 15/95 = 15.8%
gemini-3-1-flash-lite    | 4/99 = 4.0%    | 13/100 = 13.0% | 9/100 = 9.0%   | 16/99 = 16.2%  | 14/98 = 14.3%
qwen3-14b                | 3/100 = 3.0%   | 2/100 = 2.0%   | 2/100 = 2.0%   | 1/100 = 1.0%   | 2/100 = 2.0%
gpt-oss-20b              | 6/100 = 6.0%   | 11/100 = 11.0% | 8/100 = 8.0%   | 7/100 = 7.0%   | 1/70 = 1.4%
qwen3-32b                | 0/100 = 0.0%   | 3/100 = 3.0%   | 1/100 = 1.0%   | 5/100 = 5.0%   | 1/97 = 1.0%
gpt-oss-120b             | 2/100 = 2.0%   | 0/100 = 0.0%   | 1/70 = 1.4%    | 9/100 = 9.0%   | 0/10 = 0.0%
qwen3-4b                 | 1/97 = 1.0%    | 3/97 = 3.0%    | 1/98 = 1.0%    | 0/98 = 0.0%    | 0/14 = 0.0%
qwen3-8b                 | 1/100 = 1.0%   | 4/100 = 4.0%   | 1/100 = 1.0%   | 3/100 = 3.0%   | 0/99 = 0.0%
```

### What "TBA" actually means (cell-by-cell, since both 4b and 0.8b were flagged)

| Row | TBA cells | Meaning |
|---|---|---|
| **qwen3-4b** | Restricted only | Never attempted because the ablation runner had a path bug for the Restricted condition that pre-dated `pre_restricted_path_bug_fix_20260419` (see archived checkpoint `lb100_qwen3-4b_seed0.json.checkpoint.jsonl.pre_restricted_path_bug_fix_20260419_222236`). All other 4 conditions completed at n≈97-100 (Full at n=14 because the model crashes mid-run on most tasks). Restricted should be re-run before camera-ready or noted as a known gap. |
| **qwen3.5-0.8b** | No Plan / No Eval / Full + the n=24 Restricted | The 0.8B model fails to complete tasks at all. Oracle (n=94) returned 0 passes; Restricted only got n=24 of 100 because the model spins past its 30-turn budget without producing a `done` signal (eval log: `[restricted] Turn 29: 0 tool calls, done=False`). The remaining three conditions were not attempted because the smaller-coverage ones already returned 0/0 successful completions. Treat this row as evidence of a tool-use floor rather than missing data. The Restricted-only-attempted-after-bug-fix file is `lb100_qwen35-0.8b_seed0.json.checkpoint.jsonl` (post-bug-fix); the older `.invalid_parser_20260419_222020` files are abandoned. |
| **gpt-5-nano** | Restricted / No Plan / No Eval | Three middle conditions never attempted; only Solo (5/100) and Full (6/99) ran. Reportable as Solo + Full only. |
| **qwen3-30b-a3b** | All except Solo | Only Solo completed (2/53 from a checkpoint that did not finish). Treat as Solo-only data. |
| **gemini-2-5-pro** | All except Solo | Only Solo completed (0/100). Treat as Solo-only data, useful for comparing the previous-generation Gemini Pro to Gemini 3.x. |

The remaining "TBA" cells in the table (Claude Haiku 4.5 No Eval, Claude
Opus 4.7 Full, Claude Sonnet 4.6 several cells) are documented in the
"Discrepancies" section below as cells that **have data** but n<30 or are
out of sync with the paper's hand-typed values.

Condition naming: paper uses **Solo / Restricted / No Plan / No Eval / Full**;
JSONs use **oracle / restricted / team_no_plan / team_no_verify / full**.
"oracle" in the JSON == "Solo" in the paper (the full-access single agent).

### Reporting convention as of 2026-05-04 (paper v6 onward): normalize-to-90

Tables 4 and 7 and Figure 3 of the paper now use a single denominator of
**n=90** for every model and condition. A run that did not complete (model-
side malformed tool call, missing attestation, infrastructure outage, vLLM
crash, or harness exception) counts as a task failure rather than being
excluded from the denominator. Cells with attempted runs `< 30` are still
reported as TBA because the rate is uninformative at that coverage; this
threshold matches the panel-eligibility threshold in `main_results_v2.py`.

The attempt-count column in the lb90 aggregate (`valid_n` field) is
preserved for transparency but is no longer the denominator of the headline
rate. The mean-partial table (Table 7) keeps its own denominator (attempts)
because it is a per-attempt metric; the binary-pass column has been removed
from Table 7 to avoid mixing two conventions. See
`paper/scripts/main_results_v2.py:_load_runs` for the substitution.

### Current LB90 numbers under normalize-to-90 (passes/90), regraded with attestation-promotion rule

The headline figure (Figure 3) and Table 12 use the **regraded** aggregate
written by `scripts/regrade_attestation_promote.py` to
`shared/paper/lb90_full_aggregate_regraded.json`. The rule promotes
pass=False to pass=True iff (a) every recorded `failure_mode` is an
attestation-related entry (`bad_attestation`, `attestation_missing`,
`no_attestation`, `attestation_invalid`) and (b) no other failure mode
appears. This isolates the attestation-format check from the structural
checks. Per-cell `passed_orig` and `promoted` counts are preserved in the
regraded JSON so the rule is reversible. Source files prefer the
checkpoint variant (`*.checkpoint.jsonl`) which retains the original
`failure_modes` arrays. The consolidated `.json` files were rebuilt by a
recovery pass that lost the per-check failure breakdown for many runs.

```
model                    | Solo  | Restr | NoPlan| NoVer | Full  | (a-counts: Solo/Restr/NoPlan/NoVer/Full)
claude-opus-4-7          | 35.6  | 24.4  | 31.1  | 33.3  | 13.3  | 100/100/100/100/72
gpt-5-4-mini             | 33.3  | 23.3  | 25.6  | 24.4  | 28.9  | 99/90/90/90/99
gemini-3-1-pro-preview   | 27.8  | 22.2  | 16.7  | 25.6  | 28.9  | 99/99/87/98/97
gpt-5-4                  | 12.2  | 30.0  | 14.4  | 34.4  | 27.8  | 100/99/99/100/100
gemma-4-31b              | 27.8  | 25.6  | 24.4  | 20.0  | 22.2  | 73/70/59/75/56
gemini-3-flash-preview   | 13.3  | 16.7  | 10.0  | 27.8  | 25.6  | 100/100/100/100/100
claude-haiku-4-5         | 12.2  | 28.9  | 12.2  |  1.1  | 25.6  | 100/100/100/17/100
gpt-oss-20b              | 17.8  | 17.8  | 12.2  |  7.8  |  2.2  | 100/100/100/100/84
gemini-3-1-flash-lite    |  5.6  | 21.1  |  8.9  | 17.8  | 17.8  | 99/100/100/99/98
claude-sonnet-4-6        |  7.8  | 21.1  |  7.8  |  6.7  | 17.8  | 100/100/44/38/95
qwen3-14b                |  5.6  |  2.2  |  2.2  |  1.1  |  2.2  | 100/100/100/100/100
qwen3-32b                |  5.6  |  3.3  |  0.0  |  5.6  |  1.1  | 100/100/100/100/93
qwen3-8b                 |  2.2  |  5.6  |  1.1  |  3.3  |  0.0  | 100/100/100/100/99
gpt-oss-120b             |  excluded — Full a=14 only (< 30 valid runs threshold); reported in Appendix E.3 excluded-models table
qwen3-4b                 |  excluded — Full a=14 only, Restricted not run
qwen3-30b-a3b            |  excluded — Solo only (a=53)
gemini-2-5-pro           |  excluded — Solo only (a=100)
qwen3.5-0.8b             |  excluded — Solo only, Restricted a=24
```

Sort key in Table 12 is `max(Solo, Full)` descending. Bold marks the
highest cell per row.

Top of leaderboard by max(Solo, Full):
Opus 4.7 35.6 (Solo) > GPT-5.4 Mini 33.3 (Solo) > Gemini-3.1 Pro 28.9 (Full)
= GPT-5.4-Mini 28.9 (Full) > GPT-5.4 27.8 (Full) = Gemma 4 31B 27.8 (Solo) >
Gemini-3 Flash 25.6 (Full) = Haiku 4.5 25.6 (Full) > gpt-oss-20b 17.8 (Solo)
= Sonnet 4.6 17.8 (Full) = Gemini-3.1 Flash Lite 17.8 (Full).

Within-family inversions (real, not data artifacts):
- GPT-5.4 Mini above GPT-5.4 on Solo (33.3 vs 12.2) and Full (28.9 vs 27.8).
- Haiku 4.5 above Sonnet 4.6 on Full (25.6 vs 17.8).
These persist across regrade thresholds (partial >= 0.95 / 0.90 / 0.85)
and reflect tool-use specialization rather than parameter count. See
§3.2 prose for the framing.

Excluded from Table 12 (per user request, 2026-05-04): gpt-oss-120b
(Full a=14 < 30 threshold). Listed in Appendix E.3 excluded-models table
and discussed alongside the other Solo-only attempts.

---

## EXPERIMENT 2 — Cross-Provider Role Mixing (27 configs × 25 tasks × 3 seeds)

3 commercial families (A=Claude Haiku 4.5, G=Gemini-3 Flash, O=GPT-5.4 Mini)
× 3 roles = 27 configurations, 25-task stratified subset, seeds 0 / 1 / 2.
Reported in §2.5 (design) and §3.3 (results), with Figure 3 and Table 4.

### Authoritative aggregates

| Path | What it is | Use for |
|---|---|---|
| `shared/role_ablation/results/per_config_3seed.json` | All 27 configs with `n` / `passes` / `rate` / `ci95_lo,hi` / `by_seed` / `seed_range_pp` / `model_config` | Table 4, all role-mixing claims |
| `shared/role_ablation/results/per_config.json` | Single-seed (seed 0) per-config aggregate | Seed-0 only comparison if needed |
| `shared/role_ablation/results/summary.json` | Top-config breakdown with cost / tokens / wall-clock | Cost discussion in §3.3 |
| `shared/role_ablation/results/per_run.jsonl` | Raw per-run records (config, model_config, task_id, seed, run_id, pass, partial_score, elapsed, role_usage, cost_usd_by_role, turns_total, failure_modes, error, timestamp) | Bootstrap / per-seed re-analyses |
| `shared/role_ablation/cost_tracking.json` | Total runs / cost / tokens by model | Compute-and-cost paragraph |
| `shared/role_ablation/tasks_25.json` | The 25-task stratified subset | Reproducibility / appendix |
| `shared/role_ablation/runs/<CONFIG>/...` | One subdirectory per config (PAEAVA, ..., POEOVO) holding per-task run outputs | Trace inspection |

### Current scale

- **27 / 27 configurations** completed at all 3 seeds (paper still says
  "twenty-two of the twenty-seven remain single-seed; the top five are
  three-seed pooled" — **this is now stale**).
- 75 runs per config (25 tasks × 3 seeds), 27 × 75 = **2,025 unique
  task-config-seed cells**; **2,145 total runs** including retries
  (`cost_tracking.json::total_runs`).
- Total spend: **\$326.04** (paper still reports \$200.27 — also stale).
- 675 task-config pairs, 195 flips → **flip rate 28.9%** (paper says 25%).
- Spearman seed-rank correlation: 0/1 = 0.28, 0/2 = 0.16, 1/2 = 0.09 — low
  agreement across seeds.

### Top configurations under 3-seed pooling

```
config    | model assignment                       |   pooled | Wilson CI95   | seeds 0,1,2
PGEAVA    | Gemini Plan / Haiku Exec / Haiku Verif |   26.7%  | [18.0, 37.6]  | 32, 24, 24
PAEAVA    | Haiku Plan  / Haiku Exec / Haiku Verif |   22.7%  | [14.7, 33.3]  | 32, 16, 20
PGEAVO    | Gemini Plan / Haiku Exec / GPT  Verif  |   22.7%  | [14.7, 33.3]  | 40, 12, 16
POEOVA    | GPT    Plan / GPT   Exec / Haiku Verif |   22.7%  | [14.7, 33.3]  | 28, 20, 20
PAEAVO    | Haiku Plan  / Haiku Exec / GPT  Verif  |   21.3%  | [13.6, 31.9]  | 32, 16, 16
POEGVG    | GPT    Plan / Gemini Exec/ Gemini Verif|   21.3%  | [13.6, 31.9]  | 28, 16, 20
...
PGEOVA    | Gemini Plan / GPT  Exec / Haiku Verif  |   10.7%  | [ 5.5, 19.7]  | 24,  0,  8  (worst)
```

**Important**: the seed-0 leader was PGEAVO at 36% (16/25 — wait, see
discrepancy below); under three-seed pooling PGEAVO drops to 22.7%, and
PGEAVA takes the lead at 26.7%. Per-config seed range goes up to 28pp
(PGEAVO: 40 → 12 → 16 across seeds 0/1/2).

### Recomputed role marginals (3-seed pooled, mean over 9 configs/cell)

```
slot       | A=Haiku 4.5 | G=Gemini-3 Flash | O=GPT-5.4 Mini | spread
-----------+-------------+------------------+----------------+--------
Planner    |    18.5%    |     16.4%        |    17.5%       |  2.1 pp
Executor   |    19.4%    |     16.6%        |    16.4%       |  3.0 pp
Verifier   |    17.3%    |     15.9%        |    19.3%       |  3.4 pp
```

### Discrepancies vs current draft Table 4 / §3.3 narrative (need to fix)

| Item | Paper (seed-0) | 3-seed pooled (correct) |
|---|---|---|
| Planner spread | 0.8 pp | **2.1 pp** |
| Executor spread | 5.1 pp | **3.0 pp** |
| Verifier spread | 4.5 pp | **3.4 pp** |
| Headline ordering | "Executor seat dominates" | **Verifier (3.4) > Executor (3.0) > Planner (2.1)** — Verifier slot now has the largest spread |
| PGEAVA pooled rate | 25.3% | **26.7%** |
| Worst config | not stated | **PGEOVA 10.7% [5.5, 19.7]** |
| Single-seed vs pooled coverage | "22 of 27 single-seed; top 5 pooled" | **all 27 are 3-seed pooled** |
| Total spend | \$200.27 | **\$326.04** |
| Total runs | 930 | **2,145** (2,025 unique cells) |
| Flip rate (config × task) | "25%" | **28.9%** |
| Seed rank correlation | not reported | Spearman 0/1=0.28, 0/2=0.16, 1/2=0.09 |

The "Executor dominates" claim in the abstract / intro / §3.3 / §4
Discussion does not survive 3-seed pooling. Verifier choice is now the
largest single-slot effect under pooling. The honest framing is: **Planner
choice has the smallest impact (≈2pp); Executor and Verifier choices each
shift the marginal by ≈3pp, and the sign and magnitude depend strongly on
which other two slots are held fixed (flip rate 28.9% across seeds).**

---

## EXPERIMENT 3 — Pre-registered Role-Enforcement Ablation (3 conditions × 25 tasks × 2 seeds × 3 families)

The methodological centerpiece of the paper: a pre-registered comparison of
**prompt-only**, **enforced** (separate sandboxes + separate histories,
identical to "Full Team" in the LB100 ablation), and **enforced shared
history** (separate workspace sandboxes but a shared message log). 25-task
stratified subset, 3 commercial families (Claude Haiku 4.5, Gemini-3 Flash,
GPT-5.4 Mini), 2 seeds. Reported in §3.7 of the paper, with Table 5.

### Authoritative paths

| Path | What it is | Use for |
|---|---|---|
| `experiments/role_enforcement_ablation/analysis/consolidated.json` | 400 per-run records, each with `model`, `condition`, `task_id`, `seed`, `run_id`, `pass`, `partial_score`, `violation_rate` | All §3.7 numbers and Table 5 pass / violation rows |
| `experiments/role_enforcement_ablation/analysis/statistics.json` | Pre-registered McNemar test outputs (T1 / T2 / T3) with raw and Holm-Bonferroni-adjusted p-values | Table 5 lower block |
| `experiments/role_enforcement_ablation/analysis/role_collapse_summary.json` | Per (model, condition, role) cell with `turns`, `violations`, `rate`, `ci95`, and `violation_types` count breakdown | §3.7 per-violation-type narrative + role-compliance rubric appendix |
| `experiments/role_enforcement_ablation/analysis/tables/table_main_effect.tex` | LaTeX table generated by the analysis script | Drop-in for Table 5 |
| `experiments/role_enforcement_ablation/runs/{model}/results_{condition}.json` | Per (model × condition) raw runs (mirrors what consolidated.json aggregates) | Trace-level inspection |
| `experiments/role_enforcement_ablation/HYPOTHESIS.md` | Pre-registration document committed before any data collection | Reproducibility / pre-registration claim |
| `experiments/role_enforcement_ablation/config/task_selection.json` | The 25-task subset definition | Reproducibility |
| `experiments/role_enforcement_ablation/scripts/{02..05}_*.py` | Task selection / dispatch / role-compliance scoring / statistical analysis | Re-run if more seeds added |

### Coverage matrix (n runs per condition × model)

```
condition                  | haiku45 | g3flash | gpt54mini | total
prompt_only                |    50   |    50   |     50    |  150
enforced                   |    50   |    50   |     48    |  148
enforced_shared_history    |    50   |     4   |     48    |  102
                                                    -------- | -----
                                                       total | 400
```

**Two known gaps**: GPT-5.4 Mini × enforced and × enforced-shared-history
each missing 2 runs (the 25 × 2 = 50 target dropped to 48 due to API
errors); and the Gemini-3 Flash × enforced-shared-history cell only has
n=4 because the OpenRouter quota was exhausted partway through (the same
quota incident that affected Claude Opus 4.7 in LB100). The Gemini ×
shared-history cell is the open task #20 in the project task list and is
the reason T3 in Table 5 reports n=100 pairs rather than n=150.

### Pass rates per condition (from statistics.json)

```
condition                  |    n  | mean pass | 95% CI
prompt_only                |  150  |   42.7%   | [34.7, 50.0]
enforced                   |  148  |   40.5%   | [32.4, 48.6]
enforced_shared_history    |  102  |   48.0%   | [38.2, 57.8]
```

### Per-run violation rates (from statistics.json)

```
condition                  |   n  | violation rate (mean) | 95% CI
prompt_only                | 150  |       6.40%           | [5.30, 7.60]
enforced                   | 148  |       6.23%           | [5.27, 7.33]
enforced_shared_history    |  98  |       8.92%           | [7.68, 10.27]
```

### Pre-registered McNemar tests (Holm-Bonferroni-adjusted, from statistics.json)

```
T1 compliance, prompt_only vs enforced            | 148 pairs | stat=4.32 | p_raw=0.038 | p_holm=0.113
T2 outcome,    prompt_only vs enforced            | 148 pairs | stat=0.56 | p_raw=0.453 | p_holm=0.907
T3 outcome,    enforced_shared_history vs enforced| 100 pairs | stat=0.08 | p_raw=0.773 | p_holm=0.907
```

None of the three reaches significance after Holm-Bonferroni. The strongest
signal is T1 (compliance under enforcement) at p_holm=0.113 — directionally
consistent with the per-violation-type breakdown below but not statistically
resolved at the aggregate level.

### Per-violation-type breakdown (from role_collapse_summary.json, summed across all model × role cells)

```
violation_type            | prompt_only | enforced | shared_history | prompt/enforced ratio
executor_plans            |     261     |   416    |      295       | 0.63x   (enforced INCREASES this — tighter scope shortens turns and trips the no-tool-no-code rule)
executor_self_approves    |       1     |     5    |        0       | 0.20x
planner_writes_code       |       2     |     0    |        0       | inf
verifier_modifies_code    |     256     |    72    |       85       | 3.56x   ← THE 3.6× FINDING
verifier_skips_tests      |     118     |   153    |      123       | 0.77x
```

**The headline 3.6× drop** comes from `verifier_modifies_code`: 256
prompt-only events drop to 72 enforced events (3.56× reduction). The paper
draft says "executor-plans events from 262 to 419" but the JSON says
261 to 416; close but slightly off. Use the JSON numbers.

The aggregate compliance test is null because executor_plans and
verifier_skips_tests both *increase* under enforcement (tighter Executor
scope shortens turns; the rubric flags any turn with no tool call and no
code edit), so the per-run rate barely moves while the underlying mix of
what is being violated changes substantially.

### Discrepancies vs current draft §3.7 / Table 5

| Item | Paper says | JSON says |
|---|---|---|
| Pass rates | 42.7 / 40.5 / 48.0 | matches ✓ |
| Per-run violation rates | 6.4 / 6.2 / 8.9 | 6.40 / 6.23 / 8.92 ✓ |
| T1 p_adj | 0.113 | matches ✓ |
| T2 p_adj | 0.907 | matches ✓ |
| T3 p_adj | 0.907 | matches ✓ |
| `verifier-modifies-code`: prompt → enforced | 256 → 71 (3.6×) | **256 → 72** (3.56×). Off by 1 in enforced count. |
| `executor-plans`: prompt → enforced | 262 → 419 | **261 → 416**. Off by 1 / 3 respectively. |
| Number of completed runs | 400 | 400 ✓ |
| Number of excluded runs | 50 (48 from Gemini × shared-history quota incident) | matches ✓ |

The 1-2-run discrepancies in Table 5's narrative paragraph are within
rounding of the actual JSON. Rewrite the paragraph from the JSON values to
remove the typos.

---

## EXPERIMENT 4 — Human Evaluation Study (in progress)

Live human-baseline study running on the TeamBench web platform; participants
are recruited researchers / students. Three modes mirror the §3 conditions:

- **solo** (Firebase mode `oracle`) — single human, full access; equivalent to the paper's "Solo"
- **hybrid** — single human paired with an LLM agent
- **team** — three humans assigned Planner / Executor / Verifier, OS-enforced separation (same isolation as the LB100 "Full" condition)

### Authoritative paths

| Path | What it is | Use for |
|---|---|---|
| Firebase RTDB tree `teambench_new` (project URL withheld for participant privacy; available to reviewers on request through the corresponding author) | Authoritative analysis tree, structured `tasks/{task_id}/{mode}/sessions/{session_id}` (rolled out 2026-04-25) | All current numbers below |
| Firebase RTDB tree `teambench/sessions` (legacy) | Pre-2026-04-25 sessions and stale-tab v2-bypass writes | Audit / reconciliation only — do **not** use for paper numbers |
| `human_eval/firebase/count_participants.py` | Filtering + counting script — drops dev/test identities, requires `phase=='completed'` and a submitted survey for the participant's role | Reproduce numbers below; pass `--source legacy` to compare against the legacy tree |
| `human_eval/selected_20_tasks.json` | Stratified 20-task target subset (seed 42, 2026-04-13), 18 of 21 categories represented | Defines the planned target coverage |

### Filters applied (count_participants.py defaults)

A row is counted only if **all** of the following hold:

1. Session `phase == 'completed'` (or `status == 'completed'`).
2. The participant has a `survey/{role}` entry under their session blob (v2 path).
3. Identity passes the dev-pollution filter: real-shaped email (`*@*.*`), name length ≥ 2, neither name nor email matches `test*` / `admin*` / `team_test_*` / `probe*` / single-char / 1-3-char-all-lowercase patterns.

Identity quirks worth noting before tightening the filter (participant identities anonymized in this public version):
- One participant used a placeholder-looking email but submitted genuine sessions — keep, do not drop.
- Two of the 13 unique emails belong to one participant who used both an institutional and a personal address, so de-duped count is 12 distinct humans.
- One team-mode survey was backfilled to Firebase from participant-dictated values on 2026-05-01 (the participant forgot to submit). Both Firebase paths carry `backfilled: true` and `backfillReason` so the analysis pipeline can isolate it.

### Current coverage (NEW tree, 2026-05-01)

```
mode    | unique humans | unique emails | total sessions | distinct task_ids
--------+---------------+---------------+----------------+------------------
solo    |       4*      |       5       |        8       |        7
hybrid  |       9       |       9       |       15       |       10
team    |       7       |       7       |        7       |        6
        |               |               |                |
TOTAL   |      12*      |      13       |       30       |       17**
```

\* Email-uniqueness lists solo as 5 because one participant used two addresses in CR2_style_enforce/solo (one session each); de-duped by person, solo is 4 humans and the total is 12.
\** 17 distinct task_ids across all three modes; 9 of those overlap with `selected_20_tasks.json`.

Total participant×session completions (counts each role-assignment in a team session separately): **42** = solo 8 + hybrid 15 + team 19. (Six of the seven team sessions have all 3 role-survey entries; one CR2 session has only 2 surviving role surveys.)

### Per-task × per-mode breakdown

```
task_id                  | mode    | participants | sessions | in 20-task target?
-------------------------+---------+--------------+----------+-------------------
CR2_style_enforce        | hybrid  |      3       |    3     | no
CR2_style_enforce        | solo    |      2       |    2     | no
CR2_style_enforce        | team    |      2       |    1     | no
CR4_api_review           | solo    |      1       |    1     | YES
CR4_api_review           | team    |      6       |    2     | YES
D6_data_reconcile        | solo    |      1       |    1     | YES
D8_csv_cleanup           | hybrid  |      4       |    4     | no
D8_csv_cleanup           | solo    |      1       |    1     | no
DIST1_queue_race         | hybrid  |      1       |    1     | YES
GH1002_scipy_24753       | hybrid  |      1       |    1     | YES
GH16_fiber_cors_logic    | hybrid  |      1       |    1     | no
GH16_fiber_cors_logic    | solo    |      1       |    1     | no
IR1_evidence_qa          | solo    |      1       |    1     | no
IR2_misinformation_trap  | team    |      3       |    1     | YES
O6_perf_tuning           | hybrid  |      1       |    1     | YES
O8_dockerfile_fix        | team    |      3       |    1     | no
P6_license_check         | hybrid  |      1       |    1     | no
PIPE2_data_pipeline      | team    |      3       |    1     | YES (one role survey backfilled)
RDS13_smote_leakage      | hybrid  |      1       |    1     | YES
S7_env_config            | hybrid  |      1       |    1     | no
TEST3_integration        | solo    |      1       |    1     | YES
TEST8_unit_basic         | hybrid  |      1       |    1     | no
TEST8_unit_basic         | team    |      3       |    1     | no
```

20-task-target coverage: **solo 3 / 20, hybrid 4 / 20, team 3 / 20** (CR4_api_review, IR2_misinformation_trap, PIPE2_data_pipeline).

### Per-participant breakdown (anonymized; 13 emails, 12 distinct humans)

Identities are withheld in this public release per participant privacy and IRB exempt-status conditions. The shape of the contribution distribution is reproduced below.

```
participant | task-mode completions | distinct tasks
------------+-----------------------+----------------
P01         |          9            |       8
P02         |          8            |       6
P03         |          7            |       4
P04         |          4            |       4
P05         |          2            |       2
P05*        |          2            |       2     (same person as P05, second address)
P06         |          2            |       2
P07         |          2            |       2
P08         |          2            |       2
P09         |          1            |       1
P10         |          1            |       1
P11         |          1            |       1
P12         |          1            |       1
```

Total task-mode completions: 42. Top 3 participants account for 24 of 42 (57%) — the data is heavily concentrated and any per-task-mode-cell pass-rate must be reported with this concentration in mind.

### Behavior metrics by mode (2026-05-01)

| metric | solo (n=8) | hybrid (n=15) | team (n=7) |
|---|---|---|---|
| verdict recorded | **0/8** (data bug) | 14/15 pass, 1/15 fail | 7/7 pass |
| median total duration (min) | 28.8 (0.9–121) | 2.65 (0.6–30) | 22.7 (11.4–28.8) |
| median total interactions per session | 159 (5–790) | 14 (3–49) | 355 (146–979) |
| median remediation cycles | 0 | 0 (max 1) | 1 (range 0–2) |
| median `overrode_grader` (1–5) | n/a | **3**, raw {1,1,1,1,1,2,3,3,3,3,3,3,3,5,5} | n/a |

Per-role interaction medians in team mode: **Planner 115** (n=7, range 61–212), **Executor 243** (n=6, range 165–689), **Verifier 80** (n=7, range 51–150). Activity ratio ~50:25:25 Executor:Planner:Verifier.

### Updated Likert means (descriptive only)

| mode | item | mean (n) |
|---|---|---|
| solo (counterfactual) | cf_verifier | 3.25 (8) |
| solo (counterfactual) | cf_executor | 3.12 (8) |
| solo (counterfactual) | cf_planner | 2.88 (8) |
| solo (counterfactual) | cf_domain | 2.75 (8) |
| solo (counterfactual) | cf_time_only | 2.50 (8) |
| hybrid AI teammate | ai_planner_useful | 3.73 (15) |
| hybrid AI teammate | ai_planner_trust | 3.67 (15) |
| hybrid AI teammate | ai_executor_quality | 3.53 (15) |
| hybrid AI teammate | ai_executor_trust | 3.67 (15) |
| hybrid AI teammate | verifier_role_value | 3.40 (15) |
| hybrid AI teammate | overrode_grader | **2.53 (15)** |
| team coordination | executor_efficiency | **3.95 (20)** |
| team coordination | early_plan | 3.90 (20) |
| team coordination | verifier_value | 3.85 (20) |
| team coordination | role_separation_helped | 3.50 (20) |
| team coordination | info_held_by_other | 3.35 (20) |
| team coordination | comms_overhead | 2.95 (20) |
| team role-need | stronger_executor | 3.55 (20) |
| team role-need | stronger_verifier | 3.40 (20) |
| team role-need | stronger_planner | 3.25 (20) |

### Team-mode primaryFactors (multi-select, max 3 selections per survey)

| factor | endorsements |
|---|---|
| missing_info_across_roles | **9 / 20** |
| time_pressure | **9 / 20** |
| weak_or_late_planning | 4 / 20 |
| other | 4 / 20 |
| implementation_difficulty | 3 / 20 |
| unclear_communication | 2 / 20 |
| missed_verification | 1 / 20 |

`missing_info_across_roles` tied with time_pressure as the top-cited team failure factor — the human-side analog of the architectural property the benchmark tests on agents.

### Per-task LLM-vs-human reference (overlap subset)

| task | LLM Solo | LLM Team | Human Solo | Human Hybrid | Human Team |
|---|---|---|---|---|---|
| CR4_api_review | 0/13 | 0/13 | TBD (1) | – | 2/2 |
| DIST1_queue_race | 3/13 | 0/13 | – | 1/1 | – |
| GH1002_scipy_24753 | 0/13 | 0/14 | – | 1/1 | – |
| IR2_misinformation_trap | 2/13 | 5/14 | – | – | 1/1 |
| O6_perf_tuning | 8/13 | 6/14 | – | 1/1 | – |
| PIPE2_data_pipeline | 0/13 | 0/14 | – | – | 1/1 |
| RDS13_smote_leakage | 0/13 | 1/13 | – | 1/1 | – |
| TEST3_integration | 1/13 | 0/13 | TBD (1) | – | – |
| **total overlap** | **14/104 (13.5%)** | **12/108 (11.1%)** | TBD (2) | 5/5 (override-confounded) | **4/4 (100%, N small)** |

Directional gap on the three Team-overlap tasks: LLM Teams 5/41 (12%), Human Teams 4/4 (100%). Cell-level N≤4 on the human side rules out any inferential claim — table is a per-task reference panel only.

### Reproduce

```
python3 human_eval/firebase/count_participants.py                        # default summary (NEW tree, completed + survey)
python3 human_eval/firebase/count_participants.py --details              # per-task per-mode roster
python3 human_eval/firebase/count_participants.py --csv > coverage.csv   # CSV with participant emails
python3 human_eval/firebase/count_participants.py --source legacy        # cross-check against legacy tree
python3 human_eval/firebase/count_participants.py --debug                # rejection-reason histogram
```

### Open gaps before any §3.X human-baseline claim

1. **Solo verdict-persistence bug**: 0/8 solo sessions have a recorded `verdict` in Firebase meta. Solo session-end path doesn't currently write through the same final-grade-write step as hybrid/team. Fix + re-grade from persisted `sharedArtifacts` before any solo pass-rate claim.
2. **Solo coverage**: 3 of 20 target tasks have any completed solo session. Need ≥17 more target tasks completed.
3. **Team coverage**: 3 of 20 target tasks (CR4, IR2, PIPE2). Team sessions need 3 humans simultaneously — recruitment bottleneck. Need ≥17 more target tasks.
4. **Hybrid override confound**: until the eligibility filter (`overrode_grader ≤ 2` AND wall-clock ≥ 5 minutes) is applied, hybrid pass rate is contaminated. Currently 5/15 sessions self-report override ≥ 3.
5. **Scope decision for §3.8**: report restricted to `selected_20_tasks.json` (current target, low n on each cell) or report on all 17 distinct collected task_ids (better n, weaker stratification claim). Currently §3.8 reports on the broader collection but maintains the 20-task minimum-cell rule for any per-task-rate claim.
6. **De-dup**: resolve the one participant who used two addresses before computing per-participant pass-rate or learning-curve statistics. Email-only dedup currently overcounts unique humans by 1 in solo and 1 in total.
7. **PIPE2 backfill**: one team-executor survey row for `PIPE2_data_pipeline_4uiwseht` was dictated post-session and written with `backfilled: true`. Exclude from any inter-rater-agreement analysis on the open-ended response field.

---

## Generators / scripts that touch these JSONs

| Script | Reads | Writes |
|---|---|---|
| `paper/scripts/main_results_v2.py` | `lb100_figure_data.json` + checkpoints | `paper/v4/imgs/leaderboard_v6.{pdf,png}` |
| `harness/paper_tables.py` | aggregates | `shared/paper/table_*.tex` (Tables 2, 3, 4) |
| `harness/compute_tni.py` | per-task ablation | TNI report |
| `experiments/role_enforcement_ablation/scripts/05_analyze.py` | enforcement runs | role-compliance Table 5 inputs |
| `harness/benchmark_stats.py` | `shared/teambench_dataset.json` | Table 1 distribution stats |

The role-mixing pipeline is in `harness/role_ablation_runner.py` and the
analysis is `scripts/analyze_role_ablation.py` (which produces
`shared/role_ablation/results/per_config*.json` + `summary.json` +
`figures/`).

---

## Things to verify whenever the draft changes

1. Re-derive Table 3 from `lb100_full_aggregate.json` (do not trust
   hand-typed numbers in the .tex). Decide per-row how to display
   permanently-incomplete cells (qwen3-4b Restricted; qwen3.5-0.8b last
   three; gpt-5-nano middle three; qwen3-30b-a3b and gemini-2-5-pro all
   except Solo).
2. Re-derive Table 4 from `per_config_3seed.json` (not from the seed-0
   `latex/table_role_ablation.tex`, which is now older).
3. Re-derive Table 5 (and the §3.7 narrative paragraph that references
   `verifier_modifies_code` 256 → 71/72 and `executor_plans` 262 → 419) from
   `experiments/role_enforcement_ablation/analysis/role_collapse_summary.json`
   and `statistics.json`.
4. Re-check abstract / intro / Discussion for any "Executor seat dominates"
   wording — under 3-seed pooling the Verifier has the largest spread.
5. Re-check role-mixing cost (\$326.04, not \$200.27) and run count (2,145,
   not 930) anywhere they appear in §3.1, §3.3, or appendices.
6. Re-check "twenty-two single-seed" wording in §6 / §4 Discussion — all 27
   are now three-seed pooled.
7. If the Gemini × shared-history cell is re-launched (open project task
   #20), re-run `experiments/role_enforcement_ablation/scripts/05_analyze.py`
   and re-derive Table 5 plus the per-violation-type counts from the
   updated `consolidated.json` and `role_collapse_summary.json`.
8. Re-pull the human-study coverage matrix from Firebase before any §3.X
   human-baseline claim — the live RTDB changes whenever a participant
   completes a session. Run `python3 human_eval/firebase/count_participants.py`
   (default flags) and update the Experiment 4 numbers above.
