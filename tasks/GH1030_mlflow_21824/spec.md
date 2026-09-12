# GH1030_mlflow_21824: Fix tar path traversal vulnerability in `extract_archive_to_dir` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### Related Issues/PRs

Relates to https://huntr.com/bounties/09856f77-f968-446f-a930-657d126efe4e

### What changes are proposed in this pull request?

Fixes a tar path traversal (zip-slip) vulnerability in `extract_archive_to_dir` where crafted tar archives with `../` entries or malicious symlink targets could write files outside the extraction directory.

**Changes:**
- **`mlflow/pyfunc/dbconnect_artifact_cache.py`**: Replace `tar.extractall()` with `_safe_extractall()` that validates each member's resolved path stays within `dest_dir` before extracting (defense-in-depth).
- **`mlflow/utils/file_utils.py`**: Harden `check_tarfile_security` to also validate symlink members — reject absolute paths/escape paths in symlink names, and reject symlink targets that are absolute or resolve outside the extraction directory.
- **`tests/utils/test_file_utils.py`**: Add regression tests for symlink target validation and an end-to-end `extract_archive_to_dir` traversal test.

### How is this PR tested?

- [x] Existing unit/integration tests
- [x] New unit/integration tests

### Does this PR require documentation update?

- [x] No.

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

- [x] No.

### Release Notes

#### Is this a user-facing change?

- [x] Yes. Fix tar path traversal vulnerability in pyfunc archive extraction that could allow arbitrary file writes from crafted tar archives.

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [x] `area/scoring`: MLflow Model server, model deployment tools, Spark UDFs

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [x] This PR is critical and needs to be in the next patch release
- [ ] This PR can wait for the next minor release

## PR Review Comments

**[user]** on `mlflow/pyfunc/dbconnect_artifact_cache.py`:

tar doesn't work with pathlib?

**[user]** on `mlflow/utils/file_utils.py`:

```suggestion
                raise MlflowException.invalid_parameter_value(
```

**[user]** on `tests/utils/test_file_utils.py`:

```suggestion
    def create_tar_with_symlink_only(tar_path: Path, link_name: str, link_target: str) -> None:
```

can we use Path object?

**[user]** on `tests/utils/test_file_utils.py`:

can we move this to top?

**[user]** on `tests/utils/test_file_utils.py`:

🟡 **MODERATE:** `test_extract_archive_to_dir_blocks_traversal` only exercises `check_tarfile_security()` (it fails before `_safe_extractall()` runs), so the new defense-in-depth path resolution logic in `_safe_extractall` isn’t covered. Add a test where the tar member path is “safe” per `check_tarfile_security` but escapes via an existing filesystem symlink inside `dest_dir`, which `_safe_extractall` should block.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
