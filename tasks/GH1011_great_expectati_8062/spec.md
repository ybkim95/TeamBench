# GH1011_great_expectati_8062: [BUGFIX] Ensure CloudDataContext Add Checkpoint flow returns Checkpoint with cloud-updated values — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

Currently, when a new Checkpoint is added using `CloudDataContext.add_checkpoint` or `CloudDataContext.add_or_update_checkpoint` methods, the Checkpoint returned is only updated with the new cloud-assigned id. This is problematic because GX Cloud also assigns new validation ids and default actions.

This PR ensures that these methods return a Checkpoint object that has been updated from properties present from the GX Cloud POST response.

- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [ ] Code is linted

    ```
    black .

    ruff . --fix
    ```
- [ ] Appropriate tests and docs have been updated

For more details, see our [Contribution Checklist](https://docs.greatexpectations.io/docs/contributing/contributing_checklist), [Coding style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/code_style), and [Documentation style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/docs_style).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!

## PR Review Comments

**[user]** on `tests/data_context/cloud_data_context/test_checkpoint_crud.py`:

`non-blocking`
Can we use `responses` to mock this post?
https://github.com/getsentry/responses#shortcuts
https://github.com/getsentry/responses#dynamic-responses

**[user]** on `tests/data_context/cloud_data_context/test_checkpoint_crud.py`:

[user] are these passing for you locally?

**[user]** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

Is this overriding an inherited method?

**[user]** on `great_expectations/data_context/store/checkpoint_store.py`:

We have to do this at the store level? I'd love to encapsulate it at the store backend level so we don't have Cloud-specific logic here but I think that's a separate issue.

**[user]** on `great_expectations/data_context/store/checkpoint_store.py`:

Suggestion:
```python
checkpoint_ref_config = checkpoint_ref.response["data"]["attributes"]["checkpoint_config"]
checkpoint.config.validations = checkpoint_ref_config.get("validations")
checkpoint.config.action_list = checkpoint_ref_config.get('action_list")
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
