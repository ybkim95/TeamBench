# GH288_osparc-simcore_6935: 🐛 Fix deletion of files in folders — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ITISFoundation/osparc-simcore/issues/26
- Repo: https://github.com/ITISFoundation/osparc-simcore

## Issue Description

**User story**

As a **developer** I want to be able to create arbitrary pipelines out of computational services in the frontend. Mockup services can be used for finding compatible services but the metadata for input/output data structures need to be defined such that they can be used for the MVP.

**Definition of Done**

- [x] Services can interactively added to the pipeline
- [x] Only compatible services can be attached to each other
- [x] Define data structure needed for this (compatible with the pipeline that is being use in the comp. backend)
- [x] Multiple in- and outputs can exist (ports)
- [x] Settings can be defined by input
- [x] Branching

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

* datastandards
* jason.ad
* decided for

### Comment 2 ([user]):

all settings are inputs, with a default
- [ ] the link shall be deletable
- [ ] the settings is read-only when a node is connected
- [ ] all settings visible in the workbench view

## PR Review Comments

**[user]** on `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py`:

TYPO: known :-)

**[user]** on `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py`:

THOUGHT: This is the perfect example to use `conn.stream` when we upgrade `db_file_meta_data.list_fmds`.  This way we can stream the numbers until finding a match ...

or even better create a request that finds the match in the database?

**[user]** on `services/storage/src/simcore_service_storage/simcore_s3_dsm.py`:

this read strange to me.

1. you call `find_enclosing_file` with a given `file_id`
2. you get a "match" to your call  (i.e. `enclosing_file!=None`)

therefore, how can you still have the possibility of "not matching" that file? i.e. `enclosing_file.file_id != file_id` ??

**[user]** on `services/storage/tests/unit/test_handlers_files.py`:

we need to do a renaming of these things later, maybe in a separate PR. cause I don't understand what "legacy" means here ;)

**[user]** on `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py`:

here you are listing all the files of 'user_id'. that can be very heavy.
you have as argument the file_id, which at least contains the `project_id`, and possibly the `node_id` (if it is not a PublicAPI file), so you should be able to filter by them as well.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
