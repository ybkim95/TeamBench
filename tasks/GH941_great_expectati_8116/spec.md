# GH941_great_expectati_8116: [BUGFIX] Fix GXCloudStoreBackend updates by name — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

- Fix bug in update object by name flows (add_or_update, update) caused by not taking into account different structure of response from cloud (list of objects vs. single object)

- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [ ] Code is linted - run `invoke lint` (uses `black` + `ruff`)
- [ ] Appropriate tests and docs have been updated

For more details, see our [Contribution Checklist](https://docs.greatexpectations.io/docs/contributing/contributing_checklist), [Coding style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/code_style), and [Documentation style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/docs_style).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!

## PR Review Comments

**[user]** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

Hmm is there any way we can do this without specifically `isinstance` checking? I think this logic makes sense but just trying to brainstorm

**[user]** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

also do our `TypedDict`'s need to be updated at all for this singular vs multiple resource logic? Can we be consistent and always return a list or does that not make sense?

**[user]** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

Maybe we encapsulate this into a helper?

**[user]** on `tests/data_context/cloud_data_context/test_checkpoint_crud.py`:

Nit - no need to us `as` here

**[user]** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

Which TypedDicts are you referring to? `ResponsePayload`? Hm, looking at `ResponsePayload`, looks like the `data` field is incorrect. It currently says `data` field is `PayloadDataField`, but it can also be `list[PayloadDataField]` - does that annotation make sense?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
