# GH921_pytorch_lightni_21191: Fix missing reset when pruning with lottery ticket hypothesis — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/13643
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

## 🐛 Bug

<!-- A clear and concise description of the bug. -->
https://gist.github.com/SungFeng-Huang/57e1fce618d92b8f67350b31ed16ca5b
When using lottery ticket hypothesis, for each epoch, the unpruned parameters should be reset to its original values, while they actually didn't.
In my example, I print out the parameters after each forwarding. As it shows, the parameters at the start of the first training epoch is:
```
RunningStage.TRAINING
Parameter containing:
tensor([[ 0.1659,  0.0505,  0.1045, -0.1417, -0.1190,  0.1167, -0.0329,  0.0642,
          0.1052, -0.1013, -0.1337,  0.0421, -0.1219,  0.1590, -0.0412, -0.0092,
         -0.1699, -0.0617, -0.0170,  0.0743, -0.1400,  0.1014, -0.1466, -0.1046,
          0.0027,  0.0045, -0.0190, -0.0350,  0.1576, -0.1332, -0.0632,  0.0036],
        [ 0.0665, -0.1499, -0.1602, -0.0314, -0.0527,  0.0700, -0.0187,  0.1547,
         -0.1208,  0.0566, -0.1496, -0.0327, -0.0439, -0.1479,  0.1703,  0.0559,
          0.0953,  0.0130, -0.0722,  0.0475,  0.0694, -0.0046,  0.0985,  0.0927,
          0.0863,  0.0760, -0.0685, -0.0777, -0.0819,  0.0117, -0.1365, -0.1257]],
       requires_grad=True)
Parameter containing:
tensor([-0.1661,  0.0189], requires_grad=True)
```
while for the second training epoch, the parameters are only pruned without reset:
```
RunningStage.TRAINING
tensor([[ 0.3974,  0.2343,  0.3777,  0.0747, -0.2110, -0.0834, -0.1767,  0.2492,
          0.0000, -0.2491, -0.1482,  0.2866, -0.0000,  0.0000, -0.2813,  0.1499,
         -0.2980, -0.1384,  0.1447, -0.2121, -0.2717,  0.0000, -0.3288, -0.2336,
          0.2910,  0.0000, -0.0924,  0.1253,  0.0000, -0.1837, -0.1598, -0.1371],
        [ 0.2979,  0.0000,  0.1129,  0.1850, -0.1448, -0.1300, -0.1625,  0.3398,
         -0.1950, -0.0911, -0.1641,  0.2119,  0.0000, -0.2479, -0.0698,  0.2150,
         -0.0000, -0.0000,  0.0894, -0.2390, -0.0000, -0.0873, -0.0836, -0.0000,
          0.3746,  0.0949, -0.1418,  0.0826, -0.1735, -0.0000, -0.2332, -0.2664]],
       grad_fn=<MulBackward0>)
tensor([-0.3661, -0.1811], grad_fn=<MulBackward0>)
```

The problem happens mainly due to L275:
https://github.com/Lightning-AI/lightning/blob/07e7d6dc3ba1bbdae1a24da9d8d350096af68faa/src/pytorch_lightning/callbacks/pruning.py#L273-L279
assigning original values to `getattr(new, name)` is useless, since `getattr(new, name)` would be further overwritten by the pruning function's forward_pre_hooks:
https://github.com/pytorch/pytorch/blob/31142f57fc23edce291feaccf1670385e6239bbe/torch/nn/utils/prune.py#L23-L33

To fix this problem, L275 should become:
```python
dst = getattr(new, name + "_orig")
```

### To Reproduce

<!--
Please reproduce using the BoringModel!

You can use the following Colab link:
https://colab.research.google.com/github/Lightning-AI/lightning/blob/master/examples/pl_bug_report/bug_report_model.ipynb
IMPORTANT: has to be public.

or this simple template:
https://github.com/Lightning-AI/lightning/blob/master/examples/pl_bug_report/bug_report_model.py

If you could not reproduce using the BoringModel and still think there's a bug, please post here
but remember, bugs with code are fixed faster!
-->
https://gist.github.com/SungFeng-Huang/57e1fce618d92b8f67350b31ed16ca5b

### Expected behavior
The second (and later) epochs should start with parameters reset and pruned:
```
RunningStage.TRAINING
Parameter containing:
tensor([[ 0.1659,  0.0505,  0.1045, -0.1417, -0.1190,  0.1167, -0.0329,  0.0642,
          0.0000, -0.1013, -0.1337,  0.0421, -0.0000,  0.0000, -0.0412, -0.0092,
         -0.1699, -0.0617, -0.0170,  0.0743, -0.1400,  0.0000, -0.1466, -0.1046,
          0.0027,  0.0000, -0.0190, -0.0350,  0.0000, -0.1332, -0.0632,  0.0036],
        [ 0.0665, -0.0000, -0.1602, -0.0314, -0.0527,  0.0700, -0.0187,  0.1547,
         -0.1208,  0.0566, -0.1496, -0.0327, -0.0000, -0.1479,  0.1703,  0.0559,
          0.0000,  0.0000, -0.0722,  0.0475,  0.0000, -0.0046,  0.0985,  0.0000,
          0.0863,  0.0760, -0.0685, -0.0777, -0.0819,  0.0000, -0.1365, -0.1257]],
       grad_fn=<MulBackward0>)
Parameter containing:
tensor([-0.1661,  0.0189], grad_fn=<MulBackward0>)
```

<!-- FILL IN -->

### Environment

<!--
Please copy and paste the output from our environment collection script:
https://raw.githubusercontent.com/Lightning-AI/lightning/master/requirements/collect_env_details.py
(For security purposes, please check the contents of the script before running it)

You can get the script and run it with:
```bash
wget https://raw.githubusercontent.com/Lightning-AI/lightning/master/requirements/collect_env_details.py
python collect_env_details.py
```

You can also fill out the list below manually.
-->
* CUDA:
	- GPU:
		- Tesla T4
	- available:         True
	- version:           11.3
* Packages:
	- numpy:             1.21.6
	- pyTorch_debug:     False
	- pyTorch_version:   1.11.0+cu113
	- pytorch-lightning: 1.6.4
	- tqdm:              4.64.0
* System:
	- OS:                Linux
	- architecture:
		- 64bit
		- 
	- processor:         x86_64
	- python:            3.7.13
	- version:           #1 SMP Sun Apr 24 10:03:06 PDT 2022
<!--
- PyTorch Lightning Version (e.g., 1.5.0):
- PyTorch Version (e.g., 1.10):
- Python version (e.g., 3.9):
- OS (e.g., Linux):
- CUDA/cuDNN version:
- GPU models and configuration:
- How you installed PyTorch (`conda`, `pip`, source):
- If compiling from source, the output of `torch.__config__.show()`:
- Any other relevant information:
-->

### Additional context

<!-- Add any other context about the problem here. -->


cc [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Would you like to open a PR with the fix?

### Comment 2 ([user]):

I'm busy recently until the end of October. I would open a PR if the bug is still unfixed at that time.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
