# G3: does the upstream reference solution pass the task's own grader?

Generated 2026-09-05T05:42:40.283259+00:00 · commit `d185aef1` · branch `iclr2027-hardening` · seed 0 · 8 workers · rebuilt from the checkpoint, no grading in this invocation.

Scope: every task with an authoritative upstream patch at `tasks/<id>/reference/patch.diff` and a `grade.sh`. 631 tasks.

Applier: `harness/reference_apply.py`. The reference is applied to the generator's own unparameterised base and the generator's parameterisation is then replayed on the patched base with the symbol rename map frozen to the staged instance's map, so what lands in the workspace is the upstream fix expressed in the seed's identifier space.

## The three-way split

| Outcome | Meaning | Tasks | Share |
|---|---|---:|---:|
| `a_validated` | reference applies and the grader gives 1.0 | 0 | 0.0% |
| `b_grader_rejects_reference` | reference applies, grader does **not** give 1.0 | 604 | 95.7% |
| `c_unappliable` | reference cannot be applied by any method | 11 | 1.7% |
| `d_inconclusive_grader_timeout` | a grade hit the 300 s harness cap: inconclusive, not a rejection | 16 | 2.5% |

Hunk-level accounting over the whole corpus: 3740 hunks, 3669 applied, 52 already at their post state (the workspace ships the PR's test files), 9 unappliable (99.5% reached the post state).

## How the reference was applied

| Method | Tasks |
|---|---:|
| `reparam` | 588 |
| `reparam-static` | 30 |
| `direct` | 2 |

## Bucket (b): the grader disagrees with the upstream fix

604 tasks. Mean reference partial score 0.5554, range [0.25, 0.86].

- 539 score *exactly* the pristine do-nothing floor: the grader is blind to the upstream fix.
- 0 score *below* the pristine floor: applying the upstream fix loses points.
- 0 produced no effective change in the workspace (every file the fix touches is out of the workspace's scope).

Most frequently failed check ids among bucket (b):

| Check id | Tasks failing it |
|---|---:|
| `C1` | 604 |
| `C5` | 498 |
| `C8` | 134 |
| `C9` | 72 |
| `C10` | 58 |
| `C3` | 44 |
| `C2` | 16 |
| `C11` | 13 |
| `C6` | 6 |
| `C7` | 3 |
| `C12` | 1 |

## By family

| Family | `a_validated` | `b_grader_rejects_reference` | `c_unappliable` | `d_inconclusive_grader_timeout` | `error` | n |
|---|---|---|---|---|---|---|
| GH | 0 | 604 | 11 | 16 | 0 | 631 |

Pristine floor over the same 619 tasks: mean 0.5391, exactly zero on 0.

## Worked examples from bucket (b)

### GH1057_ray_28511

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 19 hunks applied / 0 already / 19 total; files written: python/ray/tune/execution/ray_trial_executor.py, python/ray/tune/execution/trial_runner.py, python/ray/tune/schedulers/pbt.py, python/ray/tune/tests/test_trial_scheduler.py, python/ray/tune/tests/test_trial_scheduler_pbt.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH1073_spaCy_13249

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 2 hunks applied / 0 already / 2 total; files written: spacy/ml/models/textcat.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH946_autogluon_3288

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 12 hunks applied / 0 already / 12 total; files written: common/src/autogluon/common/utils/path_converter.py, core/src/autogluon/core/models/abstract/abstract_model.py, core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py, core/src/autogluon/core/trainer/abstract_trainer.py, tabular/tests/conftest.py, tabular/tests/unittests/models/test_dummy.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH1121_wandb_11207

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 10 hunks applied / 0 already / 10 total; files written: CHANGELOG.unreleased.md, tests/fixtures/mock_wandb_log.py, tests/unit_tests/test_wandb_settings.py, wandb/_pydantic/__init__.py, wandb/sdk/wandb_settings.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH907_autogluon_4272

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 1 hunks applied / 0 already / 1 total; files written: tabular/src/autogluon/tabular/models/lgb/lgb_model.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH949_gpytorch_1446

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 8 hunks applied / 0 already / 8 total; files written: gpytorch/kernels/rff_kernel.py, gpytorch/lazy/low_rank_root_added_diag_lazy_tensor.py, gpytorch/lazy/low_rank_root_lazy_tensor.py, gpytorch/lazy/root_lazy_tensor.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH1149_featuretools_2380

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 23 hunks applied / 0 already / 23 total; files written: docs/source/release_notes.rst, featuretools/primitives/base/aggregation_primitive_base.py, featuretools/primitives/base/primitive_base.py, featuretools/synthesis/deep_feature_synthesis.py, featuretools/synthesis/utils.py, featuretools/tests/conftest.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

### GH906_ray_29102

- reference partial **0.25**, pristine floor 0.25, delta 0.0
- applied by `reparam`, 26 hunks applied / 0 already / 26 total; files written: python/ray/tune/examples/pb2_example.py, python/ray/tune/examples/pbt_function.py, python/ray/tune/schedulers/pb2.py, python/ray/tune/schedulers/pbt.py, python/ray/tune/tests/test_trial_scheduler.py, python/ray/tune/tests/test_trial_scheduler_pbt.py
- checks the upstream fix fails: `C1`, `C3`, `C5`

