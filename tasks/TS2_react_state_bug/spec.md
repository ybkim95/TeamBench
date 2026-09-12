# TS2_react_state_bug: React State Bug Fix — Full Specification (Planner Only)

            ## Overview

            The workspace contains a React component `ChatWindow.tsx` that manages
            messages with the following configuration:
            - Initial unread count: `3`
            - Max items: `60`
            - Flash interval: `3000ms`

            There are **4 intentional bugs** and **2 intentional-but-correct patterns**
            that must be preserved. The executor only receives the brief; this spec
            provides the full analysis.

            ## File Structure

            - `src/ChatWindow.tsx` — component with all bugs (the only file to modify)
            - `src/types.ts` — type definitions (do NOT modify)
            - `src/hooks/useDebounce.ts` — utility hook (do NOT modify)
            - `src/ChatWindow.test.tsx` — tests that detect each bug (do NOT modify)
            - `package.json`, `tsconfig.json` — build config (do NOT modify)

            ## Bug Analysis

            | # | Type | Location | Fix |
            |---|------|----------|-----|
            | A | stale_closure_counter | `handleUnreadIncrement` in `ChatWindow.tsx` | Change `setUnreadCount(unreadCount + 1)` to `setUnreadCount(c => c + 1)` |
| B | missing_dep_useeffect | fetch `useEffect` in `ChatWindow.tsx` | Add `messageId` and `maxItems` to the dependency array |
| C | missing_cleanup | subscription `useEffect` in `ChatWindow.tsx` | Return `() => { chatSubscription.unsubscribe(); }` from the effect |
| D | state_mutation | `handleMessageAdded` in `ChatWindow.tsx` | Replace `messages.push(newItem); setMessages(messages)` with `setMessages(prev => [...prev, newItem])` |

            ### Bug Details

### Bug A — Stale Closure in Counter Increment

**Location:** `handleUnreadIncrement` in `ChatWindow.tsx`

**Root cause:** The handler captures `unreadCount` from the render
closure. Under React's batched updates (e.g., rapid clicks) the captured
value is stale — two clicks in the same batch both read the same value,
so only one increment is applied.

**Buggy code:**
```tsx
const handleUnreadIncrement = () => {
  setUnreadCount(unreadCount + 1); // stale closure
};
```

**Fix:**
```tsx
const handleUnreadIncrement = () => {
  setUnreadCount(c => c + 1); // functional updater
};
```

### Bug B — Missing Dependency in `useEffect`

**Location:** fetch `useEffect` in `ChatWindow.tsx`

**Root cause:** The effect calls `fetch('/api/chat/messages/messageId')` but
`messageId` (and `maxItems`) are not in the dependency array (`[]`).
When the parent re-renders with a new `messageId` prop, the effect
does NOT re-run, leaving stale data displayed.

**Fix:** Add `messageId` and `maxItems` to the dependency array:
```tsx
}}, [messageId, maxItems]);
```

### Bug C — Missing Cleanup in Subscription Effect

**Location:** subscription `useEffect` in `ChatWindow.tsx`

**Root cause:** The effect creates a `chatSubscription` but never
returns a cleanup function. When the component unmounts the subscription
continues firing, causing `setState` calls on an unmounted component and
potential memory leaks.

**Fix:** Return a cleanup function:
```tsx
useEffect(() => {
  const chatSubscription = ...;
  return () => {
    chatSubscription.unsubscribe();
  };
}, [messageId]);
```

### Bug D — Direct State Mutation

**Location:** `handleMessageAdded` in `ChatWindow.tsx`

**Root cause:** The handler calls `messages.push(newItem)` which mutates
the existing array in place. React uses reference equality to detect changes;
since the array reference is the same, no re-render is triggered.

**Buggy code:**
```tsx
messages.push(newItem);
setMessages(messages); // same ref — React skips re-render
```

**Fix:** Create a new array:
```tsx
setMessages(prev => [...prev, newItem]);
```

## Intentional Patterns (DO NOT CHANGE)

### I1 — Empty Dependency Array in Subscription Effect

The `useEffect` that sets up the chatSubscription subscription uses
`[messageId]` as its dependency array. This is **correct and intentional**:
the subscription should be re-established only when the ID changes,
not on every render.

### I2 — Double `setFlashActive` Call in `triggerFlash`

The `triggerFlash` function sets `flashActive` to `true` then schedules
it back to `false` after `3000ms`. This **looks redundant but is
required** to trigger the CSS transition animation. Do NOT simplify this
to a single `setFlashActive(false)`.

## Acceptance Criteria

1. `tsc --noEmit` reports zero errors
2. All 5 tests in `ChatWindow.test.tsx` pass
3. The two intentional patterns (I1 and I2) are preserved unchanged
4. Only `src/ChatWindow.tsx` is modified

## Expected Behavior After Fixes

- Rapid button clicks increment `unreadCount` correctly (no lost updates)
- Fetching re-runs when `messageId` prop changes
- Subscription is cleaned up on unmount (no leaked listeners)
- Adding items via state setter triggers re-render
- Flash animation works correctly (double state toggle preserved)
