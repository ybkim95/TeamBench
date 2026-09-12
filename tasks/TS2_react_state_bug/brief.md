# TS2_react_state_bug (Brief)

The `ChatWindow` React component has bugs causing incorrect behaviour:
some updates are lost, data goes stale after prop changes, and the
component may crash after unmounting.

Fix the component so all tests pass:

```
npm test
```

**File to fix:** `src/ChatWindow.tsx`
**Do NOT modify:** `src/types.ts`, `src/hooks/useDebounce.ts`,
`src/ChatWindow.test.tsx`, `package.json`, `tsconfig.json`

Follow the Planner's guidance precisely.
