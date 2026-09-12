# GH71_starlette_3189: Handle websocket denial responses in streaming and file responses — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Kludex/starlette/issues/3048
- Repo: https://github.com/Kludex/starlette

## Issue Description

### Discussed in https://github.com/Kludex/starlette/discussions/2566

<div type='discussions-op-text'>

<sup>Originally posted by **WSH032** April  6, 2024</sup>
## Describe the bug

If we use `FileResponse` or `StreamingResponse` when sending the Websocket Denial Response, a `RuntimeError` will occur.

## To Reproduce

```py
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from uvicorn import run

app = FastAPI()

@app.websocket("/")
async def _(ws: WebSocket):
    async def foo():
        yield "hello"
        yield "world"

    resp = StreamingResponse(content=foo())
    await ws.send_denial_response(resp)

run(app)
```

Steps to reproduce the behavior:
1. Launch the server
2. Try to establish the websocket connection
3. You will see following error

```console
  |   File "e:\GitHub\fastapi-proxy\Untitled-8.py", line 16, in _
  |     await ws.send_denial_response(resp)
  |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\starlette\websockets.py", line 209, in send_denial_response        
  |     await response(self.scope, self.receive, self.send)
  |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\starlette\responses.py", line 258, in __call__
  |     async with anyio.create_task_group() as task_group:
  |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\anyio\_backends\_asyncio.py", line 678, in __aexit__
  |     raise BaseExceptionGroup(
  | exceptiongroup.ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\starlette\responses.py", line 261, in wrap
    |     await func()
    |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\starlette\responses.py", line 243, in stream_response
    |     await send(
    |   File "E:\GitHub\fastapi-proxy\.venv\lib\site-packages\starlette\websockets.py", line 75, in send
    |     raise RuntimeError(
    | RuntimeError: Expected ASGI message "websocket.accept","websocket.close" or "websocket.http.response.start",but got 'http.response.start'
    +------------------------------------
```

## Expected behavior

`FileResponse` and `StreamingResponse` override the `__call__` method, but they do not add the `"websocket."` prefix like the parent class `Response` does.

https://github.com/encode/starlette/blob/4e453ce91940cc7c995e6c728e3fdf341c039056/starlette/responses.py#L151-L154

If this is expected behavior, I didn't see any relevant information in the documentation, and at least the type checker didn't raise any errors

## Configuration
```
starlette == 0.37.2
```
</div>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi, I've not seen any update on this issue and thought of attempting to fix this using this PR: (withheld: the upstream fix is not part of the task)

Please take a look when you get a chance

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
