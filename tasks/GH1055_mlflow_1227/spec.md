# GH1055_mlflow_1227: Fix download from URI. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

## What changes are proposed in this pull request?
Fix download from URI functionality. 

### Background
The mlflow.tracking._download_artifact_from_uri() method splits artifact URIs into (directory_name, base_name) tuples. However, when a URI is of the form gs://<bucket_name> the resulting split is

```
dir_name = "gs:"
bucket_name = "<bucket_name>"
```
The method then attempts to instantiate an ArtifactRepository with artifact_uri=dir_name. The resulting repository does not work properly if dir_name="gs:".
 
## How is this patch tested?
 
Added a test verifying that _download_from_uri(artifact_uri) translates to expected pair of artifact root, artifact path. The rest it up to the appropriate Artifact Repository and does not need to be tested here.  

## Release Notes
 
### Is this a user-facing change? 

- [x ] No. You can skip the rest of this section.
- [ ] Yes. Give a description of this change to be included in the release notes for MLflow users.
 
(Details in 1-2 sentences. You can just refer to another PR with a description if this PR is part of a larger change.)
 
### What component(s) does this PR affect?
 
- [ ] UI
- [ x] CLI 
- [ ] API 
- [ ] REST-API 
- [ ] Examples 
- [ ] Docs
- [x] Tracking
- [ ] Projects 
- [x] Artifacts 
- [x] Models 
- [ ] Scoring 
- [ ] Serving
- [x] R
- [ ] Java
- [x] Python

### How should the PR be classified in the release notes? Choose one:
 
- [ ] `rn/breaking-change` - The PR will be mentioned in the "Breaking Changes" section
- [x] `rn/none` - No description will be included. The PR will be mentioned only by the PR number in the "Small Bugfixes and Documentation Updates" section
- [ ] `rn/feature` - A new user-facing feature worth mentioning in the release notes
- [ ] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes
- [ ] `rn/documentation` - A user-facing documentation change worth mentioning in the release notes

## PR Review Comments

**[user]** on `tests/store/test_cli.py`:

Nit: Can we test `file:` URIs with a single forward slash? E.g., `file:/path/to/artifact`.

**[user]** on `tests/store/test_cli.py`:

It's probably a better idea to use [mock](https://pypi.org/project/mock/) here and mock the [get_artifact_repository](https://github.com/mlflow/mlflow/blob/8582b5b83aa1896ac7af6423572a0080425db006/mlflow/store/artifact_repository_registry.py#L89) method, rather than its implementation. Using mock will also ensure that an unexpected failure in this individual test case does not cause subsequent failures for all test cases depending on `get_artifact_repository`.

**[user]** on `tests/store/test_cli.py`:

Is that a valid file uri?

**[user]** on `tests/store/test_cli.py`:

This should not affect other tests, it's in a try/finally,

I tried to use mock but it was too difficult to get it to do what I want. If you know how can this be done with mock easily I'll be happy to change it ;)

**[user]** on `tests/store/test_cli.py`:

NEvermind, I looked it up and it is a valid path. I'll add a test case for it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
