# GH1182_mlflow_21810: Fix llama-index 0.14.16 test failures for flattened workflow span inputs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### Related Issues/PRs

Resolves LlamaIndex test failures like https://github.com/mlflow/dev/actions/runs/23247456249/job/67635766887#step:13:551

### What changes are proposed in this pull request?

`llama-index >= 0.14.16` changed how `Workflow.run()` is instrumented, putting user kwargs inside
  a `StartEvent` object instead of passing them as raw `bound_args`. This changed the format of captured inputs in a span and broke the assersion.

**Note**

This PR does **not** fix all of the failed tests. There are multiple different compatibility issues with the latest llama-index. This PR focuses on the kwargs assertion, leaving out model test and the streaming test case below.


* Tests fixed in this PR
  * `test_llama_index_autolog.py::test_autolog_link_traces_to_loaded_model_workflow`
  * `test_llama_index_autolog.py::test_autolog_link_traces_to_loaded_model_workflow_pyfunc`
  * `test_llama_index_autolog.py::test_model_loading_set_active_model_id_without_fetching_logged_model`
  * `test_llama_index_tracer.py::test_tracer_parallel_workflow`
  * `test_llama_index_tracer.py::test_tracer_parallel_workflow_with_custom_spans `
* Tests **not** fixed in this PR
  * `test_llama_index_tracer.py::test_trace_chat_engine[False-True]`
  * models test



### How is this PR tested?

- [x] Existing unit/integration tests

### Does this PR require documentation update?

- [x] No.

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

- [x] No.

### Release Notes

#### Is this a user-facing change?

- [x] No.

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [x] `area/tracing`: MLflow Tracing features, tracing APIs, and LLM tracing functionality

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

## PR Review Comments

**[user]** on `mlflow/llama_index/tracer.py`:

q: is there any case start_event is StartEvent but doesn't have to_dict?

**[user]** on `mlflow/llama_index/tracer.py`:

Nope, we can remove this condition

**[user]** on `mlflow/llama_index/tracer.py`:

```suggestion
        if isinstance(start_event, StartEvent):
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
