# GH141_urllib3_3736: Fix `HTTPResponse.read_chunked` when leftover data is present in decoder's buffer — Full Specification (Planner Only)

## Source
- PR: https://github.com/urllib3/urllib3/pull/3736
- Issue: https://github.com/urllib3/urllib3/issues/3734
- Repo: https://github.com/urllib3/urllib3

## Issue Description

### Subject

When receiving a large brotli-compressed response with chunked transfer encoding, urllib3 2.6.x raises a `DecodeError` with the message:

```
brotli: decoder process called with data when 'can_accept_more_data()' is False
```

This appears to be a regression introduced in urllib3 2.6.0, likely related to the security changes for handling compressed content (GHSA-2xpw-w6gg-jr37). The issue occurs specifically when:
1. The response uses `Content-Encoding: br` (brotli)
2. The response uses `Transfer-Encoding: chunked`
3. The compressed data is moderately large (~500KB+ compressed)
4. Data arrives in small TCP segments

The issue does **not** occur with urllib3 2.5.0.

### Environment

```
OS: Linux 6.x (Debian Bookworm in Docker)
Python: 3.12.12
OpenSSL: OpenSSL 3.0.x
urllib3: 2.6.1
brotli: 1.2.0
requests: 2.31.0
```

Works correctly with:
```
urllib3: 2.5.0
brotli: 1.1.0
```

### Steps to Reproduce

Minimal reproduction script:

```python
#!/usr/bin/env python3
"""Minimal reproduction: brotli decode bug with urllib3 2.6.x + brotli 1.2.0"""

import hashlib
import socket
import threading

import brotli
import requests

def main() -> int:
    from importlib.metadata import version

    print(f"urllib3: {version('urllib3')}, brotli: {version('brotli')}")

    # Generate ~15MB data with moderate compressibility (~27x ratio)
    data = b"".join(
        f"{hashlib.sha256(str(i).encode()).hexdigest()}{'a' * 900}{i:06d}\n".encode()
        for i in range(15000)
    )
    compressed = brotli.compress(data)
    print(f"Data: {len(data):,} -> {len(compressed):,} bytes ({len(data) // len(compressed)}x)")

    # Build chunked HTTP response
    resp = b"HTTP/1.1 200 OK\r\nContent-Encoding: br\r\nTransfer-Encoding: chunked\r\n\r\n"
    for i in range(0, len(compressed), 32768):
        chunk = compressed[i : i + 32768]
        resp += f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n"
    resp += b"0\r\n\r\n"

    # Start mock server
    ready = threading.Event()

    def serve(port: int) -> None:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        ready.set()
        c, _ = s.accept()
        c.recv(4096)
        for i in range(0, len(resp), 128):  # Small chunks trigger bug
            c.send(resp[i : i + 128])
        c.close()
        s.close()

    threading.Thread(target=serve, args=(18765,), daemon=True).start()
    ready.wait()

    try:
        r = requests.get("http://127.0.0.1:18765/", timeout=60)
        print(f"SUCCESS: {len(r.content):,} bytes")
        return 0
    except requests.exceptions.ContentDecodingError as e:
        print(f"FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
```

### Expected Behavior

The response should be successfully decompressed and returned:

```
urllib3: 2.5.0, brotli: 1.1.0
Data: 14,565,000 -> 549,724 bytes (26x)
SUCCESS: 14,565,000 bytes
```

### Actual Behavior

With urllib3 2.6.x, the request fails with a `ContentDecodingError`:

```
urllib3: 2.6.1, brotli: 1.2.0
Data: 14,565,000 -> 549,724 bytes (26x)
FAILED: ('Received response with content-encoding: br, but failed to decode it.', 
         error("brotli: decoder process called with data when 'can_accept_more_data()' is False"))
```

Full traceback:
```
urllib3.exceptions.DecodeError: ('Received response with content-encoding: br, but 
failed to decode it.', error("brotli: decoder process called with data when 
'can_accept_more_data()' is False"))
```

The error suggests that the brotli decoder signals completion (`can_accept_more_data()` returns `False`) but urllib3 continues trying to feed it more compressed data from the chunked stream.

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@hanamurayuki):

same here

### Comment 2 (@Cycloctane):

[Code changes omitted — Planner should analyze the issue and guide the Executor]

### Comment 3 (@illia-v):

Please check if #3736 fixes your issue. Thanks for the reproducer, it doesn't fail with the fix.

### Comment 4 (@illia-v):

@Cycloctane that's the same logic as in my fix, thanks 👍🏻
I reused your approach to simplify #3736.

### Comment 5 (@corsac-s):

So for what it's worth I'm experiencing this on Debian sid with:

```
ii python3-urllib3                              2.5.0-1
ii  libbrotli-dev:amd64                          1.1.0-2+b9      
ii  libbrotli1:amd64                             1.1.0-2+b9      
ii  python3-brotli                               1.1.0-2+b9   
ii  python3-brotlicffi                           1.2.0.0+ds-1+b1 
```

So it might be more related to the brotli update than an urllib update. Unfortunately I don't seem to be able to apply the patch in #3736 to 2.5.0 so I might have to wait until Debian updates urllib (or maybe switch to a venv at least temporarily)

### Comment 6 (@kesara):

Indeed this seems to be an error related to brotli 1.2.0 update.

Sample code results from the original issue:
With brotli 1.1.0:
```
urllib3: 2.6.1, brotli: 1.1.0
Data: 14,565,000 -> 549,724 bytes (26x)
SUCCESS: 14,565,000 bytes
```

With brotli 1.2.0:
```
urllib3: 2.6.1, brotli: 1.2.0
Data: 14,565,000 -> 549,724 bytes (26x)
Exception in thread Thread-1 (serve):
FAILED: ('Received response with content-encoding: br, but failed to decode it.', error("brotli: decoder process called with data when 'can_accept_more_data()' is False"))
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.12/3.12.12/Frameworks/Python.framework/Versions/3.12/lib/python3.12/threading.py", line 1075, in _bootstrap_inner
```

### Comment 7 (@aborigeth):

> Please check if [#3736](https://github.com/urllib3/urllib3/pull/3736) fixes your issue. Thanks for the reproducer, it doesn't fail with the fix.

So far, fix works for me.

### Comment 8 (@illia-v):

The fix was released in [v2.6.2](https://github.com/urllib3/urllib3/releases/tag/2.6.2).

### Comment 9 (@zanllan24-spec):

My until el aporte gracias por em apoyo y las cknfirmaciones.

## Files Changed in Fix

- `changelog/3734.bugfix.rst` (added, +2/-0)
- `src/urllib3/response.py` (modified, +8/-4)
- `test/test_response.py` (modified, +41/-0)

## `src/urllib3/response.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
