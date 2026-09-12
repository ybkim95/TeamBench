# GH360_rain.orderbook_1936: Fix partial select token deserialization issue — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/rainlanguage/rain.orderbook/issues/1935
- Repo: https://github.com/rainlanguage/rain.orderbook

## PR Description

<!-- Thanks for your Pull Request, please read the contributing guidelines before submitting. -->

## Motivation

<!--
Explain the context and why you're making that change. What is the problem
you're trying to solve? In some cases there is not a problem and this can be
thought of as being the motivation for your change.
-->

See issue: https://github.com/rainlanguage/rain.orderbook/issues/1935

There was a problem with deserializing partially selected tokens. This PR fixes that.

## Solution

<!--
Summarize the solution and provide any necessary context needed to understand
the code change.
-->

- Populate context with select tokens data before parsing order map in yaml file during deserialization

## Checks
<!-- It's important you've done these, or your PR will not be considered for review -->
By submitting this for review, I'm confirming I've done the following:
- [x] made this PR as small as possible
- [x] unit-tested any new functionality
- [x] linked any relevant issues or PRs
- [ ] included screenshots (if this involves a front-end change)

fix https://github.com/rainlanguage/rain.orderbook/issues/1935

<!-- This is an auto-generated comment: release notes by coderabbit.ai -->
## Summary by CodeRabbit

- **New Features**
  - Improved order retrieval by supporting deployment-specific context and GUI select tokens.

- **Chores**
  - Updated test configuration to exclude mock files from test runs.
  - Adjusted module mocking to only apply during testing, ensuring mocks are limited to the test environment.
<!-- end of auto-generated comment: release notes by coderabbit.ai -->

## PR Review Comments

**[user]** on `crates/settings/src/yaml/dotrain.rs`:

_🧹 Nitpick (assertive)_

**Add Rustdoc, avoid needless `clone()` churn**

The new `current_deployment` parameter changes the public API, but the function signature and its behaviour are undocumented.  Please add a short rust-doc explaining:

* the semantics of passing `None` vs `Some(&deployment_key)`
* why select-token expansion must happen here rather than in the caller

While you are here, you can avoid the extra allocation of `Vec<String>` by mapping directly into an iterator:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

That keeps the code allocation-free and simpler.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In crates/settings/src/yaml/dotrain.rs around lines 92 to 116, add a Rustdoc
comment to the get_order function explaining the meaning of passing None versus
Some(&deployment_key) for current_deployment and why select-token expansion is
done inside this function rather than by the caller. Also, refactor the code
that adds select tokens to context by replacing the collect::<Vec<_>>() call
with a direct iterator mapping to avoid unnecessary allocation and cloning,
making the code simpler and more efficient.
```

</details>

<!-- This is an auto-generated reply by CodeRabbit -->

**[user]** on `packages/ui-components/vite.config.ts`:

_⚠️ Potential issue_

**`import.meta.vitest` is always truthy – unconditional mocks in production**

`define: { 'import.meta.vitest': 'undefined' }` replaces the expression with the *string* `"undefined"`.
Because non-empty strings are truthy, the check

```ts
if (import.meta.vitest) { … }
```

inside your mocks now evaluates to `true` in *all* build modes, leading
to `vi.mock` being executed in production, where `vi` is not defined
→ runtime crash.

Fix by injecting the real `undefined`, not the string:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

or drop the define completely – Vitest already sets the property during
tests.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In packages/ui-components/vite.config.ts around lines 21 to 23, the define
configuration incorrectly sets 'import.meta.vitest' to the string "undefined",
causing it to always be truthy and triggering mocks in production. Fix this by
either removing the define setting entirely, as Vitest sets it during tests, or
by setting 'import.meta.vitest' to the actual undefined value without quotes to
ensure the condition correctly evaluates to false outside test environments.
```

</details>

<!-- This is an auto-generated reply by CodeRabbit -->

**[user]** on `packages/ui-components/src/lib/__mocks__/stores.ts`:

_⚠️ Potential issue_

**Mock guard still triggers outside tests & may reference `vi` in prod**

Because the build step replaces `import.meta.vitest` with the string
`"undefined"`, the guard below is permanently truthy and `vi` becomes
an undefined global in non-test builds.

```ts
if (import.meta.vitest) {
  vi.mock(…)
}
```

Patch:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

This keeps production bundles free of testing code and prevents a
ReferenceError.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In packages/ui-components/src/lib/__mocks__/stores.ts around lines 9 to 15, the
current guard using if (import.meta.vitest) incorrectly triggers in production
because import.meta.vitest is replaced with the string "undefined", causing vi
to be undefined and leading to errors. To fix this, change the guard to
explicitly check if import.meta.vitest is truthy and of the correct type before
calling vi.mock, ensuring the mocking code only runs in test environments and is
excluded from production bundles.
```

</details>

<!-- This is an auto-generated reply by CodeRabbit -->

**[user]** on `crates/js_api/src/gui/state_management.rs`:

_🧹 Nitpick (assertive)_

**Minor efficiency: avoid `get_order` in a tight loop**

`get_order` reparses YAML on every call.  
Inside the vault-id loop you already know `order_key` and
`selected_deployment`; fetch the order once and mutate it instead of
re-parsing for every `(is_input, index)` pair.

Not critical, but reduces CPU for large orders.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In crates/js_api/src/gui/state_management.rs around lines 238 to 239, the code
calls get_order repeatedly inside a loop, causing YAML to be reparsed each time.
To improve efficiency, fetch the order once before the loop using order_key and
selected_deployment, then mutate the cached order within the loop for each
(is_input, index) pair instead of calling get_order repeatedly.
```

</details>

<!-- This is an auto-generated reply by CodeRabbit -->

**[user]** on `crates/js_api/src/gui/order_operations.rs`:

_🧹 Nitpick (assertive)_

**Single YAML parse would suffice**

`populate_vault_ids` now calls

```rust
self.dotrain_order.dotrain_yaml().get_order(...)?   // parses YAML
    .populate_vault_ids()?;
```

Every invocation fully reparses the order.  Consider caching the
`OrderCfg` for the duration of `populate_vault_ids` (or storing the
mutated order back into the deployment) to avoid redundant work.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In crates/js_api/src/gui/order_operations.rs around lines 282 to 288, the method
populate_vault_ids reparses the YAML order multiple times during its execution,
causing redundant work. To fix this, parse the YAML once at the start of
populate_vault_ids, cache the resulting OrderCfg object in a local variable, and
then perform all necessary operations on this cached object. Optionally, store
the mutated order back into the deployment if needed to maintain state
consistency.
```

</details>

<!-- This is an auto-generated reply by CodeRabbit -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
