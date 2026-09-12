# GH1210_wandb_11242: fix(artifacts): fetch new presigned download url when expires — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

The new version of (withheld: the upstream fix is not part of the task)

Description
-----------

- Fixes WB-30412

When server side sign a download url with a short expiration time and the file is large, the presigned url can expire. Existing multipart download would fail directly because it does not fetch a new presigned url for the failed parts.

Instead of changing expiration duration on server side, send a new graphql request to get a new not expired download url. Different parts can reuse same refreshed download url, no need to fetch a new url as long as current one is valid.

### Changed

- Add url fetching logic in multipart download
- Clean up multipart download, existing function is too long
- Clean up the mock in multipart download unit test, I introduced those stuff when adding multipart download ...
- [x] I updated CHANGELOG.unreleased.md, or it's not applicable

Things to clean up

- [x] repeated server support check, `server_features` has LRU cache per client instance
- [x] the invalidation and retry logic in the shared url provider

Testing
-------
How was this PR tested?

- [x] unit test
- [x] system test
- [ ] e2e manual test, set server expiration time to 1 minute and see if it works

## PR Review Comments

**[user]** on `tests/unit_tests/test_artifacts/test_wandb_artifacts.py`:

**suggestion:** this is a lot of boilerplate to mock an open file.  There are well-developed / established tools for this already, and our tests will generally be less brittle -- not to mention much easier to maintain -- if we avoid reinventing the wheel :)

I think this can probably be replaced with existing mock APIs (within a test, use the `mocker` fixture from `pytest-mock` -- [docs](https://pytest-mock.readthedocs.io/en/latest/usage.html)).  Including:
- `mocker.mock_open` -- which is just the builtin `mock.mock_open` ([docs](https://docs.python.org/3/library/unittest.mock.html#mock-open))
- `mocker.spy` -- you do need the `mocker` fixture for this, as this is specific to `pytest-mock`, but you can use it to track call counts ([docs](https://pytest-mock.readthedocs.io/en/latest/usage.html#spy))
- `mocker.patch.object(file, "seek", side_effect=SomeError("some error message")` to simulate the error on `IO.seek()`.
  - Also, I forget which error `IO.seek()` actually raises when the file is closed, but it's likely to be a subtype of `OSError` so at the very least, you probably want to raise an `OSError`

**[user]** on `tests/unit_tests/test_artifacts/test_wandb_artifacts.py`:

**suggestion:** similarly here -- am wondering, do we need to hand-craft our own mock classes from scratch just for these tests?

**[user]** on `wandb/sdk/artifacts/storage_policies/_url_provider.py`:

**note:** this adds a lot of complexity for something that seems like it can be handled with builtins and ultimately requires a callback that's defined elsewhere (`fetch_fn`).  The latter isn't a dealbreaker, but in Python it can lead to really hard-to-debug code (not to mention really noisy/unhelpful stack traces) if not handled well

Let me come back to this after taking a closer look at what it's doing -- at a glance it looks like a thread-safe generator with an extra TTL mechanism, and I'd like to better understand why we might need to implement this from scratch

**[user]** on `wandb/sdk/artifacts/artifact.py`:

**question:** Not sure I fully understand -- why are we migrating the init logic for `ArtifactFiles` ( https://github.com/wandb/wandb/blob/f8a477323ec0a1666f2c8eeb619cd54714faab11/wandb/apis/public/artifacts.py#L847) to here?

**[user]** on `wandb/sdk/artifacts/artifact.py`:

**question:** as above, this seems really unnecessary at first glance but would like to understand better -- why not just fetch the first result from an `ArtifactFiles` iterator instead?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
