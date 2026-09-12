# GH1031_mlflow_21922: Fix Anthropic structured outputs compatibility in gateway adapter — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### Related Issues/PRs

Relates to #21739

### What changes are proposed in this pull request?

When using Anthropic models via the gateway adapter (e.g. for `discover_issues()` or judge evaluation), two issues cause 400 errors:

### How is this PR tested?

- [x] Existing unit/integration tests
- [x] Manual tests

Tested end-to-end with `anthropic:/claude-sonnet-4-5-20250929` via `discover_issues()` and the Playwright E2E script.

https://github.com/user-attachments/assets/ff8df9c6-b98a-42d9-8c9f-9b85b0ce8bac

### Does this PR require documentation update?

- [x] No.

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

- [x] No.

### Release Notes

#### Is this a user-facing change?

- [x] Yes. Fix Anthropic models failing with 400 errors when used as judge models for evaluation and issue detection via the gateway adapter.

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [x] `area/gateway`: MLflow AI Gateway client APIs, server, and third-party integrations
- [x] `area/evaluation`: MLflow model evaluation features, evaluation metrics, and evaluation workflows

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [x] This PR can wait for the next minor release

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## PR Review Comments

**[user]** on `mlflow/metrics/genai/model_utils.py`:

🔴 **CRITICAL:** This retry trigger relies on the literal substring "does not support output format", but that string doesn’t appear anywhere else in the codebase. If the upstream error wording differs, the fallback will never run and the 400s will persist. Prefer keying off a structured signal (e.g., HTTP 400 + provider error type/code parsed from the response body) instead of a hard-coded message substring.
```suggestion
            if getattr(e, "error_code", None) != INVALID_PARAMETER_VALUE:
```

**[user]** on `mlflow/metrics/genai/model_utils.py`:

🟡 **MODERATE:** `_send_request()` raises a new `MlflowException` without chaining the original `HTTPError` (`from e`), which makes debugging harder (loses the original traceback/context like status code). Consider raising with exception chaining so callers can still inspect the root exception.
```suggestion
        ) from e
```

**[user]** on `mlflow/metrics/genai/model_utils.py`:

🟡 **MODERATE:** New behavior (retrying without `output_config`/`response_format` and including HTTP response bodies in errors) isn’t covered by unit tests in `tests/metrics/genai/test_model_utils.py`, which already exercises this module. Add tests that (1) simulate an HTTP 400 indicating unsupported structured output and assert a second request is made with those fields removed, and (2) assert the raised error message includes the response body.

**[user]** on `mlflow/gateway/providers/anthropic.py`:

🔴 **CRITICAL:** `_enforce_strict_schema()` unconditionally overwrites `additionalProperties` for every `{ "type": "object" }`. For schemas that intentionally model dictionaries via `additionalProperties: { ... }`, this changes the meaning to “no properties allowed” (often making the only valid value `{}`), which can silently break structured outputs. Consider detecting map-like schemas (`additionalProperties` is a dict / schema) and either (a) failing fast with a clear error that Anthropic structured outputs don’t support dict-shaped objects, or (b) transforming the schema into a representable structure (e.g., array of key/value entries) instead of forcing `additionalProperties: false`.

**[user]** on `mlflow/gateway/providers/anthropic.py`:

🟡 **MODERATE:** The strict-schema sanitization is applied in-place to `json_schema["schema"]` and can materially change the request payload. There’s no test coverage asserting the sanitization behavior (e.g., that nested objects get `additionalProperties: false`, and that dict-like `additionalProperties: { ... }` is handled as intended). Add a unit test in `tests/gateway/providers/test_anthropic.py` exercising the new sanitization so future schema changes don’t reintroduce 400s or change semantics unintentionally.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
