# GH25_aiohttp_12245: [PR #12217 backport][3.14] Raise on redirect with consumed non-rewindable request bodies — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/aio-libs/aiohttp/issues/12195
- Repo: https://github.com/aio-libs/aiohttp

## Issue Description

### Describe the bug

uploading a file, redirect to other url, will send empty data.

### To Reproduce

```python
# redirect.py
from aiohttp import web

async def handle(request):
    raise web.HTTPTemporaryRedirect('http://httpbin.org/post')

app = web.Application()
app.router.add_post('/', handle)
app.router.add_post('/{path:.*}', handle)

if __name__ == '__main__':
    web.run_app(app, port=8080)

```

```python
# client.py
import asyncio

import aiofiles
import aiohttp

async def file_sender(file_name=None):
    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(64 * 1024)
        while chunk:
            yield chunk
            chunk = await f.read(64 * 1024)

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://httpbin.org/post',
                                data=file_sender(file_name='huge_file')) as resp:
            print(await resp.text())
            """
            {
              "args": {}, 
              "data": "data:application/octet-stream;base64,H4sIAAARNl4C/+y9e3sTR7Iwvn/zPHyH ...... ", 
              "files": {}, 
              "form": {}, 
              "headers": {
                "Accept": "*/*", 
                "Accept-Encoding": "gzip, deflate", 
                "Content-Type": "application/octet-stream", 
                "Host": "httpbin.org", 
                "Transfer-Encoding": "chunked", 
                "User-Agent": "Python/3.13 aiohttp/3.13.3", 
                "X-Amzn-Trace-Id": "Root=1-69a8225e-08fc19484261a700527700cc"
              }, 
              "json": null, 
              "origin": "61.149.70.168", 
              "url": "http://httpbin.org/post"
            }       
            """

        async with session.post('http://localhost:8080/post',
                                data=file_sender(file_name='huge_file')) as resp:
            print(await resp.text())
            """
            {
              "args": {}, 
              "data": "", 
              "files": {}, 
              "form": {}, 
              "headers": {
                "Accept": "*/*", 
                "Accept-Encoding": "gzip, deflate", 
                "Content-Length": "0", 
                "Content-Type": "application/octet-stream", 
                "Host": "httpbin.org", 
                "User-Agent": "Python/3.13 aiohttp/3.13.3", 
                "X-Amzn-Trace-Id": "Root=1-69a8225f-20c3324430583ce72991e30e"
              }, 
              "json": null, 
              "origin": "61.149.70.168", 
              "url": "http://httpbin.org/post"
            }
        """

if __name__ == "__main__":
    asyncio.run(main())

```

### Expected behavior

None

### Logs/tracebacks

```python-traceback
None
```

### Python Version

```console
Python 3.13.6
```

### aiohttp Version

```console
Name: aiohttp
Version: 3.13.3
Summary: Async http client/server framework (asyncio)
Home-page: https://github.com/aio-libs/aiohttp
Author:
Author-email:
License: Apache-2.0 AND MIT
Location: D:\GitHub\ksrpc\.venv\Lib\site-packages
Requires: aiohappyeyeballs, aiosignal, attrs, frozenlist, multidict, propcache, yarl
Required-by: ksrpc
```

### multidict Version

```console
Name: multidict
Version: 6.7.1
Summary: multidict implementation
Home-page: https://github.com/aio-libs/multidict
Author: [redacted]
Author-email: [email redacted]
License: Apache License 2.0
Location: D:\GitHub\ksrpc\.venv\Lib\site-packages
Requires:
Required-by: aiohttp, yarl
```

### propcache Version

```console
Name: propcache
Version: 0.4.1
Summary: Accelerated property cache
Home-page: https://github.com/aio-libs/propcache
Author: [redacted]
Author-email: [email redacted]
License: Apache-2.0
Location: D:\GitHub\ksrpc\.venv\Lib\site-packages
Requires:
Required-by: aiohttp, yarl
```

### yarl Version

```console
Name: yarl
Version: 1.23.0
Summary: Yet another URL library
Home-page: https://github.com/aio-libs/yarl
Author: [redacted]
Author-email: [email redacted]
License: Apache-2.0
Location: D:\GitHub\ksrpc\.venv\Lib\site-packages
Requires: idna, multidict, propcache
Required-by: aiohttp
```

### OS

Windows

### Related component

Client, Server

### Additional context

_No response_

### Code of Conduct

- [x] I agree to follow the aio-libs Code of Conduct

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

file_sender() is a generator. When sending the request to the original URL you used the generator, so there is no way to send the contents again in the second request. Maybe we could raise an exception here instead..

For file uploading, I think you can just use the file object, in which case aiohttp can seek back to the start of the file for the second request. See if you can try something like:
```
f = await asyncio.to_thread(open, file_name, "rb")
# data=f
```

If that works for you, then please make a PR to update the docs examples.

### Comment 2 ([user]):

> If that works for you, then please make a PR to update the docs examples.

Actually, the first example does exactly that:
```
with open('massive-body', 'rb') as f:
   await session.post('http://httpbin.org/post', data=f)
```

The second example should probably be changed to not open a file and do something else with an async generator.

### Comment 3 ([user]):

Actually, my real use case involves uploading a large amount of data. Compressing it makes the file much smaller, but compressing the entire chunk at once takes a long time. So, I used a method that compresses and transmits the data in chunks simultaneously. Initially, I employed an iterator approach, which sped up the upload by dozens of times, but I later discovered that redirects don’t work with it.

Now, if the first request needs to send a large amount of data before the redirect occurs, it becomes much slower.

I’m currently feeling stuck.

### Comment 4 ([user]):

Best solution would be to avoid the redirects if possible. Otherwise, you'd need to disable the automatic redirects (allow_redirects=False) and make new requests to the redirect URL manually.

### Comment 5 ([user]):

Thank you very much.

Indeed, the file upload request should be split into two separate requests.

### Comment 6 ([user]):

Looks like a simple fix. 

The code should collect chunks during streaming and stores them in `_cached_chunks` instead of marking the payload as consumed.

I can submit a PR for this one if [user] doesn't intend to.

### Comment 7 ([user]):

> The code should collect chunks during streaming and stores them in `_cached_chunks` instead of marking the payload as consumed.

If a user uses a generator, that likely indicates they don't want to load everything into memory (it might be producing GBs of data). So, caching the result of the iterator is probably not an acceptable action. Unless I'm misunderstanding your suggestion?

I think actions we can take here:

- Update the file example from the docs to avoid the redirect (presumably just needs to use https://). Probably also use asyncio.to_thread() as I showed above.
- Replace the aiofiles iterator example with something that doesn't open a file (e.g. Just generate some lines by iterating over range()).
- Add a warning to the example explaining that redirects need to be avoided or manually handled.

### Comment 8 ([user]):

Sorry, you are right, guys. I misunderstood the issue. Working on the PR based on the [user] comments

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
