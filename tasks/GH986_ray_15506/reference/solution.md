# Reference solution — GH986_ray_15506

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH986_ray_15506`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH986_ray_15506/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dashboard/head.py` (modified, +3/-0)
- `dashboard/tests/test_dashboard.py` (modified, +19/-0)

## Diff Summary (What the Fix Changes)

### `dashboard/head.py`
```diff
@@ -3,6 +3,7 @@
 import json
 import asyncio
 import logging
+import ipaddress
 
 import aiohttp
 import aiohttp.web
@@ -210,6 +211,8 @@ async def _async_notify():
             raise Exception(f"Failed to find a valid port for dashboard after "
                             f"{self.http_port_retries} retries: {last_ex}")
         http_host, http_port, *_ = site._server.sockets[0].getsockname()
+        http_host = self.ip if ipaddress.ip_address(
+            http_host).is_unspecified else http_host
         logger.info("Dashboard head http address: %s:%s", http_host, http_port)
 
         # Write the dashboard head port to redis.
```

## Moved from `brief.md`

## Files That May Need Changes

- `dashboard/head.py`
