# GH528_poetry_10719: Fix AssertionError when cloning at annotated tag — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-poetry/poetry

## PR Description

When cloning a Git repository at an annotated tag, if the peeled tag reference (refs/tags/v1.0.0^{}) is not available in the fetch result, Poetry would set HEAD to the tag object SHA instead of the commit SHA. This caused reset_index() to fail with:

```
  AssertionError: assert isinstance(obj, Commit)
```

The fix peels tag objects recursively to extract the underlying commit SHA before setting HEAD. This ensures HEAD always points to a Commit object, not a Tag object.

Dulwich has already been updated to print clearer errors in this situation, which should be in 1.0.1

# Pull Request Check List

Resolves: #10658

- [x] Added **tests** for changed code.
- [x] Updated **documentation** for changed code.

## PR Review Comments

**[user]** on `tests/vcs/git/test_backend.py`:

**suggestion (testing):** Strengthen the test by asserting that HEAD matches the expected commit SHA, not just that it is a Commit object.

In `test_clone_annotated_tag`, you currently only check that `HEAD` is a `Commit`, which guards against it being a `Tag`. To make the test stronger, also assert that this `Commit` is the one created in the source repo by capturing its SHA (e.g., from `porcelain.commit` or `repo.head()` before tagging) and comparing that value to `head_sha`. This verifies both the type and that the peeling logic resolves to the correct commit.

Suggested implementation:

```python
    from dulwich import porcelain
    from dulwich.objects import Commit

```

```python
    # Create a source repository with an annotated tag

```

```python
    repo = Repo.init(str(source_path))

```

```python
    # HEAD should be a commit (not a Tag) and it should be the same commit
    # that was created in the source repository before tagging.
    assert isinstance(head, Commit)
    assert head_sha == expected_head_sha

```

I only see the beginning of `test_clone_annotated_tag`, so you will need to wire in the expected SHA where the initial commit is created:

1. When you create the commit in the source repository (likely via `porcelain.commit` or `repo.do_commit`), capture its SHA, for example:
   - If using `porcelain.commit(str(source_path), message=b"Initial commit")`, assign the return value to `expected_head_sha`.
   - If using `repo.do_commit(...)`, use `expected_head_sha = repo.head()` (or `repo[repo.head()].id` depending on how you compute `head_sha`).
2. Ensure that `head_sha` in the assertion block refers to the SHA of `HEAD` in the cloned repo (whatever variable you currently derive from the peeled `HEAD` object).
3. Make sure `expected_head_sha` is defined in the same scope as the final assertions so that `assert head_sha == expected_head_sha` compiles and runs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
