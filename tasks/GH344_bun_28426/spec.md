# GH344_bun_28426: Fix assertion crash when hostname/unix coerces to empty string — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/oven-sh/bun

## PR Description

`Bun.listen()` and `Bun.connect()` crash with an internal assertion failure when the `hostname` (or `unix`) option is a truthy value whose `toString()` returns an empty string — for example, an empty array `[]` or `new String("")`.

**Root cause:** The bindgen `IDLLooseNullable` conversion checks the truthiness of the original JS value (objects are truthy), then calls `toString()` to get a `WTF::String`. When `toString()` produces `""`, the result is a non-null `WTFStringImpl*` (the static empty string singleton) with `length == 0`. The Zig code then hits `assertf(hostname.length() > 0, "truthy bindgen string should not be empty")`.

**Fix:** Replace the assertions with proper validation that returns a `TypeError` when the coerced string is empty.

**Repro:**
```js
Bun.listen({ hostname: [], port: 0, socket: { data(){}, open(){}, close(){} } });
// Before: panic — "Internal assertion failure: truthy bindgen string should not be empty"
// After:  TypeError — Expected a non-empty "hostname"
```

---

🔍 **Verified by robobun**: Zig fix at Handlers.zig lines 303 and 315 replaces `bun.assertf` panics with `throwInvalidArguments` error returns — matches the existing pattern in the same function (line 319). Return type `bun.JSError!SocketConfig` supports this. On main, these lines have `bun.assertf(...)` which crashes. Regression test at socket.test.ts lines 786-803 exercises the exact crash path with `[]` and `new String("")` as hostname — both are truthy but `toString()` returns `""`. Would crash on main; does not exist on main. Unix test correctly asserts the bindgen-layer rejection message. Lint JavaScript passed. Buildkite build #41227 in progress. No TODO/FIXME/HACK in diff. CodeRabbit actionable comment addressed. Claude Code Review LGTM.

## PR Review Comments

**[user]** on `test/js/bun/net/socket.test.ts`:

_🧹 Nitpick_ | _🔵 Trivial_

**Assert the specific error message for consistency.**

The unix test should verify the specific error message like the hostname test does. This ensures the correct validation path is exercised.

<details>
<summary>Proposed fix</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]

</details>

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
Verify each finding against the current code and only fix it if needed.

In `@test/js/bun/net/socket.test.ts` around lines 797 - 801, Update the test
"should throw on empty unix path from truthy non-string value" to assert the
exact error message instead of a generic toThrow(); specifically change the two
expectations around Bun.listen({ unix: [] as any, socket }) and Bun.connect({
unix: [] as any, socket }) to use the same toThrowError(...) string used by the
hostname test so the validation path is verified; keep the test name and socket
stub the same and only replace the matcher on those two assertions.
```

</details>

<!-- fingerprinting:phantom:poseidon:ocelot -->

<!-- This is an auto-generated comment by CodeRabbit -->

✅ Addressed in commit 7459aec

**[user]** on `test/js/bun/net/socket.test.ts`:

🟡 The unix path test is weaker than its hostname counterpart: it uses generic .toThrow() without asserting the specific error message, and only tests [] while the hostname test covers both [] and new String(""). Update the unix test to assert Expected a non-empty "unix" path and loop over both inputs to match the hostname test rigor.

<details>
<summary>Extended reasoning...</summary>

## Analysis

The PR adds two regression tests: one for hostname and one for unix path validation. The hostname test (lines 786-795) is thorough: it loops over [[], new String("")] and asserts the exact error message 'Expected a non-empty "hostname"' for both Bun.listen and Bun.connect. The unix test (lines 797-801) is weaker on two dimensions.

## Bug 1: Missing specific error message assertion

The unix test calls .toThrow() with no argument, while the Zig fix at Handlers.zig:303 emits the specific message "Expected a non-empty "unix" path" via throwInvalidArguments. A bare .toThrow() would pass even if a completely different error were thrown -- for example, an OS-level error because the empty path was passed through to the socket layer, or a TypeError from a different validation branch. This reduces the diagnostic value of the test: a future regression where the wrong error is thrown would go undetected.

**Step-by-step proof:**
1. Suppose someone accidentally removes the new if (unix.length() == 0) check but introduces a different error path that still throws for [] (e.g., a length check somewhere else with a different message).
2. The unix test still passes because .toThrow() matches any thrown value.
3. The hostname test would catch the equivalent regression because it asserts the exact message.

## Bug 2: Missing new String("") test case

The hostname test explicitly iterates over both [] and new String("") because they exercise different paths through the IDLLooseNullable bindgen conversion: an empty array coerces via toString() to "", while new String("") is a String object that yields the WTFString empty singleton more directly. The unix test omits new String("") entirely. If a future change accidentally broke the new String("") path specifically for unix (while keeping the array path working), the unix test would not catch it.

## Why existing code does not prevent this

The Zig validation (if (unix.length() == 0)) is symmetric for both inputs -- both produce a zero-length WTFString and hit the same check. The production fix is correct. The gap is purely in test coverage and assertion strength.

## Fix

Change the unix test to mirror the hostname test:

CodeRabbitAI flagged the missing error message assertion as a nitpick in an inline comment on line 801, confirming this is a recognized issue.

</details>

**[user]** on `src/bun.js/api/bun/socket/Handlers.zig`:

🟣 Pre-existing issue: if unix is set to exactly "file://", "unix://", or "sock://" (length 7), the new length() == 0 guard passes, but stripping the 7-char prefix via slice[7..] yields an empty string that gets used as the socket path, causing cryptic OS-level errors (ENOENT/EINVAL) instead of a clean TypeError. A post-strip length check after the prefix-stripping block would catch this edge case.

<details>
<summary>Extended reasoning...</summary>

The PR adds a length() == 0 guard at line 303 to replace the old assertf. This correctly handles the case where a truthy JS value (like []) coerces to an empty string. However, there is an adjacent gap: if the unix value is exactly "file://", "unix://", or "sock://" (all exactly 7 characters), it passes the guard since 7 != 0.

After passing the guard, unix.toUTF8() produces the string "file://". The hasPrefixComptime check at line 306 matches, and slice[7..] is computed. Since the input is exactly 7 characters long, slice[7..] yields a zero-length slice. This empty string is then duped and stored as result.hostname_or_unix, which gets passed to the OS as the unix domain socket path.

The OS receives an empty path and returns a cryptic error (ENOENT or EINVAL) rather than Bun throwing a clean TypeError with a descriptive message.

Step-by-step proof:
1. User calls Bun.listen({ unix: "file://", socket: { data(){}, open(){}, close(){} } })
2. unix.length() returns 7, so the length == 0 check is false - no error thrown
3. unix.toUTF8() stores "file://" in result.hostname_or_unix
4. slice = "file://" (7 bytes)
5. hasPrefixComptime(slice, "file://") returns true
6. slice[7..] = "" (empty string)
7. bun.default_allocator.dupe(u8, "") succeeds, producing an empty allocation
8. result.hostname_or_unix is set to "" and passed to the socket layer
9. The OS rejects the empty path with ENOENT/EINVAL

This is a pre-existing bug - the old assertf(unix.length() > 0) also would not have caught this since the raw input length is 7, not 0. The PR is an improvement (replacing the crash with a proper error) but misses this edge case. The same applies to "unix://" and "sock://" inputs.

Fix: After the prefix-stripping block (around line 312), add a check: if (result.hostname_or_unix.slice().len == 0) return global.throwInvalidArguments("Expected a non-empty unix path", .{});

</details>

**[user]** on `test/js/bun/net/socket.test.ts`:

Already addressed in 7459aec — the test now asserts the specific error message. Note that the suggestion to use `'Expected a non-empty "unix" path'` would be incorrect: `unix` uses a strict string type in bindgen, so `[]` is rejected with `"SocketOptions.unix must be a string"` before reaching the empty-string check. The test asserts this actual message.

**[user]** on `src/bun.js/api/bun/socket/Handlers.zig`:

Good observation about `"file://"` stripping to empty — that is a pre-existing issue outside the scope of this crash fix. The OS would return an error (ENOENT/EINVAL) rather than crash, so it's less critical but worth a follow-up.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
