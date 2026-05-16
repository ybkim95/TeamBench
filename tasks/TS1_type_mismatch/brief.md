# TS1_type_mismatch: Fix TypeScript Type Errors (Brief)

The REST API has TypeScript type errors between the shared type definitions
(`types.ts`) and the implementations in `handlers.ts` and `service.ts`.

Fix the type errors so both of the following pass:

```bash
cd /workspace
npm install
npx tsc --noEmit     # must exit 0
npx ts-node test.ts  # must exit 0
```

**Do NOT modify** `types.ts`, `test.ts`, or `tsconfig.json`.
Only modify `handlers.ts` and `service.ts`.

Follow the Planner's guidance precisely.
