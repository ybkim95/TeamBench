# GH903_transformers_33200: 🚨🚨🚨 [SuperPoint] Fix keypoint coordinate output and add post processing — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/huggingface/transformers/issues/33825
- Repo: https://github.com/huggingface/transformers

## Issue Description

Hi, I am trying the Keypoint detection but it shows that the `post_process_keypoint_detection` is not an attribute of `SuperPointImageProcessor`.
Here is the link of page.
https://huggingface.co/docs/transformers/en/tasks/keypoint_detection

## System info
- `transformers` version: 4.46.0.dev0
- Platform: Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.29
- Python version: 3.8.10
- Huggingface_hub version: 0.25.1
- Safetensors version: 0.4.5
- Accelerate version: 0.34.2
- Accelerate config:    not found
- PyTorch version (GPU?): 2.4.1+cu121 (True)
- Tensorflow version (GPU?): not installed (NA)
- Flax version (CPU?/GPU?/TPU?): not installed (NA)
- Jax version: not installed
- JaxLib version: not installed
- Using distributed or parallel set-up in script?: <fill in>
- Using GPU in script?: <fill in>
- GPU type: NVIDIA GeForce RTX 3060 Ti

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], thanks for opening an issue! Indeed, I see there is no such method for `SuperPointImageProcessor` in main. That's probably require not yet merged PR
 - (withheld: the upstream fix is not part of the task)

 cc [user]

### Comment 2 ([user]):

Thank you. I will waiting it merge to the main.

### Comment 3 ([user]):

You can also try to install from this PR

```
pip install git+(withheld: the upstream fix is not part of the task)
```

### Comment 4 ([user]):

> You can also try to install from this PR
> 
> ```
> pip install git+(withheld: the upstream fix is not part of the task)
> ```

Thank you, it is useful. 
I can try keypoint detection now.

## PR Review Comments

**[user]** on `src/transformers/models/superpoint/image_processing_superpoint.py`:

Could you add type hinting and a docstring for this please?

**[user]** on `src/transformers/models/superpoint/image_processing_superpoint.py`:

We should add this as a documented method for the model's doc page e.g. [like here ](https://github.com/huggingface/transformers/blob/c409cd81777fb27aadc043ed3d8339dbc020fb3b/docs/source/en/model_doc/deformable_detr.md?plain=1#L61)

**[user]** on `src/transformers/models/superpoint/image_processing_superpoint.py`:

We shouldn't be modifying inputs - this is a side-effect and can cause surprising to users

**[user]** on `src/transformers/models/superpoint/image_processing_superpoint.py`:

it's more pythonic to iterate over objects directly 

```suggestion
        for (image_mask, keypoints, scores, descriptors) in zip(outputs.mask, outputs.keypoints, outputs.scores, outputs.descriptors):
            indices = torch.nonzero(image_mask).squeeze(1)
            keypoints = keypoints[indices]
            scores = scores[indices]
            descriptors = descriptors[indices]
            results.append({"keypoints": keypoints, "scores": scores, "descriptors": descriptors})
```

**[user]** on `src/transformers/models/superpoint/modeling_superpoint.py`:

Technically a breaking change - but as this is more of a fix, I think it's OK

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
