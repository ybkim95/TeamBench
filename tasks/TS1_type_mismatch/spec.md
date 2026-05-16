# TS1_type_mismatch: TypeScript API Type Errors

## Goal

Fix all TypeScript type mismatches in the REST API so that
`npx tsc --noEmit` exits with code 0 and all runtime tests in `test.ts` pass.

## Background

The workspace has five files:

- **`types.ts`** — Shared interface definitions. **Source of truth. Do NOT modify.**
- **`handlers.ts`** — HTTP handler layer. Contains type mismatches against `types.ts`.
- **`service.ts`** — Business logic layer. Contains type mismatches against `types.ts`.
- **`test.ts`** — Type-level and runtime tests. **Do NOT modify.**
- **`tsconfig.json`** — TypeScript config (`strict: true`). **Do NOT modify.**

## How Many Mismatches

There are **4–6 type mismatches** in this instance, spread across `handlers.ts` and
`service.ts`. The spec (this file) lists all of them exactly. The brief only says
"there are type errors".

## Mismatch Categories

Mismatches belong to one or more of these categories:

| Category | Description |
|---|---|
| `wrong_field_name` | Handler destructures a variable under the wrong name (e.g., `ageVal` instead of `age`) |
| `wrong_primitive_type` | Service type annotation uses `string` where interface says `number`, or vice-versa |
| `optional_as_required` | Handler accesses an optional field without a null/undefined check |
| `missing_required_field` | Service list function omits a required field from returned objects |
| `wrong_return_type` | Helper function annotated with wrong return type (e.g., `string` instead of `number`) |
| `date_as_string` | Service assigns `new Date().toISOString()` (a `string`) to a `Date` field |

## Exact Mismatches (Generated Per Seed)

The actual mismatch details are listed in the generated `spec.md` written to the
task directory at generation time. Each mismatch entry contains:
- Which file it is in (`handlers.ts` or `service.ts`)
- The exact line description and what is wrong
- The correct fix

## Requirements

1. `npx tsc --noEmit` must exit with code `0` (zero TypeScript errors).
2. `npx ts-node test.ts` must exit with code `0` (all assertions pass).
3. **Do NOT modify** `types.ts`, `test.ts`, or `tsconfig.json`.
4. Do not add `// @ts-ignore` or `// @ts-expect-error` suppressions.
5. Only edit `handlers.ts` and `service.ts`.

## File Map

| File | Action |
|------|--------|
| `types.ts` | **Read-only** — source of truth |
| `handlers.ts` | Fix handler-layer type mismatches |
| `service.ts` | Fix service-layer type mismatches |
| `test.ts` | **Read-only** — do not modify |
| `tsconfig.json` | **Read-only** — do not modify |

## Verification

```bash
cd /workspace
npm install
npx tsc --noEmit        # must exit 0
npx ts-node test.ts     # must exit 0
```

Both commands must exit 0.
