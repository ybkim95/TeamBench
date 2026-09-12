# GH8: Async Dependency Cache Race Condition — Full Specification

## Issue

Under concurrent async requests, `Depends(get_current_user)` sometimes returns
the wrong user. Request A's user appears in Request B's context.

**Reported behaviour**: In production with ≥ 2 workers handling simultaneous
requests to `/me` or `/profile`, the response occasionally contains another
user's identity. The bug is non-deterministic and disappears under sequential
load, making it easy to miss in testing.

## Root Cause

`DependencyResolver._cache` is a shared dict keyed by the dependency function
name alone:

```python
cache_key = dep.func.__name__          # BUG: no request identity
if cache_key in self._cache:
    return self._cache[cache_key]
result = await dep.func(request)
self._cache[cache_key] = result        # overwrites another request's slot
return result
```

When two async requests resolve the same dependency concurrently:

1. Request A starts resolving `get_current_user`. No cache hit — proceeds to
   call the async function and awaits it.
2. While Request A is awaited, the event loop suspends it and starts Request B.
3. Request B also finds no cache entry (A hasn't written yet) and calls the
   async function.
4. Both coroutines resume in some order. Whichever writes last wins, and the
   other request reads the winner's value on a subsequent cache lookup —
   returning the wrong user.

The race window is widened by any `await` inside the dependency function
(e.g., a database query, an HTTP call, or even `asyncio.sleep()`).

## The Fix

Include the request ID in the cache key so each request has its own namespace:

```python
cache_key = (dep.func.__name__, request.id)   # scoped to this request
```

This ensures that cached values written by Request A are never visible to
Request B. The cache still provides the intended within-request deduplication
(the same dependency used by multiple handlers in one request is evaluated
only once).

An equivalent alternative is to use a per-request cache dict (created fresh
for every call to `handle_request`) instead of a single shared dict.

## What Must Not Change

- **Dependency resolution order**: Sub-dependencies (dependencies of
  dependencies) are resolved depth-first before the route handler runs. This
  ordering is correct and must be preserved.
- **Route registration and URL matching**: The `Router.add_route` / `App.route`
  decorator interface and the path-matching logic are correct.
- **`use_cache=False` behaviour**: Dependencies created with
  `Dependency(func, use_cache=False)` already bypass the cache on every call
  and must continue to do so after the fix.
- **Handler signature**: Route handlers receive `(request, deps)` where `deps`
  is a dict mapping function name to resolved value. This contract must not
  change.
