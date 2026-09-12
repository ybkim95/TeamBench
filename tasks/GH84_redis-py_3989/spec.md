# GH84_redis-py_3989: Fix async ClusterPipeline missing nodes_manager and set_response_callback required by JSON module — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/redis/redis-py/issues/3936
- Repo: https://github.com/redis/redis-py

## Issue Description

redis-py version: 7.1.0

when use redis.asyncio.cluster.ClusterPipeline.json()

    def json(self, encoder=JSONEncoder(), decoder=JSONDecoder()) -> JSON:
        """Access the json namespace, providing support for redis json."""

        from .json import JSON

        jj = JSON(client=self, encoder=encoder, decoder=decoder)
        return jj

get_protocol_version function used when initializing JSON(...)
but redis.asyncio.cluster.ClusterPipeline dose not have attribute nodes_manager and set_response_callback

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], thank you for bringing this to our attention! We will have a look at it!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
