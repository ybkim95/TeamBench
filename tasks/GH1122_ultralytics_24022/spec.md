# GH1122_ultralytics_24022: Use jsdelivr CDN assets URL for zidane.jpg reliability — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ultralytics/ultralytics

## PR Description

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
🛠️ This PR makes small but useful maintenance updates by cleaning up the COCO JSON training guide and hardening a Python prediction test with a fixed image URL.

### 📊 Key Changes
- 📘 Updated the **COCO JSON training guide** in `docs/en/guides/coco-json-training.md`:
  - Reordered a few imports for consistency.
  - Simplified category-mapping code formatting into single-line comprehensions.
  - Fixed YAML example indentation for the `names` field so it is clearer and more valid-looking.
  - Adjusted comment spacing and formatting to improve readability.
- ✅ Updated `tests/test_python.py`:
  - Replaced a variable-based asset URL with a direct CDN image URL for the online prediction test input.

### 🎯 Purpose & Impact
- 🧹 Improves **documentation clarity** for users building custom COCO JSON training workflows, making examples easier to copy and use correctly.
- 📚 Reduces confusion around the dataset YAML structure, especially for class name definitions.
- 🔒 Makes the Python test a bit more **stable and predictable** by using a fixed remote image source instead of relying on a shared URL variable.
- 👥 Overall impact is low-risk but helpful: no core model behavior changes, just better docs and slightly more robust testing.

## PR Review Comments

**[user]** on `tests/test_python.py`:

💡 **MEDIUM**: Using jsDelivr improves host availability, but `@main` keeps this test dependent on a mutable branch tip. If `zidane.jpg` is ever replaced, moved, or rewritten in `ultralytics/assets`, this test can start failing without any change in this repo. Pinning the CDN URL to a specific commit or immutable release tag would make the test deterministic.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
