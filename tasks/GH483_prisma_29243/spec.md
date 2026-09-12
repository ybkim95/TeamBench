# GH483_prisma_29243: fix: render tuple functions — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/prisma/prisma/issues/29215
- Repo: https://github.com/prisma/prisma

## Issue Description

### Bug description

After upgrading to Prisma 7.4.0, queries involving `in: [...]` with `case: 'insensitive'` appear to have changed, and likely have broken.

### Severity

⚠️ Major: Breaks core functionality (e.g., migrations fail)

### Reproduction

Run a query similar to below (`in: ['a', 'b']` with `case: 'insensitive'`)

### Expected vs. Actual Behavior

I'd expect the generated query not to change from a minor version upgrade

### Frequency

Consistently reproducible

### Does this occur in development or production?

Both development and production

### Is this a regression?

Yes, worked in 7.3.0 and broke in 7.4.0

### Workaround

Downgrading to 7.3.0 fixes it

### Prisma Schema & Queries

```prisma
model Attachment {
  id        Int      @id @default(autoincrement())
  createdAt DateTime @default(now())
  updatedAt DateTime @default(now()) @updatedAt

  name             String?
  fileName         String
  originalFileName String

  // where we're storing the file in S3
  fileUrl          String?

  companyId Int
  company   Company @relation(fields: [companyId], references: [id])

  @@index([fileName])
}
```
```ts
await prisma.attachment.findMany({
  where: {
    companyId: 34,
    fileName: {
      in: ['AbC.jpg', 'DEF.txt', 'gHi.png'],
      mode: 'insensitive',
    },
  },
  select: {
    id: true,
    fileName: true,
  },
});
```

### Prisma Config

```ts
import 'dotenv/config';
import { defineConfig, env } from 'prisma/config';

export default defineConfig({
  schema: 'prisma/schema.prisma',
  migrations: {
    path: 'prisma/migrations',
    seed: 'tsx prisma/seed.ts',
  },
  datasource: {
    url: env('DATABASE_URL'),
  },
});

```

### Logs & Debug Info

v7.3.0:
```
SELECT "public"."Attachment"."id", "public"."Attachment"."fileName" FROM "public"."Attachment" 
WHERE ("public"."Attachment"."companyId" = $1 
AND LOWER("public"."Attachment"."fileName") IN (LOWER($2),LOWER($3),LOWER($4))) 
OFFSET $5
```
v7.4.0:
```
SELECT "public"."Attachment"."id", "public"."Attachment"."fileName" FROM "public"."Attachment" 
WHERE ("public"."Attachment"."companyId" = $1 
AND LOWER("public"."Attachment"."fileName") IN ($2,$3,$4)) OFFSET $5
```

### Environment & Setup

- **OS:** macOS
- **Database:** PostgreSQL
- **Node.js version:** v22.21.1

### Prisma Version

```
Loaded Prisma config from prisma.config.ts.

Prisma schema loaded from prisma/schema.prisma.
prisma               : 7.4.0
@prisma/client       : 7.4.0
Operating System     : darwin
Architecture         : arm64
Node.js              : v22.21.1
TypeScript           : 5.9.3
Query Compiler       : enabled
PSL                  : @prisma/prisma-schema-wasm 7.4.0-20.ab56fe763f921d033a6c195e7ddeb3e255bdbb57
Schema Engine        : schema-engine-cli ab56fe763f921d033a6c195e7ddeb3e255bdbb57 (at node_modules/prisma/node_modules/@prisma/engines/schema-engine-darwin-arm64)
Default Engines Hash : ab56fe763f921d033a6c195e7ddeb3e255bdbb57
Studio               : 0.13.1
Preview Features     : postgresqlExtensions, typedSql
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

hello! [user] 
please check out the PR!

## PR Review Comments

**[user]** on `packages/client-engine-runtime/src/query-plan.ts`:

_⚠️ Potential issue_ | _🟠 Major_

<details>
<summary>🧩 Analysis chain</summary>

🏁 Script executed:

```shell
#!/bin/bash
# Search for parameterTuple references across the codebase
rg -n "parameterTuple" --type=ts -C 3
```

Repository: prisma/prisma

Length of output: 18706

---

🏁 Script executed:

```shell
#!/bin/bash
# Check the exact type definition for parameterTuple
sed -n '68,85p' packages/client-engine-runtime/src/query-plan.ts | cat -n

# Check renderQuery implementation for parameterTuple
sed -n '128,139p' packages/client-engine-runtime/src/interpreter/render-query.ts | cat -n
```

Repository: prisma/prisma

Length of output: 1093

---

🏁 Script executed:

```shell
#!/bin/bash
# Get the full context around parameterTuple type definition with more lines
sed -n '65,90p' packages/client-engine-runtime/src/query-plan.ts

# Check if fields might be optional (could be marked with ?)
rg -A 10 "type: 'parameterTuple'" packages/client-engine-runtime/src/query-plan.ts
```

Repository: prisma/prisma

Length of output: 894

---

🏁 Script executed:

```shell
#!/bin/bash
# Look at one complete test that uses parameterTuple without fields
sed -n '69,82p' packages/client-engine-runtime/src/interpreter/render-query.test.ts | cat -n

# Check if there's any type assertion or override
rg -B 5 -A 5 "type: 'parameterTuple'" packages/client-engine-runtime/src/interpreter/render-query.test.ts | head -40
```

Repository: prisma/prisma

Length of output: 1728

---

🏁 Script executed:

```shell
#!/bin/bash
# Check if tests have type assertions or any casting
rg -B 2 "type: 'parameterTuple'" packages/client-engine-runtime/src/interpreter/render-query.test.ts | grep -A 2 "as\|satisfies" || echo "No type overrides found"

# Check if there's conditional logic or defaults in render-query.ts for these fields
sed -n '120,160p' packages/client-engine-runtime/src/interpreter/render-query.ts | cat -n
```

Repository: prisma/prisma

Length of output: 1695

---

🏁 Script executed:

```shell
#!/bin/bash
# Check how fragments are created/deserialized from engine JSON
rg -B 5 -A 5 "Fragment\|fragment" packages/client-engine-runtime/src/query-plan.ts | head -80

# Look for where parameterTuple fragments are created in the codebase
rg "type: 'parameterTuple'" --type=ts -B 3 -A 3 | grep -v test | head -50
```

Repository: prisma/prisma

Length of output: 1285

---

🏁 Script executed:

```shell
#!/bin/bash
# I found two different Fragment types. Let me check the pairFragmentsWithParams function that converts them
sed -n '174,230p' packages/client-engine-runtime/src/interpreter/render-query.ts | cat -n
```

Repository: prisma/prisma

Length of output: 2370

---

🏁 Script executed:

```shell
#!/bin/bash
# Let me check the exact syntax more carefully - maybe there are ? marks I missed
cat packages/client-engine-runtime/src/query-plan.ts | sed -n '65,90p'

# Also check if there's a separate internal type vs external type
rg "Fragment" packages/client-engine-runtime/src/query-plan.ts | head -20
```

Repository: prisma/prisma

Length of output: 686

---

🏁 Script executed:

```shell
#!/bin/bash
# Let me check the raw file to see if there are ? marks that might be hidden in formatting
cat packages/client-engine-runtime/src/query-plan.ts | grep -A 10 "type: 'parameterTuple'"

# Also check the entire Fragment type definition comprehensively
rg -A 25 "^export type Fragment" packages/client-engine-runtime/src/query-plan.ts
```

Repository: prisma/prisma

Length of output: 874

---

🏁 Script executed:

```shell
#!/bin/bash
# Check if tests have `@ts-ignore` or type assertions
rg -B 5 "type: 'parameterTuple'" packages/client-engine-runtime/src/interpreter/render-query.test.ts | head -60

# Check if the test file imports Fragment type and uses it strictly
head -30 packages/client-engine-runtime/src/interpreter/render-query.test.ts
```

Repository: prisma/prisma

Length of output: 2668

---

🏁 Script executed:

```shell
#!/bin/bash
# The tests have satisfies on QueryPlanDbQuery but not on the fragments themselves
# Let me check if maybe the fields are optional but displayed without ?
python3 << 'EOF'
import re

with open('packages/client-engine-runtime/src/query-plan.ts', 'r') as f:
    content = f.read()
    
# Find Fragment type
fragment_match = re.search(r'export type Fragment = (.*?)(?=\nexport)', content, re.DOTALL)
if fragment_match:
    fragment_def = fragment_match.group(1)
    print("Fragment type definition:")
    print(fragment_def[:1500])
    print("\n---\n")
    
    # Check for optional markers
    if 'itemPrefix?' in fragment_def:
        print("FOUND: itemPrefix is optional (?)")
    else:
        print("NOT FOUND: itemPrefix appears to be required")
        
    if 'itemSeparator?' in fragment_def:
        print("FOUND: itemSeparator is optional (?)")
    else:
        print("NOT FOUND: itemSeparator appears to be required")
EOF
```

Repository: prisma/prisma

Length of output: 39

---

🏁 Script executed:

```shell
#!/bin/bash
# Check if the fields have ? in them - more direct approach
grep -n "itemPrefix\|itemSeparator\|itemSuffix" packages/client-engine-runtime/src/query-plan.ts

# Also let me look at the raw bytes to see if there's anything unusual
cat packages/client-engine-runtime/src/query-plan.ts | sed -n '70,75p' | od -c | head -20
```

Repository: prisma/prisma

Length of output: 288

---

🏁 Script executed:

```shell
#!/bin/bash
# The tests show parameterTuple without required fields but type shows them as required
# Let me verify if TypeScript is actually checking this

# First, check if there's a tsconfig
cat tsconfig.json 2>/dev/null | grep -A 5 "strict\|noImplicitAny" || echo "No tsconfig found"

# Check if tests compile at all with strict mode
ls -la packages/client-engine-runtime/tsconfig* 2>/dev/null || echo "No tsconfig in package"

# Let me look at the exact line 461 test that has parameterTuple
sed -n '460,465p' packages/client-engine-runtime/src/interpreter/render-query.test.ts | cat -n
```

Repository: prisma/prisma

Length of output: 478

---

🏁 Script executed:

```shell
#!/bin/bash
# Let me get the exact raw content without any processing
head -90 packages/client-engine-runtime/src/query-plan.ts | tail -30
```

Repository: prisma/prisma

Length of output: 700

---

🏁 Script executed:

```shell
#!/bin/bash
# Check if tests have `@ts-ignore` or `@ts-expect-error`
rg "@ts-ignore|@ts-expect-error" packages/client-engine-runtime/src/interpreter/render-query.test.ts

# Check the full context of one failing test to understand what's happening
sed -n '453,475p' packages/client-engine-runtime/src/interpreter/render-query.test.ts | cat -n
```

Repository: prisma/prisma

Length of output: 1035

---

🏁 Script executed:

```shell
#!/bin/bash
# I think I found it - there are TWO different fragment types
# Let me check what type the test actually passes to renderQuery

# Check the renderQuery function signature
sed -n '1,50p' packages/client-engine-runtime/src/interpreter/render-query.ts | cat -n

# Check what QueryPlanDbQuery requires
rg -A 20 "export type QueryPlanDbQuery" packages/client-engine-runtime/src/query-plan.ts
```

Repository: prisma/prisma

Length of output: 2681

---

</details>

**Type definition requires fields that test fixtures omit—runtime corruption risk exists now**

The `parameterTuple` type definition requires `itemPrefix`, `itemSeparator`, and `itemSuffix` as non-optional strings, but test fixtures (lines 73, 107, 141, 172, 203, 407, 464, 509 of render-query.test.ts) provide `{ type: 'parameterTuple' }` without these fields. The `renderFragment` implementation accesses them directly without null checks (render-query.ts:128-139), meaning any fragment missing these fields will produce:

- `` `${undefined}$1${undefined}` `` → `"undefined$1undefined"`  
- `.join(undefined)` → `","` (default behavior, losing intended separator)

Either the type definition should mark these fields as optional, or all fragment literals must include them. Add runtime validation with defaults (e.g., `itemPrefix ?? ''`) or update all fragment usages to match the type contract.

<!-- fingerprinting:phantom:poseidon:churro -->

<!-- This is an auto-generated reply by CodeRabbit -->

✅ Confirmed as addressed by [user]

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `packages/client/tests/functional/issues/29215-case-insensitive-in/tests.ts`:

_⚠️ Potential issue_ | _🔴 Critical_

<details>
<summary>🧩 Analysis chain</summary>

🌐 Web query:

`Prisma "mode: insensitive" in notIn support MySQL SQLite providers`

💡 Result:

Prisma’s `mode: "insensitive"` is **not supported** for the **MySQL** and **SQLite** providers—so you can’t use it with `notIn` (or any other string filter) on those providers.

- **MySQL**: Prisma does **not** generate the `mode` filter option for MySQL; case-(in)sensitivity is controlled by the **database/column collation** (MySQL is typically case-insensitive by default with `_ci` collations). [1]  
- **SQLite**: Prisma does **not** provide `mode` for SQLite. SQLite case-insensitive comparisons are limited (ASCII only) and require defining the column with `COLLATE NOCASE` if you want that behavior. [1]

**If you need `mode: "insensitive"` with `notIn`, you’ll need to use a provider that supports it (notably PostgreSQL or MongoDB).** [1]

Sources:  
[1] Prisma Docs – Case sensitivity / case-insensitive filtering support matrix and provider notes. ([docs.prisma.io](https://docs.prisma.io/docs/v6/orm/prisma-client/queries/case-sensitivity?utm_source=openai))

Citations:

- 1: https://docs.prisma.io/docs/v6/orm/prisma-client/queries/case-sensitivity?utm_source=openai

---

🏁 Script executed:

```shell
# First, let's examine the test file and its context
cat -n packages/client/tests/functional/issues/29215-case-insensitive-in/tests.ts | head -70
```

Repository: prisma/prisma

Length of output: 1983

---

🏁 Script executed:

```shell
# Check if there's a test configuration file that shows which providers are being tested
fd -e ts -e js -path "*29215*" -type f
```

Repository: prisma/prisma

Length of output: 225

---

🏁 Script executed:

```shell
# Search for provider-specific handling of mode: insensitive
rg -i "mode.*insensitive" --type ts --type js -A 2 -B 2 | head -100
```

Repository: prisma/prisma

Length of output: 9331

---

🏁 Script executed:

```shell
# Check the _matrix file for the test configuration
cat packages/client/tests/functional/issues/29215-case-insensitive-in/_matrix.ts
```

Repository: prisma/prisma

Length of output: 218

---

🏁 Script executed:

```shell
# Check how string-filters tests structure their provider-specific tests
head -50 packages/client/tests/functional/string-filters/tests.ts
```

Repository: prisma/prisma

Length of output: 1426

---

🏁 Script executed:

```shell
# Look for the test configuration to understand allProviders
fd -name "_matrix.ts" packages/client/tests/functional/ -exec head -30 {} \;
```

Repository: prisma/prisma

Length of output: 287

---

🏁 Script executed:

```shell
# Check if there's a _matrix.ts in string-filters
cat packages/client/tests/functional/string-filters/_matrix.ts
```

Repository: prisma/prisma

Length of output: 212

---

🏁 Script executed:

```shell
# Look at the complete mode: insensitive test section in string-filters
sed -n '/mode: insensitive/,/^  }\)/p' packages/client/tests/functional/string-filters/tests.ts | head -100
```

Repository: prisma/prisma

Length of output: 106

---

🏁 Script executed:

```shell
# Find and show the complete mode: insensitive describe block in string-filters
rg -A 60 "describeIf.*POSTGRESQL.*COCKROACHDB.*MONGODB" packages/client/tests/functional/string-filters/tests.ts | head -80
```

Repository: prisma/prisma

Length of output: 1697

---

🏁 Script executed:

```shell
# Also check if there are any provider checks or guards in the 29215 test file
cat packages/client/tests/functional/issues/29215-case-insensitive-in/tests.ts
```

Repository: prisma/prisma

Length of output: 1542

---

</details>

**Wrap these tests with a provider check — `mode: 'insensitive'` on `in`/`notIn` is not supported in MySQL and SQLite**

The test matrix runs against all providers. Since `mode: 'insensitive'` is not supported by MySQL and SQLite (per Prisma documentation), these tests will fail on those providers during CI. Guard the tests using `describeIf` like the `string-filters` tests do:

```typescript
describeIf(provider === Providers.POSTGRESQL || provider === Providers.COCKROACHDB || provider === Providers.MONGODB)(
  'case insensitive IN/NOT IN filters',
  () => {
    // existing tests
  }
)
```

<!-- fingerprinting:phantom:poseidon:churro -->

<!-- This is an auto-generated reply by CodeRabbit -->

✅ Addressed in commit b0fd4dd

**[user]** on `packages/client/tests/functional/issues/29215-case-insensitive-in/tests.ts`:

_⚠️ Potential issue_ | _🟠 Major_

**Non-deterministic result order makes this assertion flaky**

`findMany` at line 17 has no `orderBy` clause, but the assertion at lines 30–37 uses `toEqual([...])` which requires an exact ordered match. Without explicit ordering, databases (especially PostgreSQL) make no order guarantee, so `DEF.txt` may legitimately appear before `abc.jpg` and fail the test.

<details>
<summary>🐛 Proposed fix: add `orderBy` or switch to `arrayContaining`</summary>

[Code changes omitted — Planner should analyze the issue and guide the Executor]

Alternatively, keep the existing order but use `expect.arrayContaining` with a length check:

[Code changes omitted — Planner should analyze the issue and guide the Executor]
</details>

<!-- suggestion_start -->

<details>
<summary>📝 Committable suggestion</summary>

> ‼️ **IMPORTANT**
> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.

```suggestion
    const results = await prisma.attachment.findMany({
      where: {
        fileName: {
          in: ['AbC.jpg', 'DEF.txt'],
          mode: 'insensitive',
        },
      },
      select: {
        id: true,
        fileName: true,
      },
      orderBy: { fileName: 'asc' },
    })

    expect(results).toEqual([
      expect.objectContaining({
        fileName: 'DEF.txt',
      }),
      expect.objectContaining({
        fileName: 'abc.jpg',
      }),
    ])
```

```suggestion
    const results = await prisma.attachment.findMany({
      where: {
        fileName: {
          in: ['AbC.jpg', 'DEF.txt'],
          mode: 'insensitive',
        },
      },
      select: {
        id: true,
        fileName: true,
      },
    })

    expect(results).toHaveLength(2)
    expect(results).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ fileName: 'abc.jpg' }),
        expect.objectContaining({ fileName: 'DEF.txt' }),
      ]),
    )
```

</details>

<!-- suggestion_end -->

<!-- fingerprinting:phantom:poseidon:churro -->

<!-- This is an auto-generated reply by CodeRabbit -->

✅ Addressed in commit b0fd4dd

**[user]** on `packages/client-engine-runtime/src/query-plan.ts`:

updated

**[user]** on `packages/client/tests/functional/issues/29215-case-insensitive-in/tests.ts`:

updated

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
