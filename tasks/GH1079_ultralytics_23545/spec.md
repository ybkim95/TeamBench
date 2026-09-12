# GH1079_ultralytics_23545: Fix disk caching with multispectral images — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ultralytics/ultralytics

## PR Description

**MRE**

```
yolo train data=coco8-grayscale.yaml epochs=1 cache=disk
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
Fixes disk-cached image loading to respect grayscale (and other OpenCV read) modes, and updates a grayscale test to exercise disk caching 🧪💾

### 📊 Key Changes
- Updated disk caching to read images with the dataset’s configured OpenCV flag (`self.cv2_flag`) instead of always using the default read mode 🖼️➡️📦
- Adjusted the grayscale unit test to train with `cache="disk"` so this code path is tested directly ✅🧩

### 🎯 Purpose & Impact
- Ensures cached `.npy` images match the intended input format (e.g., grayscale) when using `cache="disk"` 🎛️🖤🤍
- Prevents subtle training/validation inconsistencies where cached images could differ from non-cached loading behavior 🔄🛡️
- Improves test coverage and reduces the chance of regressions for users training on grayscale or non-standard image loading configurations 🧪🚀

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
