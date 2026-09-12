# GH989_great_expectati_8084: [BUGFIX] Fix Update Checkpoint for Cloud — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

Update Checkpoint operations (`add`, `update`, `add_or_update`) were broken for cloud in two ways:
1. `GXCloudStoreBackend` did not support updating Checkpoints by name. If `add_or_update` was called once, a new Checkpoint would be added, and the returned Checkpoint (in memory) would be properly updated with the new `id`. If the same method was called again with the same in-memory objects, the update operation would work, but if the same script was run at a later time, the operation would fail due to absence of `id` (GX would attempt adding a new Checkpoint with the same name, which violates unique constraint).
2. Since update Checkpoint operations use a PUT request, no object is returned with the response, which prevented GX from returning complete/updated Checkpoint configs (since cloud may add default values and/or assign new ids to Validations).
3. Similar errors would also occur in add operations if the returned Checkpoint object was not properly updated.

These bugs were fixed by:
1. Adding update by name support to `GXCloudStoreBackend`. The update flow was already checking for record existence by attempting to GET a resource, but the returned object was not being used. Instead, if the object exists, the update key is updated with the appropriate id if missing. 
2. Upon successful completion of an Update operation, the Checkpoint is re-fetched and returned from Cloud.
3. Since add operations use a POST request, which returns a complete Checkpoint config, logic was updated to simply return this Checkpoint config, rather than manually updating attributes on the existing in-memory Checkpoint.

- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [ ] Code is linted - run `invoke lint` (uses `black` + `ruff`)
- [ ] Appropriate tests and docs have been updated

For more details, see our [Contribution Checklist](https://docs.greatexpectations.io/docs/contributing/contributing_checklist), [Coding style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/code_style), and [Documentation style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/docs_style).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!

## PR Review Comments

**[user]** on `great_expectations/data_context/data_context/abstract_data_context.py`:

Should this be `Checkpoint`? The class itself? Or should it be `result.name`?

**[user]** on `great_expectations/data_context/data_context/cloud_data_context.py`:

Should we maybe always return a `CheckpointConfig`? Feels a little odd that we have this union (but maybe a matter for another time)

**[user]** on `great_expectations/data_context/data_context/abstract_data_context.py`:

Great catch! Fixing

**[user]** on `great_expectations/data_context/data_context/abstract_data_context.py`:

Addressed in (withheld: the upstream fix is not part of the task)commits/d21a474ecc16d15000eefc368c05fbee79ec5d63

**[user]** on `great_expectations/data_context/store/checkpoint_store.py`:

Are we guaranteed to have "id" in `checkpoint_config`? Will this `pop()` possible cause a runtime issue?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
