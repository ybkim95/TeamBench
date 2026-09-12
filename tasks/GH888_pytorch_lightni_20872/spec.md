# GH888_pytorch_lightni_20872: bugfix: add support for `global_ordinal`, `local_ordinal`, `world_size` in xla — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/20852
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Description & Motivation

[PyTorch / XLA 2.7](https://github.com/pytorch/xla/releases/tag/v2.7.0) deprecates several APIs that Lightning still relies on. Could Lightning be updated for full XLA 2.7 compatibility?

### Pitch

_No response_

### Alternatives

_No response_

### Additional context

_No response_

cc [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi, [user]!

Would you consider separating these two topics into two issues making this one a bug, and not a feature? I implemented a bugfix for torch_xla 2.7, but did not add Native AMP

### Comment 2 ([user]):

> Hi, [user]!
> 
> Would you consider separating these two topics into two issues making this one a bug, and not a feature? I implemented a bugfix for torch_xla 2.7, but did not add Native AMP

Done, thanks for the fix!

### Comment 3 ([user]):

This issue has been automatically marked as stale because it hasn't had any recent activity. This issue will be closed in 7 days if no further activity occurs. Thank you for your contributions - the Lightning Team!

## PR Review Comments

**[user]** on `tests/tests_fabric/plugins/environments/test_xla.py`:

```suggestion


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch("lightning.fabric.accelerators.xla._XLA_GREATER_EQUAL_2_1", True)
@mock.patch("(lightning.fabric.plugins.environments.xla._XLA_GREATER_EQUAL_2_1", True)
def test_attributes_from_xla_greater_21_used(xla_available, monkeypatch):
    """Test XLA environment attributes when using XLA runtime >= 2.1."""
```

**[user]** on `src/lightning/fabric/plugins/environments/xla.py`:

Thanks for the update! Just to clarify — shouldn't this be `_XLA_GREATER_EQUAL_2_7` instead? Pls let me know if I’m missing something here.

**[user]** on `tests/tests_fabric/plugins/environments/test_xla.py`:

```suggestion
@mock.patch("lightning.fabric.plugins.environments.xla._XLA_GREATER_EQUAL_2_1", True)
```
my bad

**[user]** on `src/lightning/fabric/plugins/environments/xla.py`:

Thank you very much for the review and suggestions!

Yes, the old methods were deprecated in 2.7, but the new methods were introduced already in 2.1. You could see it here:  https://github.com/pytorch/xla/releases/tag/v2.1.0, MR#5011
1. `world_size`: (withheld: the upstream fix is not part of the task)files#diff-b5151ded18fbfdf1debacf597819bd88f7954b7f67f951fa8e131340805e5df5R129
2. `global_ordinal`: (withheld: the upstream fix is not part of the task)files#diff-b5151ded18fbfdf1debacf597819bd88f7954b7f67f951fa8e131340805e5df5R152
3. `local_ordinal`: (withheld: the upstream fix is not part of the task)files#diff-b5151ded18fbfdf1debacf597819bd88f7954b7f67f951fa8e131340805e5df5R162

I did not want to introduce more flags when the current ones should do the job, hence this usage of 2.1.

I also just now ran this on [Google Collab](https://colab.research.google.com/drive/13d6f3SCJBwOJaVn8UP-Nm9xWqCZLRGgk?usp=sharing) just to check if there were any differences in version 2.1, but it seems that the outputs are identical:

```python
import torch_xla
from torch_xla import runtime as xr
import torch_xla.core.xla_model as xm

print("TORCH XLA VERSION: ", torch_xla.__version__)

assert xr.world_size() == xm.xrt_world_size()
assert xr.local_ordinal() == xm.get_local_ordinal()
assert xr.global_ordinal() == xm.get_ordinal()
```

**[user]** on `src/lightning/fabric/plugins/environments/xla.py`:

Oh, got it! Thanks a lot for the clarification, [user]. 
I mistakenly assumed those methods got introduced in 2.7 — my bad.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
