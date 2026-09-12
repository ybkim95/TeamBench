# GH1159_pytorch_166984: [Graph Partition] fix partition x memory plan issue — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytorch/pytorch

## PR Description

For `test_graph_partition_with_memory_plan_reuse`, before this PR, when using graph partition, it would error ([P1992728479](https://www.internalfb.com/phabricator/paste/view/P1992728479)):

```
def partition_0(args):
    ...
    del buf0
    return (buf3, buf4, buf5, buf2, primals_4, )

...

  File "/tmp/torchinductor_boyuan/ww/cwwc7ukfqscg2vy6ankby2fizdb377tvgyx3fwdgddrxe3g47jg6.py", line 132, in partition_0
    return (buf3, buf4, buf5, buf2, primals_4, )
                              ^^^^
NameError: name 'buf2' is not defined. Did you mean: 'buf0'?
```

When not using graph partition, it would work and give the following code ([P1992997521](https://www.internalfb.com/phabricator/paste/view/P1992997521)):

```
def call(self, args):
    ...
    buf2 = buf0; del buf0  # reuse
    ...
```

Note that the issue is buf0 is not reused for buf2 when using graph partition.

Why? Because the codegen runs `run_wrapper_ir_passes` and `memory_plan_reuse`, which pops tailing `MemoryPlanningLine` unless it is in graph output by checking `V.graph.get_output_names()`. However, for graph partition, we should check the output of the current partition instead of the graph before partition.





cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
