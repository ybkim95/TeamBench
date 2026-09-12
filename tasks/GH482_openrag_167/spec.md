# GH482_openrag_167: Fix/filename — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/linagora/openrag

## PR Description

This PR adds a `sanitize_filename` utility function to clean and normalize uploaded filenames, preventing issues from special characters and ensuring consistent file naming. 

**Changes:**
- New `sanitize_filename` function removes special characters, normalizes separators to underscores, and handles edge cases
- unittests added

<!-- This is an auto-generated comment: release notes by coderabbit.ai -->

## Summary by CodeRabbit

* **New Features**
  * Implemented automatic filename sanitization for uploaded files, normalizing and removing disallowed characters to improve file handling robustness.

* **Tests**
  * Added comprehensive test coverage for filename sanitization, including edge cases with special characters and multiple spaces.

<sub>✏️ Tip: You can customize this high-level summary in your review settings.</sub>

<!-- end of auto-generated comment: release notes by coderabbit.ai -->

## PR Review Comments

**[user]** on `openrag/components/files.py`:

you can use Path directly, it will be more robust:
```
path = Path(filename)
name = p.stem
ext = p.suffix
```

**[user]** on `openrag/components/files.py`:

Is is a problem to have multiple underscore? I know I have files with them, this case seems legit to me

**[user]** on `openrag/components/files.py`:

Is hyphens really problematic ? Lot of files have it

**[user]** on `openrag/components/test_files.py`:

Could you add a test with `.` in file name? :pray:

**[user]** on `openrag/components/files.py`:

Yep. It's better

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
