# GH351_prisma_29307: fix(adapter-pg): handle both quoted/unquoted column names in ColumnNotFound error — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/prisma/prisma

## PR Description

This pull request improves the handling and testing of PostgreSQL "ColumnNotFound" errors in the adapter. The main focus is on correctly extracting column names from error messages, regardless of whether the column name is quoted, and ensuring the tests cover both scenarios.

We were getting "The column `(not available)` does not exist in the current database" error all the time, the sql was trying to get qualified name (e.g. schema.table_name) which generated postgres error message without quotes:
`column table.column does not exist` vs `column "column" does not exist`.
Our setup included:
- multi-schema DB
- custom @@map() fields.
- Postgres v18.3

Error handling improvements:

* Updated the `mapDriverError` function in `errors.ts` to strip quotes from column names when parsing "ColumnNotFound" (42703) errors, ensuring consistent extraction of the column name.

Testing enhancements:

* Added a new test case for handling unquoted column names and clarified the description of the existing test for quoted column names in `errors.test.ts`, ensuring both cases are covered for "ColumnNotFound" errors.

<!-- This is an auto-generated comment: release notes by coderabbit.ai -->
## Summary by CodeRabbit

* **Bug Fixes**
  * Improved detection and normalization of PostgreSQL "column not found" errors so column names are identified correctly for unquoted, quoted, qualified, spaced, and escaped-quote formats, providing clearer, consistent error details.

* **Tests**
  * Added comprehensive tests covering many column-name formats to ensure accurate detection and unchanged original error messaging.
<!-- end of auto-generated comment: release notes by coderabbit.ai -->

## PR Review Comments

**[user]** on `packages/adapter-pg/src/errors.ts`:

`replaceAll('"', '')` removes *all* double quotes in the identifier token. That can incorrectly change valid Postgres identifiers that contain escaped quotes (e.g. column name `foo"bar` is rendered as `"foo""bar"` in messages; removing all quotes would lose the embedded quote). Consider parsing the identifier more precisely: split on `.` into parts, strip only wrapping quotes per part, and unescape doubled quotes (`""` -> `"`).

**[user]** on `packages/adapter-pg/src/__tests__/errors.test.ts`:

The new tests cover quoted vs unquoted single identifiers, but the motivating production case mentioned in the PR description is a *qualified* name (e.g. `table.column` / `"table"."column"`). Adding an assertion for a dotted identifier would better lock in the intended behavior and prevent regressions where only the first segment is parsed.

**[user]** on `packages/adapter-pg/src/errors.ts`:

_⚠️ Potential issue_ | _🟡 Minor_

<details>
<summary>🧩 Analysis chain</summary>

🏁 Script executed:

```shell
find . -type f -name "errors.ts" | head -20
```

Repository: prisma/prisma

Length of output: 490

---

🏁 Script executed:

```shell
git ls-files | grep -E "packages/adapter-pg/src" | head -20
```

Repository: prisma/prisma

Length of output: 375

---

🏁 Script executed:

```shell
cat -n packages/adapter-pg/src/errors.ts | head -150
```

Repository: prisma/prisma

Length of output: 4937

---

🏁 Script executed:

```shell
# Run the verification script from the review
python - <<'PY'
samples = [
    'column foo does not exist',
    'column "foo" does not exist',
    'column "first name" does not exist',
    'column "a""b" does not exist',
]

for msg in samples:
    parts = msg.split(' ')
    token = parts[1] if len(parts) > 1 else None
    parsed = token.replace('"', '') if token is not None else None
    print(f'{msg!r} -> {parsed!r}')
PY
```

Repository: prisma/prisma

Length of output: 219

---

🏁 Script executed:

```shell
# Search for test files related to this error handler
find . -type f -path "*adapter-pg*" -name "*test*" -o -path "*adapter-pg*" -name "*spec*" | grep -i error
```

Repository: prisma/prisma

Length of output: 107

---

🏁 Script executed:

```shell
cat -n packages/adapter-pg/src/__tests__/errors.test.ts
```

Repository: prisma/prisma

Length of output: 9190

---

🏁 Script executed:

```shell
# Check if there are existing tests for the 42703 error code
grep -n "42703\|ColumnNotFound" packages/adapter-pg/src/__tests__/errors.test.ts
```

Repository: prisma/prisma

Length of output: 484

---

🏁 Script executed:

```shell
# Let's verify the PostgreSQL error message format more thoroughly
# by checking if there's any documentation or comments in the code
grep -r "42703\|ColumnNotFound" packages/adapter-pg/src --include="*.ts" -A 3 -B 3
```

Repository: prisma/prisma

Length of output: 2321

---

🏁 Script executed:

```shell
# Test the suggested regex-based approach to confirm it would work correctly
python3 - <<'PY'
import re

def parse_column_current(msg):
    """Current implementation"""
    return msg.split(' ').at(1) if hasattr(msg.split(' '), 'at') else msg.split(' ')[1] if len(msg.split(' ')) > 1 else None

def parse_column_current_js(msg):
    """Current implementation - JavaScript style"""
    parts = msg.split(' ')
    token = parts[1] if len(parts) > 1 else None
    return token.replace('"', '') if token is not None else None

def parse_column_suggested(msg):
    """Suggested implementation"""
    match = re.match(r'^column (.+) does not exist$', msg)
    if not match:
        return None
    raw_column = match.group(1)
    
    if raw_column.startswith('"') and raw_column.endswith('"'):
        # Remove leading/trailing quotes and unescape doubled quotes
        unquoted = raw_column[1:-1]  # Remove outer quotes
        unescaped = unquoted.replace('""', '"')
        return unescaped
    else:
        return raw_column

test_cases = [
    'column foo does not exist',
    'column "foo" does not exist',
    'column "first name" does not exist',
    'column "a""b" does not exist',
    'column "a with spaces and ""quotes"" inside" does not exist',
]

print("Testing parsing approaches:")
print("-" * 80)
for msg in test_cases:
    current = parse_column_current_js(msg)
    suggested = parse_column_suggested(msg)
    match = "✓" if current == suggested else "✗ DIFFERENT"
    print(f"Input: {msg!r}")
    print(f"  Current:  {current!r}")
    print(f"  Suggested: {suggested!r}")
    print(f"  Status: {match}")
    print()
PY
```

Repository: prisma/prisma

Length of output: 704

---

</details>

**Column name parsing fails for quoted identifiers with spaces or escaped quotes.**

Line 142 only extracts the first word after "column". PostgreSQL quoted identifiers can contain spaces (`column "first name" does not exist` parses as `first`) and escaped quotes (`column "a""b" does not exist` parses as `ab` instead of `a"b`). Capture the full substring between `column ` and ` does not exist`, then strip only wrapper quotes and unescape doubled quotes.

<details>
<summary>Suggested fix</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]
</details>

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
    case '42703':
      const rawColumn = error.message.match(/^column (.+) does not exist$/)?.at(1)
      return {
        kind: 'ColumnNotFound',
        column: rawColumn?.startsWith('"')
          ? rawColumn.replaceAll('""', '"').replace(/^"|"$/g, '')
          : rawColumn,
```

</details>

<!-- suggestion_end -->

<!-- fingerprinting:phantom:poseidon:grasshopper -->

<!-- This is an auto-generated reply by CodeRabbit -->

✅ Addressed in commit 39f63c3

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `packages/adapter-pg/src/errors.ts`:

I think this coderabbit comment needs attention

**[user]** on `packages/adapter-pg/src/errors.ts`:

[user], the concern is valid — both the old and the new implementation only split on whitespace and take the second word, so any column name containing spaces (e.g. `"first name"`) or an escaped quote (e.g. `"a""b"`) will be silently truncated or mis-parsed.

Here's my plan to properly fix this:

- Fix the `42703` case in `errors.ts` to use a regex that captures the full raw column token, then strip wrapper quotes and unescape `""` → `"`
- Extend `errors.test.ts` with the two additional edge-case tests (spaces in name, escaped quote in name)

<!-- <requirement>
[requirement fix_column_parsing_1/2]
Update the `42703` (ColumnNotFound) case in `packages/adapter-pg/src/errors.ts` to correctly parse quoted column names that may contain spaces or escaped double-quotes.

Replace:
```ts
case '42703':
  return {
    kind: 'ColumnNotFound',
    column: error.message.split(' ').at(1)?.replaceAll('"', ''),
  }
```

With:
```ts
case '42703': {
  const rawColumn = error.message.match(/^column (.+) does not exist$/)?.at(1)
  return {
    kind: 'ColumnNotFound',
    column: rawColumn?.startsWith('"')
      ? rawColumn.replaceAll('""', '"').replace(/^"|"$/g, '')
      : rawColumn,
  }
}
```

This correctly handles:
- `column foo does not exist` → `"foo"`
- `column "foo" does not exist` → `"foo"`
- `column "first name" does not exist` → `"first name"` (was broken: returned `"first"`)
- `column "a""b" does not exist` → `"a\"b"` (was broken: returned `"ab"`)
</requirement> -->

<!-- <requirement>
[requirement fix_column_parsing_2/2]
Add two new test cases to `packages/adapter-pg/src/__tests__/errors.test.ts` for the 42703 error code to cover the edge cases fixed above.

Append the following tests alongside the existing `42703` tests:

```ts
it('should handle ColumnNotFound error (42703) with a column name containing spaces', () => {
  const error = new DatabaseError('column "first name" does not exist', 100, 'error')
  error.code = '42703'
  error.severity = 'ERROR'

  expect(convertDriverError(error)).toEqual({
    kind: 'ColumnNotFound',
    column: 'first name',
    originalCode: '42703',
    originalMessage: 'column "first name" does not exist',
  })
})

it('should handle ColumnNotFound error (42703) with a column name containing an escaped quote', () => {
  const error = new DatabaseError('column "a""b" does not exist', 100, 'error')
  error.code = '42703'
  error.severity = 'ERROR'

  expect(convertDriverError(error)).toEqual({
    kind: 'ColumnNotFound',
    column: 'a"b',
    originalCode: '42703',
    originalMessage: 'column "a""b" does not exist',
  })
})
```
</requirement> -->

---

<details>
<summary>🧠 Learnings used</summary>

```
Learnt from: jacek-prisma
Repo: prisma/prisma PR: 28992
File: packages/client/tests/functional/issues/28591-mapped-enums/test.ts:9-18
Timestamp: 2026-01-05T16:15:18.374Z
Learning: Prisma: After the TML-1663 fix, when using enums with map directives, only the mapped (lowercase) input values are accepted. For example, enum SuggestionStatus { PENDING map("pending") } will accept 'pending' but not 'PENDING'. This is a behavioral change from before. Update tests and usage accordingly to validate inputs against mapped values, and ensure any input normalization or validation relies on the mapped string rather than the enum name.
```

---

```
Learnt from: Felipeness
Repo: prisma/prisma PR: 29317
File: packages/cli/src/utils/checkpoint.ts:10-10
Timestamp: 2026-03-07T22:54:09.604Z
Learning: When reviewing TypeScript code, do not confl ate the strings 'prisma-client', 'prisma-client-js', and 'prisma-client-ts'. Treat each as a separate generator provider; if a provider string is extracted into a constant, create distinct constants for each literal and avoid aliasing. This applies to any hardcoded provider string literals in the codebase; ensure comparisons are explicit and maintainable.
```

</details>

---

💡 Use [user] plan to create a plan for code changes

<!-- This is an auto-generated reply by CodeRabbit -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
