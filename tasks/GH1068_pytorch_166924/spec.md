# GH1068_pytorch_166924: [dynamo] fix keyerror in resume_execution,  fix store attr — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/166176
- Repo: https://github.com/pytorch/pytorch

## Issue Description

Originally reported in an internal model.

```python
import torch

def fn(x):
    torch._dynamo.graph_break()
    with torch.no_grad():
        with torch.no_grad():
            torch._dynamo.graph_break()
    return x + 1

inp = torch.ones(3)
opt_m = torch.compile(fn, backend="eager")
opt_m(inp)
```

gives error

```
...
  File "/data/users/williamwen/pytorch4/torch/_dynamo/symbolic_convert.py", line 1030, in handle_graph_break
    + self.create_call_resume_at(
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/symbolic_convert.py", line 2975, in create_call_resume_at
    resume_code, resume_name = cur_tx.create_resume(
                               ^^^^^^^^^^^^^^^^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/symbolic_convert.py", line 2879, in create_resume
    new_code: types.CodeType = ContinueExecutionCache.lookup(
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/resume_execution.py", line 307, in lookup
    cls.cache[code][key] = cls.generate(code, lineno, *key)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/resume_execution.py", line 336, in generate
    return cls.generate_based_on_original_code_object(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/resume_execution.py", line 683, in generate_based_on_original_code_object
    setup_fn_target_offsets = tuple(
                              ^^^^^^
  File "/data/users/williamwen/pytorch4/torch/_dynamo/resume_execution.py", line 684, in <genexpr>
    meta.block_target_offset_remap[new_offset][n]
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
torch._dynamo.exc.InternalTorchDynamoError: KeyError: 236

from user code:
   File "/data/users/williamwen/pytorch4/playground.py", line 18, in torch_dynamo_resume_in_fn_at_14
    y = gn(x)
```

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## PR Review Comments

**[user]** on `test/dynamo/test_repros.py`:

cc [user]  this doesn't exist on release/2.9... should we just remove this testcase?

**[user]** on `test/dynamo/test_repros.py`:

This test is coming from (withheld: the upstream fix is not part of the task) which we're not cherry picking? So we can probably just remove this test case.

**[user]** on `torch/_dynamo/resume_execution.py`:

cc [user]  this code is also causing a breakage since (target,) is not able to be unpacked.  Any thoughts on the right change to support this?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
