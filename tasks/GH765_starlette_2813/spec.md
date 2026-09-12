# GH765_starlette_2813: Fix unclosed 'MemoryObjectReceiveStream' upon exception in 'BaseHTTPMiddleware' children — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Kludex/starlette

## PR Description

I open a different PR to remove the `close_recv_stream_on_response_sent`. I'm not sure that's why the test is failing...

## PR Review Comments

**[user]** on `starlette/middleware/base.py`:

Remove this as per [user] comment on https://matrix.to/#/!JfFIjeKHlqEVmAsxYP:gitter.im/$S0X8-1wH1qscoq6FQjVCVDgBL4Qk-5BcTnaQfqBCkGI?via=gitter.im&via=matrix.org&via=matrix.freyachat.eu

**[user]** on `starlette/middleware/base.py`:

```suggestion
        send_stream, recv_stream = anyio.create_memory_object_stream[Message]()
```

**[user]** on `starlette/testclient.py`:

```suggestion
            self._send_queue.put(EOF)  # TODO: use self._send_queue.shutdown() on 3.13+
```

**[user]** on `starlette/middleware/base.py`:

```suggestion
```

**[user]** on `starlette/testclient.py`:

The problem this solves is not related to this PR then?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
