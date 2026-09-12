# GH1078_ultralytics_23546: Fix AutoBatch with multispectral images — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ultralytics/ultralytics

## PR Description

**MRE**
```
yolo train data=coco8-grayscale.yaml batch=-1
```

<!--
Thank you 🙏 for your contribution to [Ultralytics](https://www.ultralytics.com/) 🚀! Your effort in enhancing our repositories is greatly appreciated. To streamline the process and assist us in integrating your Pull Request (PR) effectively, please follow these steps:

1. Check for Existing Contributions: Before submitting, kindly explore existing PRs to ensure your contribution is unique and complementary.
2. Link Related Issues: If your PR addresses an open issue, please link it in your submission. This helps us better understand the context and impact of your contribution.
3. Elaborate Your Changes: Clearly articulate the purpose of your PR. Whether it's a bug fix or a new feature, a detailed description aids in a smoother integration process.
4. Ultralytics Contributor License Agreement (CLA): To uphold the quality and integrity of our project, we require all contributors to sign the CLA. Please confirm your agreement by commenting below:

    I have read the CLA Document and I sign the CLA

For more detailed guidance and best practices on contributing, refer to our ✅ [Contributing Guide](https://docs.ultralytics.com/help/contributing/). Your adherence to these guidelines ensures a faster and more effective review process.
-->

## 🛠️ PR Summary

<sub>Made with ❤️ by [Ultralytics Actions](https://www.ultralytics.com/actions)</sub>

### 🌟 Summary
Adds grayscale (non-3-channel) coverage to CUDA training tests and fixes AutoBatch to respect a model’s configured input channels 🧪⚡️

### 📊 Key Changes
- ✅ **Extended CUDA training tests** to run a quick training pass on `coco8-grayscale.yaml`, ensuring grayscale pipelines are exercised in CI.
- 🛠️ **Updated `autobatch()` to use the model’s configured input channels** (`model.yaml["channels"]`, defaulting to 3) instead of assuming RGB.
- 🔧 **AutoBatch profiling tensors now match real model inputs**, creating `torch.empty(b, ch, imgsz, imgsz)` rather than hardcoding `3` channels.

### 🎯 Purpose & Impact
- 📉 **Prevents AutoBatch mis-profiling and potential crashes** when training models/datasets with non-RGB inputs (e.g., grayscale medical/industrial imagery).
- 🎯 **Improves batch-size auto-selection accuracy** for custom channel configurations, leading to more reliable training setup on CUDA devices.
- 🧷 **Better regression protection**: CI will catch future changes that accidentally break grayscale or custom-channel training workflows.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
