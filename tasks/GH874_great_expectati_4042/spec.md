# GH874_great_expectati_4042: [BUGFIX] Fix s3 path suffix bug on windows — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/great-expectations/great_expectations/issues/4022
- Repo: https://github.com/great-expectations/great_expectations

## Issue Description

**Describe the bug**
On Windows when referencing an S3 data source, the prefix is suffixed with ``\`` instead of ``/``, resulting in query always failing.

**To Reproduce**
Create a ``InferredAssetS3DataConnector`` data connector, and pass any valid prefix (probably needs to be non-empty). Then, attempt to load a file from that connector.

**Expected behavior**
The file gets loaded properly.

**Error**
```
...\lib\site-packages\great_expectations\datasource\data_connector\util.py in list_s3_keys(s3, query_options, iterator_dict, recursive)
    452 
    453     if not any(key in s3_objects_info for key in ["Contents", "CommonPrefixes"]):
--> 454         raise ValueError("S3 query may not have been configured correctly.")
    455 
    456     if "Contents" in s3_objects_info:

ValueError: S3 query may not have been configured correctly.
```

**Fix**
In ``inferred_asset_s3_data_connector.py``, line 82 is:

```
        self._prefix = FilePathDataConnector.sanitize_prefix(prefix)
```

This ensures that the file path is always a folder, by appending a slash to the end. However, on Windows, the slash is ``\``, and thus you end up with a prefix like ``path/to/some/folder\``, which results in an S3 query with no results, hence the above stacktrace.

The fix is to ensure that only the correct slash can be appended to the prefix, regardless of the host OS. For example:

```
        self._prefix = prefix.rstrip('/') + '/'
```

or something to that effect.

**Environment (please complete the following information):**
 - Operating System: Windows
 - Great Expectations Version: 0.14.1

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Howdy [user], thanks for reaching out. I'm bringing this up with the team, we'll let keep you informed.

### Comment 2 ([user]):

[user] Working on a PR for this as well.

## PR Review Comments

**[user]** on `great_expectations/datasource/data_connector/inferred_asset_s3_data_connector.py`:

Could we change the name of this to `sanitize_prefix_for_s3` unless this will be used for anything else?

Additionally, would you please add this to the `ConfiguredAssetS3DataConnector`?

**[user]** on `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py`:

NIT: Is it okay to assume that every base name should be manipulated like this, and would it break an existing workflow.
A directory name could have a fullstops in this. how would you go about addressing it if this were the case?

This appears to be something that can happen, and I believe it's possible for a dot to surface in a directory name, what's a suggested workaround for cases like that?

**[user]** on `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py`:

We'd generally lean towards similar logic as [here](https://github.com/great-expectations/great_expectations/blob/develop/great_expectations/data_context/store/tuple_store_backend.py#L478-L491)

**[user]** on `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py`:

[user] My target was to provide identical behavior as the original sanitizer ``FilePathDataConnector.sanitize_prefix``, with the exception being that it did not rely on system path separators. I also avoided merely wrapping the original sanitizer with ``.replace('\\', '/')`` since both slashes are allowed in S3 paths.

I've added a new test that ensures that the new sanitizer results in exactly the same paths as the original sanitizer (following all the test cases for the original sanitizer, as well as a few additional cases). There's a little cleanup in that test case to allow it to pass on Windows, but it's worth noting that, without that cleanup, it wouldn't work on Windows, and that cleanup (as mentioned above) is not appropriate for production use. Please check the cases I list in the new test and let me know if there are any edge cases you're still worried about.

**[user]** on `tests/datasource/data_connector/test_configured_asset_s3_data_connector.py`:

[user] Here are the equality checks performed to ensure the new sanitizer does not break user code.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
