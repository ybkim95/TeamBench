# TeamBench Task Admission Gate

Generated 2026-09-12T06:58:33.383822+00:00 from commit `ede45ad0` on branch `v2`.

Regenerate with: `python3 scripts/task_admission_gate.py --bootstrap`

Scope: 48 tasks at seed 0 (0 leaderboard tasks + 0 randomly sampled from the rest, `random.Random(0)`).

## Gate results

| Gate | Requirement | Pass | Fail | Unknown | Error |
|---|---|---:|---:|---:|---:|
| G1 | an empty submission scores 0 on the discriminative checks | 48 | 0 | 0 | 0 |
| G2 | pristine does not pass | 48 | 0 | 0 | 0 |
| G3 | reference solution scores 1.0 | 47 | 1 | 0 | 0 |
| G4 | grader is deterministic | 48 | 0 | 0 | 0 |
| G5 | grader is hermetic (static) | 48 | 0 | 0 | 0 |
| G6 | >=50% of checks are discriminative | 1 | 47 | 0 | 0 |
| G7 | grader terminates within 300 s | 48 | 0 | 0 | 0 |

## Admission

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Tasks evaluated | 48 | 0 | 0 |
| **Pass ALL seven gates** | **1** | **0** | **0** |
| Pass six gates, G3 unknown or pass | 1 | 0 | 0 |

`Pass ALL seven gates` is the honest size of the benchmark. The second row is the ceiling that becomes reachable once every task has a reference solution proving G3; it is not a substitute for it.

Why the second row is not a substitute, concretely: `GH120_redis-py_3863` is a 22-line stub grader that writes `partial_score: 0.0` for every submission. Its floor is 0.0, it never free-passes, it is perfectly deterministic, it touches no network, its single check is never free, and it finishes instantly. It satisfies six of the seven gates. Only G3 can reject it, because no reference solution can ever score 1.0 against a grader that returns 0.0 unconditionally. A task with no demonstrated solution has not been shown to be solvable, and G3 `unknown` must never be counted as a pass.

## G1: the pristine floor

Score awarded for staging the workspace and doing nothing at all.

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Tasks measured | 48 | n/a | n/a |
| Mean floor | 0.8146 | n/a | n/a |
| Median floor | 0.86 | n/a | n/a |
| Floor == 0.00 (clean) | 0 | n/a | n/a |
| Floor >= 0.50 | 47 | n/a | n/a |
| Floor == 1.00 | 0 | n/a | n/a |
| Max floor | 0.9 | n/a | n/a |

Across all evaluated tasks, 303 of 374 executed checks (81.0%) pass on the untouched workspace.

## Advisory: attestation credit

`submission/attestation.json` is a scored check in many graders. These rows re-grade the same untouched workspace after writing the harness's own passing-attestation stub (`harness.ablation._write_passing_attestation`), which is exactly what the `team_no_verify` condition writes automatically. This is score a do-nothing agent collects for filing a report.

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Mean floor, bare | 0.8146 | n/a | n/a |
| Mean floor, with attestation | 0.8146 | n/a | n/a |
| Tasks where attestation adds score | 0 | n/a | n/a |
| Mean credit | 0.0 | n/a | n/a |
| Max credit | 0.0 | n/a | n/a |
| Tasks reaching pass=true with attestation alone | 0 | n/a | n/a |

## G5: what the static hermeticity scan found

| Violation kind | Tasks |
|---|---:|
| (none) | 0 |

## Corpus-wide static scan (all graders, not just the sampled scope)

The two static checks cost only a file read, so they were run over every `tasks/*/grade.sh` in the repository.

| Measure | Tasks | of |
|---|---:|---:|
| Graders scanned | 821 | 821 |
| Pass G5 (no grade-time network, no venv-path reference) | 128 | 821 |
| Install packages or fetch over the network at grade time | 678 | 821 |
| Reference a gitignored or image-only venv path | 36 | 821 |
| Execute a script inside the agent-writable workspace | 5 | 821 |
| Write to a fixed (host-shared) `/tmp` path | 20 | 821 |

| Violation kind | Tasks |
|---|---:|
| pip_install | 675 |
| image_only_venv | 31 |
| gitignored_venv | 5 |
| npm_install | 4 |
| curl_wget | 1 |

## By task family

| Family | Tasks | Mean floor | Pass all 7 | Pass 6, G3 unknown |
|---|---:|---:|---:|---:|
| GH | 48 | 0.8146 | 1 | 1 |

## Artifact presence

| Artifact | Tasks with it | of |
|---|---:|---:|
| `grade_sh` | 48 | 48 |
| `task_yaml` | 48 | 48 |
| `spec_md` | 48 | 48 |
| `brief_md` | 48 | 48 |
| `reference_patch` | 48 | 48 |

A task with no on-disk `spec.md` hands the agent an empty specification: no harness caller writes a generator's in-memory spec to `task_dir` at run time.

## Advisory: graders that write to a fixed `/tmp` path

0 of 48 evaluated graders write intermediate results to a literal `/tmp/...` path rather than a per-process one. Two grades of such a task running anywhere on the same host at the same time overwrite each other's file and both report whatever the loser wrote, so the task's score depends on what else the machine is doing. This sweep serialises its own invocations of these graders; it cannot serialise other processes on the host, so these rows carry residual risk.

## Advisory: graders that execute a script inside the agent's workspace

0 of 48 evaluated graders run a relative script after `cd`-ing into the workspace the agent can write. The agent controls that file, so it controls its own score.

## Worst 25 pristine floors

| Task | Scope | Floor | Pristine pass | Free / total checks | Gates failed |
|---|---|---:|---|---|---|
| `GH30_werkzeug_3109` | explicit | 0.9 | False | 9/10 | G6 |
| `GH32_jinja_1664` | explicit | 0.9 | False | 9/10 | G6 |
| `GH405_narwhals_1515` | explicit | 0.89 | False | 8/9 | G6 |
| `GH139_marshmallow_2894` | explicit | 0.88 | False | 7/8 | G6 |
| `GH37_pydantic_12816` | explicit | 0.88 | False | 7/8 | G6 |
| `GH415_arrow_852` | explicit | 0.88 | False | 7/8 | G6 |
| `GH47_jinja_1706` | explicit | 0.88 | False | 7/8 | G6 |
| `GH684_starlette_3144` | explicit | 0.88 | False | 7/8 | G6 |
| `GH71_starlette_3189` | explicit | 0.88 | False | 7/8 | G6 |
| `GH140_marshmallow_2874` | explicit | 0.86 | False | 6/7 | G6 |
| `GH35_jinja_1665` | explicit | 0.86 | False | 6/7 | G6 |
| `GH371_arrow_1194` | explicit | 0.86 | False | 6/7 | G6 |
| `GH381_celery_10013` | explicit | 0.86 | False | 6/7 | G6 |
| `GH39_jinja_1762` | explicit | 0.86 | False | 6/7 | G6 |
| `GH442_arrow_1172` | explicit | 0.86 | False | 6/7 | G6 |
| `GH46_pydantic_12951` | explicit | 0.86 | False | 6/7 | G6 |
| `GH516_attrs_1513` | explicit | 0.86 | False | 6/7 | G6 |
| `GH52_jinja_1702` | explicit | 0.86 | False | 6/7 | G6 |
| `GH539_redis-py_3969` | explicit | 0.86 | False | 6/7 | G6 |
| `GH540_redis-py_3968` | explicit | 0.86 | False | 6/7 | G6 |
| `GH54_pydantic_12817` | explicit | 0.86 | False | 6/7 | G6 |
| `GH558_marshmallow_2861` | explicit | 0.86 | False | 6/7 | G6 |
| `GH566_jinja_1537` | explicit | 0.86 | False | 6/7 | G6 |
| `GH56_werkzeug_3066` | explicit | 0.86 | False | 6/7 | G6 |
| `GH60_starlette_3148` | explicit | 0.86 | False | 6/7 | G6 |

## Reproduction

- Interpreter: `/tmp/teambench_admission_gate/gate_venv/bin/python` (3.10.12)
- Staging: `harness.run_all.setup_run`, unmodified, seed 0
- Grading: `grade.sh` via a parameterised copy of `harness.run_all.grade_run` (timeout 300 s; harness cap 300 s)
- Grader invocations: 192 (1087.0 s of grader time, mean 5.66 s per invocation)
- Tasks evaluated between 2026-09-12T06:29:02.138024+00:00 and 2026-09-12T06:57:39.791805+00:00
- 1/5/15-minute load average when the summary was written: [4.62, 7.85, 6.48]
- `harness/grader_helpers.sh` sha256: `d866800dacfa9276...` (sourced by most graders)
- Every task record carries the sha256 and mtime of the `grade.sh` that was actually run, so a verdict can be rechecked against the exact grader bytes it was derived from. Graders in this repository are under active repair; a record whose hash no longer matches the file on disk describes a grader that has since changed.
- G7 is wall-clock on this machine. Grader timings scale with whatever else the machine is running, so a G7 failure should be reconfirmed on an idle host before it is reported as a property of the task. Every invocation's `grade_seconds` is in the ledger.
- Packages installed into the throwaway venv by graders during the sweep: 0

