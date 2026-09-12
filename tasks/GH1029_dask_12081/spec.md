# GH1029_dask_12081: Fix mixed HLG/Expr handling in ``_ExprSequence._simplify_down`` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/9117
- Repo: https://github.com/dask/dask

## Issue Description

The purpose of this issue is to agree on a development plan for the design I have roughly prototyped in dask#8980.  The addition of a new `CollectionOperation` class (or similar) corresponds to a significant design change in Dask. Therefore, I propose that we push on this work in a new branch of dask/dask. 

**NOTE**: The text below should be modified if/when the development plan changes.  Also, links should also be added for ongoing or completed PRs.

# Development Plan

### Step 1: Create a new `collection-refactor` branch in dask/dask

- [x] **Link**: https://github.com/dask/dask/tree/collection-refactor

Although it may be a bit painful to keep this new branch in sync with `main`, I don't think it would be very wise for me (or others) to attempt a complete refactor within a single giant pull request.  I think we are much more likely to produce a good design if we attack this work in small **reviewable** steps.

The assumption here is that we will be able to run CI for PRs submitted to this branch.

## DataFrame Development

### Step 2: Adopt *compatibility* version of `CollectionOperation` in Dask-DataFrame (Initial PR)

- [x] **Link**: (withheld: the upstream fix is not part of the task)

- Add base `CollectionOperation` class
- Add `FrameOperation` and `CompatFrameOperation` classes to Dask-DataFrame
- Refactor `_Frame` (and subclasses) to reference a central `operation` attribute for `name`/`meta`/`divisions`/`dask`
    - Long-term goal will remove `dask` (or make `dask` synonymous with `operation`), but my preference is that we delay this change until after the entire Dask-DataFrame API has migrated away from the HLG/Layer design.

This PR will **not** introduce any `CollectionOperation` optimization or graph-materialization logic, but it will provide the foundation to implement these features.

### Step 3: Migrate Dask-DataFrame API to CollectionOperation design (Multiple PRs)

This step will not attempt to enable any new features or optimizations (like predicate pushdown), but will result in `CollectionOperation` coverage of the existing DataFrame `Layer` definitions:

- DataFrameIOLayer
- Blockwise
- ShuffleLayer/SimpleShuffleLayer
- BroadcastJoinLayer
- DataFrameTreeReduction

The completion of this step should also capture the existing HLG optimization pass (culling, fusion, column projection).

### Step 4: Add new `CollectionOperation` optimizations

Add predicate-pushdown optimization (and others - TBD).  Should be prioritized **after** general serialization/communication (steps 5-7).

## Array Development

### Step 2: Adopt *compatibility* version of `CollectionOperation` in Dask-Array

- Add `ArrayOperation` and `CompatArrayOperation` classes to Dask-Array
- Refactor `Array` to reference a central `operation` attribute for `name`/`meta`/`chunks`/`dask`

### Step 3: Migrate Dask-Array API to CollectionOperation design

Specifics TBD

### Step 4: Add new `CollectionOperation` optimizations

Specifics TBD.  Should be prioritized after general serialization/communication (steps 5-7).

## General Development

At this point, the DataFrame and Array APIs should be completely based on `CollectionOperation`. However, the APIs will still return a single-layer `HighLevelGraph` object when the `.dask` attribute is queried, and will still be using the HighLevelGraph API for graph communication and materialization. Therefore, most remaining work will be related

### Step 5: Change `.dask` queries to expect `HighLevelGraph` **or** `CollectionOperation` object

### Step 6: Create a new `collection-refactor` branch in dask/distributed

### Step 7: Support client-scheduler communication of a `CollectionOperation`

In order to replace the HLG/Layer infrastructure in Dask, we need to be able to send `CollectionOperation` objects to the scheduler (and use them to materialize the graph).

### Step 8: Merge changes into `main`

Once there is sufficient agreement (perhaps using a "Dask Design Proposal" in addition to a PR to `main`), these changes should be merged into the main branches of dask/dask dask/distributed.

### Step 9: Migrate Dask-Bag

### Step 10: Deprecate HighLevelGraph/Layer APIs

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
