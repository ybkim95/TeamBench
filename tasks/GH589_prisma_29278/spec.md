# GH589_prisma_29278: chore: migrate get-platform to vitest — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/prisma/prisma

## PR Description

This PR migrates get-platform tests from jest to vitest using vitest context.

<!-- This is an auto-generated comment: release notes by coderabbit.ai -->
## Summary by CodeRabbit

* **Tests**
  * Migrated tests from Jest to Vitest, updated imports, test harnesses and fixture/context setup while preserving assertions and platform-specific scopes.
* **Chores**
  * Removed legacy Jest configuration and testing dev-dependencies; switched package test script to use Vitest.
<!-- end of auto-generated comment: release notes by coderabbit.ai -->

## PR Review Comments

**[user]** on `packages/get-platform/src/__tests__/getPlatform.test.ts`:

_🧹 Nitpick_ | _🔵 Trivial_

**Well-structured test fixture for console mocking.**

The `test.extend` pattern is properly used to create reusable console mocks with automatic cleanup.

One minor linter improvement: Line 22 uses `forEach` with a callback that implicitly returns a value (from `mockRestore()`). Consider using `for...of` to silence the Biome warning.

<details>
<summary>♻️ Optional fix to address Biome warning</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]
</details>

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
const it = test.extend<{
  consoleMock: {
    log: MockInstance
    warn: MockInstance
    error: MockInstance
  }
}>({
  // eslint-disable-next-line no-empty-pattern
  consoleMock: async ({}, use) => {
    const mocks = {
      log: vi.spyOn(console, 'log').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {}),
    }
    await use(mocks)
    for (const m of Object.values(mocks)) {
      m.mockRestore()
    }
  },
})
```

</details>

<!-- suggestion_end -->

<details>
<summary>🧰 Tools</summary>

<details>
<summary>🪛 Biome (2.4.4)</summary>

[error] 15-15: Unexpected empty object pattern.

(lint/correctness/noEmptyPattern)

---

[error] 22-22: This callback passed to forEach() iterable method should not return a value.

(lint/suspicious/useIterableCallbackReturn)

</details>

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commit d70ff47

**[user]** on `packages/get-platform/src/__tests__/getSSLVersion.test.ts`:

_⚠️ Potential issue_ | _🟡 Minor_

<details>
<summary>🧩 Analysis chain</summary>

🏁 Script executed:

```shell
#!/bin/bash
# Verify the file structure and import path
echo "=== Directory structure around test file ==="
find packages/get-platform/src -type f -name "*.ts" | sort

echo ""
echo "=== Current imports in getSSLVersion.test.ts ==="
head -20 packages/get-platform/src/__tests__/getSSLVersion.test.ts

echo ""
echo "=== Check if getPlatform.ts exists at src level ==="
ls -la packages/get-platform/src/getPlatform.ts 2>/dev/null || echo "File not found at packages/get-platform/src/getPlatform.ts"

echo ""
echo "=== Check depth of __tests__ directory ==="
pwd
cd packages/get-platform && pwd
```

Repository: prisma/prisma

Length of output: 1671

---

</details>

**Simplify the import path in the test file.**

The import `'../../src/getPlatform'` unnecessarily traverses up two levels and back into `src`. From `src/__tests__/`, the correct relative path is `../getPlatform`.

<details>
<summary>🔧 Suggested fix</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]
</details>

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
import { computeLibSSLSpecificPaths, getArchFromUname, getSSLVersion } from '../getPlatform'
```

</details>

<!-- suggestion_end -->

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commit d70ff47

**[user]** on `packages/get-platform/src/__tests__/getPlatform.test.ts`:

maybe use `vitestConsoleContext` from `test-utils`

**[user]** on `packages/get-platform/src/__tests__/getPlatform.test.ts`:

I find that this is more vitest way. I'll make it re-usable in a next PR

**[user]** on `packages/get-platform/src/__tests__/getPlatform.test.ts`:

Let's replace `vitestConsoleContext` now

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
