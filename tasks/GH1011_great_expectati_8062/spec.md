# GH1011_great_expectati_8062: [BUGFIX] Ensure CloudDataContext Add Checkpoint flow returns Checkpoint with cloud-updated values — Full Specification (Planner Only)

## Source
- PR: https://github.com/great-expectations/great_expectations/pull/8062
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

**@Kilo59** on `tests/data_context/cloud_data_context/test_checkpoint_crud.py`:

`non-blocking`
Can we use `responses` to mock this post?
https://github.com/getsentry/responses#shortcuts
https://github.com/getsentry/responses#dynamic-responses

**@Kilo59** on `tests/data_context/cloud_data_context/test_checkpoint_crud.py`:

@roblim are these passing for you locally?

**@Kilo59** on `great_expectations/data_context/store/gx_cloud_store_backend.py`:

Is this overriding an inherited method?

**@cdkini** on `great_expectations/data_context/store/checkpoint_store.py`:

We have to do this at the store level? I'd love to encapsulate it at the store backend level so we don't have Cloud-specific logic here but I think that's a separate issue.

**@cdkini** on `great_expectations/data_context/store/checkpoint_store.py`:

Suggestion:
```python
checkpoint_ref_config = checkpoint_ref.response["data"]["attributes"]["checkpoint_config"]
checkpoint.config.validations = checkpoint_ref_config.get("validations")
checkpoint.config.action_list = checkpoint_ref_config.get('action_list")
```

## Files Changed in Fix

- `great_expectations/data_context/data_context/cloud_data_context.py` (modified, +10/-9)
- `great_expectations/data_context/store/checkpoint_store.py` (modified, +8/-2)
- `pyproject.toml` (modified, +3/-0)
- `tests/data_context/cloud_data_context/test_checkpoint_crud.py` (modified, +138/-24)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/data_context/cloud_data_context.py`
```diff
@@ -764,15 +764,16 @@ def add_checkpoint(  # noqa: PLR0913
             checkpoint=checkpoint,
         )
 
-        checkpoint_config = self.checkpoint_store.create(
-            checkpoint_config=checkpoint.config
-        )
-
-        from great_expectations.checkpoint.checkpoint import Checkpoint
-
-        return Checkpoint.instantiate_from_config_with_runtime_args(
-            checkpoint_config=checkpoint_config, data_context=self  # type: ignore[arg-type]
-        )
+        try:
+            return self.checkpoint_store.add_checkpoint(checkpoint)
+        except gx_exceptions.CheckpointError as e:
+            # deprecated-v0.16.16
+            warnings.warn(
+                f"{e.message}; using add_checkpoint to overwrite an existing value is deprecated as of v0.16.16 "
+                "and will be removed in v0.18. Please use add_or_update_checkpoint instead.",
+                DeprecationWarning,
+            )
+            return self.checkpoint_store.add_or_update_checkpoint(checkpoint)
 
     def list_checkpoints(self) -> Union[List[str], List[ConfigurationIdentifier]]:
         return self.checkpoint_store.list_checkpoints(ge_cloud_mode=True)
```

### `great_expectations/data_context/store/checkpoint_store.py`
```diff
@@ -19,7 +19,6 @@
     DataContextConfigDefaults,
 )
 from great_expectations.data_context.types.refs import (
-    GXCloudIDAwareRef,
     GXCloudResourceRef,
 )
 from great_expectations.data_context.types.resource_identifiers import (  # noqa: TCH001
@@ -251,9 +250,16 @@ def _persist_checkpoint(
         persistence_fn: Callable,
     ) -> Checkpoint:
         checkpoint_ref = persistence_fn(key=key, value=checkpoint.get_config())
-        if isinstance(checkpoint_ref, GXCloudIDAwareRef):
+        if isinstance(checkpoint_ref, GXCloudResourceRef):
+            # update parts of config that may have been updated by cloud (ids, default actions, etc.)
             cloud_id = checkpoint_ref.id
             checkpoint.config.ge_cloud_id = cloud_id
+            checkpoint.config.validations = checkpoint_ref.response["data"][
+                "attributes"
+            ]["checkpoint_config"].get("validations")
+            checkpoint.config.action_list = checkpoint_ref.response["data"][
+                "attributes"
+            ]["checkpoint_config"].get("action_list")
         return checkpoint
 
     @public_api
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
