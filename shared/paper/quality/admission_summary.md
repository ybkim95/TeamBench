# TeamBench Task Admission Gate

Generated 2026-09-07T19:44:43.292042+00:00 from commit `d185aef1` on branch `iclr2027-hardening`.

Regenerate with: `python3 scripts/task_admission_gate.py --bootstrap`

Scope: 240 tasks at seed 0 (90 leaderboard tasks + 60 randomly sampled from the rest, `random.Random(0)`).

## Gate results

| Gate | Requirement | Pass | Fail | Unknown | Error |
|---|---|---:|---:|---:|---:|
| G1 | pristine floor is 0.0 | 9 | 230 | 0 | 1 |
| G2 | pristine does not pass | 235 | 5 | 0 | 0 |
| G3 | reference solution scores 1.0 | 0 | 153 | 87 | 0 |
| G4 | grader is deterministic | 238 | 2 | 0 | 0 |
| G5 | grader is hermetic (static) | 223 | 17 | 0 | 0 |
| G6 | >=50% of checks are discriminative | 151 | 88 | 0 | 1 |
| G7 | grader terminates within 300 s | 240 | 0 | 0 | 0 |

## Admission

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Tasks evaluated | 240 | 90 | 60 |
| **Pass ALL seven gates** | **0** | **0** | **0** |
| Pass six gates, G3 unknown or pass | 9 | 8 | 1 |

`Pass ALL seven gates` is the honest size of the benchmark. The second row is the ceiling that becomes reachable once every task has a reference solution proving G3; it is not a substitute for it.

Why the second row is not a substitute, concretely: `GH120_redis-py_3863` is a 22-line stub grader that writes `partial_score: 0.0` for every submission. Its floor is 0.0, it never free-passes, it is perfectly deterministic, it touches no network, its single check is never free, and it finishes instantly. It satisfies six of the seven gates. Only G3 can reject it, because no reference solution can ever score 1.0 against a grader that returns 0.0 unconditionally. A task with no demonstrated solution has not been shown to be solvable, and G3 `unknown` must never be counted as a pass.

## G1: the pristine floor

Score awarded for staging the workspace and doing nothing at all.

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Tasks measured | 239 | 89 | 60 |
| Mean floor | 0.5143 | 0.4735 | 0.5159 |
| Median floor | 0.5 | 0.5 | 0.5 |
| Floor == 0.00 (clean) | 9 | 8 | 1 |
| Floor >= 0.50 | 187 | 51 | 51 |
| Floor == 1.00 | 5 | 5 | 0 |
| Max floor | 1.0 | 1.0 | 0.75 |

Across all evaluated tasks, 887 of 1724 executed checks (51.4%) pass on the untouched workspace.

## Advisory: attestation credit

`submission/attestation.json` is a scored check in many graders. These rows re-grade the same untouched workspace after writing the harness's own passing-attestation stub (`harness.ablation._write_passing_attestation`), which is exactly what the `team_no_verify` condition writes automatically. This is score a do-nothing agent collects for filing a report.

| | All tasks | Leaderboard 90 | Sample 60 |
|---|---:|---:|---:|
| Mean floor, bare | 0.5143 | 0.4735 | 0.5159 |
| Mean floor, with attestation | 0.5138 | 0.4712 | 0.5172 |
| Tasks where attestation adds score | 2 | 1 | 1 |
| Mean credit | -0.0005 | -0.0023 | 0.0013 |
| Max credit | 0.08 | 0.08 | 0.08 |
| Tasks reaching pass=true with attestation alone | 5 | 5 | 0 |

## G5: what the static hermeticity scan found

| Violation kind | Tasks |
|---|---:|
| image_only_venv | 14 |
| npm_install | 3 |
| curl_wget | 1 |
| pip_install | 1 |

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
| GH | 163 | 0.5602 | 0 | 1 |
| RDS | 8 | 0.1615 | 0 | 2 |
| INC | 7 | 0.6171 | 0 | 1 |
| TRAP | 5 | 0.534 | 0 | 0 |
| CROSS | 5 | 0.38 | 0 | 0 |
| D | 5 | 0.668 | 0 | 0 |
| CRYPTO | 5 | 0.46 | 0 | 0 |
| TEST | 5 | 0.384 | 0 | 1 |
| CR | 4 | 0.255 | 0 | 0 |
| LH | 4 | 0.245 | 0 | 2 |
| DIST | 3 | 0.5 | 0 | 0 |
| IR | 3 | 0.7267 | 0 | 0 |
| PIPE | 3 | 0.49 | 0 | 0 |
| P | 3 | 0.3733 | 0 | 1 |
| MULTI | 2 | 0.55 | 0 | 0 |
| O | 2 | 0.53 | 0 | 0 |
| SPEC | 2 | 0.045 | 0 | 1 |
| SYNTH | 1 | 0.1 | 0 | 0 |
| INT | 1 | 0.09 | 0 | 0 |
| JS | 1 | 0.29 | 0 | 0 |
| NEG | 1 | 0.33 | 0 | 0 |
| API | 1 | 0.4 | 0 | 0 |
| INFRA | 1 | 0.3 | 0 | 0 |
| TS | 1 | None | 0 | 0 |
| SEC | 1 | 0.64 | 0 | 0 |
| GO | 1 | 0.57 | 0 | 0 |
| SCALE | 1 | 0.46 | 0 | 0 |
| S | 1 | 0.17 | 0 | 0 |

## Artifact presence

| Artifact | Tasks with it | of |
|---|---:|---:|
| `grade_sh` | 240 | 240 |
| `task_yaml` | 232 | 240 |
| `spec_md` | 207 | 240 |
| `brief_md` | 208 | 240 |
| `reference_patch` | 153 | 240 |

A task with no on-disk `spec.md` hands the agent an empty specification: no harness caller writes a generator's in-memory spec to `task_dir` at run time.

## Advisory: graders that write to a fixed `/tmp` path

13 of 240 evaluated graders write intermediate results to a literal `/tmp/...` path rather than a per-process one. Two grades of such a task running anywhere on the same host at the same time overwrite each other's file and both report whatever the loser wrote, so the task's score depends on what else the machine is doing. This sweep serialises its own invocations of these graders; it cannot serialise other processes on the host, so these rows carry residual risk.

- `CRYPTO5_tls_config`
- `CRYPTO6_token_validation`
- `GO1_concurrency_fix`
- `INC8_cascading_timeout`
- `LH5_data_migration`
- `MULTI2_microservice_debug`
- `PIPE3_msg_queue`
- `SPEC5_config_system`
- `TRAP1_spec_conflict`
- `TRAP3_metric_mirage`
- `TRAP4_version_paradox`
- `TRAP5_security_theater`
- `TRAP6_deprecated_api`

## Advisory: graders that execute a script inside the agent's workspace

1 of 240 evaluated graders run a relative script after `cd`-ing into the workspace the agent can write. The agent controls that file, so it controls its own score.

- `INC2_data_corruption`

## Worst 25 pristine floors

| Task | Scope | Floor | Pristine pass | Free / total checks | Gates failed |
|---|---|---:|---|---|---|
| `INC1_cascade_failure` | lb90 | 1.0 | True | 9/9 | G1,G2,G6 |
| `GH10_retry_backoff` | lb90 | 1.0 | True | 11/11 | G1,G2,G6 |
| `GH11_middleware_order` | lb90 | 1.0 | True | 10/10 | G1,G2,G6 |
| `GH1_flask_session_ctx` | lb90 | 1.0 | True | 7/7 | G1,G2,G6 |
| `GH7_fixture_scope_leak` | lb90 | 1.0 | True | 9/9 | G1,G2,G6 |
| `IR4_temporal` | lb90 | 0.93 | False | 13/14 | G1,G6 |
| `IR3_multi_source` | lb90 | 0.92 | False | 11/12 | G1,G6 |
| `INC3_memory_leak` | lb90 | 0.91 | False | 10/11 | G1,G6 |
| `D7_etl_reconciliation` | lb90 | 0.9 | False | 9/10 | G1,G6 |
| `LH3_multi_service` | lb90 | 0.9 | False | 18/20 | G1,G6 |
| `GH112_redis-py_3996` | lb90 | 0.86 | False | 6/7 | G1,G3,G6 |
| `GH539_redis-py_3969` | reference | 0.86 | False | 6/7 | G1,G3,G6 |
| `GH103_redis-py_3998` | lb90 | 0.82 | False | 9/11 | G1,G3,G6 |
| `TRAP6_deprecated_api` | lb90 | 0.8 | False | 8/10 | G1,G5,G6 |
| `GH2_click_flag_value` | lb90 | 0.78 | False | 7/9 | G1,G6 |
| `PIPE3_msg_queue` | lb90 | 0.77 | False | 10/13 | G1,G6 |
| `GH1177_numpy_31079` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH1209_pytorch_176603` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH379_aiohttp_12240` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH900_scikit_learn_14286` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH916_scikit_learn_22191` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH978_pandas_64846` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH979_numpy_30965` | sample60 | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH1027_scipy_24761` | reference | 0.75 | False | 3/4 | G1,G3,G6 |
| `GH1058_ray_15056` | reference | 0.75 | False | 3/4 | G1,G3,G6 |

## Reproduction

- Interpreter: `/tmp/teambench_admission_gate/gate_venv/bin/python` (3.10.12)
- Staging: `harness.run_all.setup_run`, unmodified, seed 0
- Grading: `grade.sh` via a parameterised copy of `harness.run_all.grade_run` (timeout 300 s; harness cap 300 s)
- Grader invocations: 870 (23703.6 s of grader time, mean 27.25 s per invocation)
- Tasks evaluated between 2026-09-07T19:00:23.796490+00:00 and 2026-09-07T19:41:26.054677+00:00
- 1/5/15-minute load average when the summary was written: [2.02, 8.01, 9.64]
- `harness/grader_helpers.sh` sha256: `d6b470f88660cfce...` (sourced by most graders)
- Every task record carries the sha256 and mtime of the `grade.sh` that was actually run, so a verdict can be rechecked against the exact grader bytes it was derived from. Graders in this repository are under active repair; a record whose hash no longer matches the file on disk describes a grader that has since changed.
- G7 is wall-clock on this machine. Grader timings scale with whatever else the machine is running, so a G7 failure should be reconfirmed on an idle host before it is reported as a property of the task. Every invocation's `grade_seconds` is in the ledger.
- Packages installed into the throwaway venv by graders during the sweep: 0

