# Reference solution — GH1210_wandb_11242

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1210_wandb_11242`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1210_wandb_11242/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.unreleased.md` (modified, +4/-0)
- `tests/system_tests/test_artifacts/test_wandb_artifacts_full.py` (modified, +57/-0)
- `tests/unit_tests/test_artifacts/test_wandb_artifacts.py` (modified, +105/-62)
- `wandb/sdk/artifacts/storage_policies/_factories.py` (modified, +3/-0)
- `wandb/sdk/artifacts/storage_policies/_multipart.py` (modified, +143/-53)
- `wandb/sdk/artifacts/storage_policies/wandb_storage_policy.py` (modified, +25/-1)

## Diff Summary (What the Fix Changes)

### `wandb/sdk/artifacts/storage_policies/_factories.py`
```diff
@@ -37,6 +37,9 @@ def make_http_session() -> Session:
     HTTP_RETRY_STRATEGY: Final[Retry] = Retry(  # noqa: N806
         backoff_factor=1,
         total=16,
+        # 401, 403 are not retried because expired presigned url
+        # requires calling graphql to get a new url. Upper layer such as
+        # _download_chunk_with_refresh in _multipart handles refresh.
         status_forcelist=(308, 408, 409, 429, 500, 502, 503, 504),
     )
 
```

### `wandb/sdk/artifacts/storage_policies/_multipart.py`
```diff
@@ -8,12 +8,14 @@
 from concurrent.futures import FIRST_EXCEPTION, Executor, wait
 from dataclasses import dataclass, field
 from queue import Queue
-from typing import TYPE_CHECKING, Any, Final, Iterator, Union
+from typing import IO, TYPE_CHECKING, Any, Callable, Final, Iterator, Union
 
+import requests
 from typing_extensions import TypeAlias, TypeIs, final
 
 from wandb import env
 from wandb.sdk.artifacts.artifact_file_cache import Opener
+from wandb.sdk.lib import retry
 
 if TYPE_CHECKING:
     from requests import Session
@@ -95,79 +97,167 @@ def scan_chunks(path: str, chunk_size: int) -> Iterator[bytes]:
 
 @dataclass
 class MultipartDownloadContext:
+    """Shared state for multipart download threads."""
+
+    session: Session
     q: Queue[QueuedChunk]
     cancel: threading.Event = field(default_factory=threading.Event)
 
+    # URL state management (thread-safe)
+    _url_lock: threading.Lock = field(default_factory=threading.Lock)
+    _url: str = ""
+    _url_invalidated: bool = False
+    _url_fetch_fn: Callable[[], str] | None = None
+
+    def get_url(self) -> str:
+        """Get the current URL, fetching a fresh one only if invalidated."""
+        with self._url_lock:
+            if self._url_invalidated and self._url_fetch_fn:
+                self._url = self._url_fetch_fn()
+                self._url_invalidated = False
+            return self._url
+
+    def invalidate_url(self) -> None:
+        """Mark the cached URL as invalid, forcing next get_url() to fetch fresh."""
+        with self._url_lock:
+            self._url_invalidated = True
+
+
+def _download_chunk_with_refresh(
+    ctx: MultipartDownloadContext,
+    start: int,
+    end: int | None,
+) -> None:
+    """Download a single chunk with refresh logic for expired presigned URLs.
+
+    Args:
+        ctx: Shared download context with session, queue, cancel event, and URL state.
+        start: Start byte offset (inclusive).
+        end: End byte offset (inclusive), or Non
```

### `wandb/sdk/artifacts/storage_policies/wandb_storage_policy.py`
```diff
@@ -12,6 +12,7 @@
 from typing import TYPE_CHECKING, Any
 from urllib.parse import quote
 
+import requests
 from typing_extensions import assert_never
 
 from wandb.errors.term import termwarn
@@ -142,7 +143,30 @@ def load_file(
         if url := manifest_entry._download_url:
             # Use multipart parallel download for large file
             if executor and (size := manifest_entry.size):
-                multipart_download(executor, self._session, url, size, cache_open)
+                # Create URL provider with GraphQL-based refresh callback
+                def fetch_fresh_url() -> str:
+                    files = artifact.files(
+                        names=[str(manifest_entry.path)],
+                        per_page=1,
+                    )
+
+                    try:
+                        file = next(iter(files))
+                    except StopIteration:
+                        raise ValueError(
+                            f"Failed to fetch URL for file: {manifest_entry.path}"
+                        )
+                    else:
+                        return file.direct_url
+
+                multipart_download(
+                    executor,
+                    self._session,
+                    size,
+                    cache_open,
+                    initial_url=url,
+                    fetch_fn=fetch_fresh_url,
+                )
                 return path
 
             # Serial download
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `wandb/sdk/artifacts/storage_policies/_factories.py`
- `wandb/sdk/artifacts/storage_policies/_multipart.py`
- `wandb/sdk/artifacts/storage_policies/wandb_storage_policy.py`
