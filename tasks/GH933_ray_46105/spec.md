# GH933_ray_46105: [Serve] fix logging error on passing traceback object into exc_info — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ray-project/ray/issues/45912
- Repo: https://github.com/ray-project/ray

## Issue Description

There are some edge case we are missing doing the serve logger redirect those errors. Let's look into the issue and fix it.


A full traceback looks like 
```app.py:133 - Request 04155ecd-be7d-4bb4-a077-5de77d626bc5 complete. Model mistralai/Mistral-7B-Instruct-v0.1 generated 31 for user euser_p4u4i5e1di4ntlbnzrllfhhgjj. Billing fields: {}
base.py:61 - Completed: Generating streaming response
middleware.py:126 - Handling of the request 04155ecd-be7d-4bb4-a077-5de77d626bc5 successfully completed
replica.py:394 - __CALL__ OK 1089.0ms
_client.py:1773 - HTTP Request: POST https://api.metronome.com/v1/ingest "HTTP/1.1 200 OK"
handlers.py:75 - --- Logging error ---
traceback.py:105 - Traceback (most recent call last):

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/anyio/streams/memory.py", line 98, in receive
    return self.receive_nowait()

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/anyio/streams/memory.py", line 93, in receive_nowait
    raise WouldBlock

traceback.py:105 - anyio.WouldBlock

traceback.py:105 - 
During handling of the above exception, another exception occurred:


traceback.py:105 - Traceback (most recent call last):

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 159, in call_next
    message = await recv_stream.receive()

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/anyio/streams/memory.py", line 118, in receive
    raise EndOfStream

traceback.py:105 - anyio.EndOfStream

traceback.py:105 - 
During handling of the above exception, another exception occurred:


traceback.py:105 - Traceback (most recent call last):

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/middleware.py", line 44, in _handle_application_exceptions
    return await call_next(request)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 165, in call_next
    raise app_exc

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 151, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/opentelemetry/instrumentation/asgi/__init__.py", line 606, in __call__
    await self.app(scope, otel_receive, otel_send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/observability/middleware.py", line 39, in __call__
    await self.app(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 191, in __call__
    response = await self.dispatch_func(request, call_next)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/auth/auth_router.py", line 134, in token_authorization
    return await call_next(request)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 165, in call_next
    raise app_exc

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 151, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/routing.py", line 758, in __call__
    await self.middleware_stack(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/routing.py", line 778, in app
    await route.handle(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/routing.py", line 299, in handle
    await self.app(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/routing.py", line 79, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/_exception_handler.py", line 64, in wrapped_app
    raise exc

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    await app(scope, receive, sender)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/routing.py", line 74, in app
    response = await func(request)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/fastapi/routing.py", line 299, in app
    raise e

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/fastapi/routing.py", line 294, in app
    raw_response = await run_endpoint_function(

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/fastapi/routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/router_app.py", line 548, in chat
    await self._validate_model_for_endpoint(

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/router_app.py", line 690, in _validate_model_for_endpoint
    model_def = await self.model_data(model)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/router_app.py", line 432, in model_data
    model_data = await self.query_engine.model(model)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/plugins/multi_query_client.py", line 107, in model
    _, model_data = await self._find_client_for_model(model)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/plugins/multi_query_client.py", line 88, in _find_client_for_model
    model_def = await client.model(model)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/multiplex/multiplex_client.py", line 198, in model
    model_type, config = await self._get_model_config(model, raise_if_missing=False)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/multiplex/multiplex_client.py", line 214, in _get_model_config
    return ModelType.remote_multiplex_model, await self._authorize(

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/multiplex/multiplex_client.py", line 131, in _authorize
    anyscale_model_config = await anyscale_auth_client.authorize_multiplex_model(

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/asyncache/__init__.py", line 78, in wrapper
    val = await func(*args, **kwargs)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/auth/anyscale_auth_client.py", line 51, in authorize_multiplex_model
    res = await self._request(

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/backoff/_async.py", line 133, in retry
    ret = await target(*args, **kwargs)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/aviary_endpoints/backend/server/auth/anyscale_auth_client.py", line 153, in _request
    raise OpenAIHTTPException(

traceback.py:105 - rayllm.backend.server.openai_compat.openai_exception.OpenAIHTTPException: (404, 'Unable to find requested model. Please confirm that the model exists and you have permission.', 'Not found')

traceback.py:105 - 
During handling of the above exception, another exception occurred:


traceback.py:105 - Traceback (most recent call last):

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/logging/__init__.py", line 1083, in emit
    msg = self.format(record)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/logging/__init__.py", line 927, in format
    return fmt.format(record)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/ray/serve/_private/logging_utils.py", line 103, in format
    record_attributes = copy.deepcopy(record.__dict__)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 146, in deepcopy
    y = copier(x, memo)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 230, in _deepcopy_dict
    y[deepcopy(key, memo)] = deepcopy(value, memo)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 146, in deepcopy
    y = copier(x, memo)

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 210, in _deepcopy_tuple
    y = [deepcopy(a, memo) for a in x]

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 210, in <listcomp>
    y = [deepcopy(a, memo) for a in x]

traceback.py:105 -   File "/home/ray/anaconda3/lib/python3.9/copy.py", line 161, in deepcopy
    rv = reductor(4)

traceback.py:105 - TypeError: cannot pickle 'traceback' object

handlers.py:75 - Call stack:
traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/threading.py", line 937, in _bootstrap
    self._bootstrap_inner()

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/threading.py", line 980, in _bootstrap_inner
    self.run()

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/threading.py", line 917, in run
    self._target(*self._args, **self._kwargs)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/ray/serve/_private/replica.py", line 800, in _run_user_code_event_loop
    self._user_code_event_loop.run_forever()

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/ray/serve/_private/replica.py", line 1153, in call_user_method
    await self._call_func_or_gen(

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/ray/serve/_private/replica.py", line 877, in _call_func_or_gen
    result = await result

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/ray/serve/_private/http_util.py", line 456, in __call__
    await self._asgi_app(

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/applications.py", line 123, in __call__
    await self.middleware_stack(scope, receive, send)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/middleware.py", line 112, in __call__
    return await self.app(scope, receive, send)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/observability/middleware.py", line 80, in __call__
    await self.app(scope, receive, send_wrapper)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/cors.py", line 83, in __call__
    await self.app(scope, receive, send)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/starlette/middleware/base.py", line 191, in __call__
    response = await self.dispatch_func(request, call_next)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/routers/middleware.py", line 52, in _handle_application_exceptions
    response_payload = get_response_for_error(e, request_id)

traceback.py:25 -   File "/home/ray/anaconda3/lib/python3.9/site-packages/rayllm/backend/server/utils.py", line 283, in get_response_for_error
    log(

handlers.py:75 - Message: 'Encountered failure while handling request a174dfd1-5fe0-4cf4-aaf5-5e4130fc197c'
handlers.py:75 - Arguments: ()
middleware.py:115 - Handling of the request a174dfd1-5fe0-4cf4-aaf5-5e4130fc197c failed
_client.py:1773 - HTTP Request: POST https://app.endpoints.anyscale.com/endpoints-api/v1/public-auth/authenticate-model-id "HTTP/1.1 404 Not Found"
replica.py:394 - __CALL__ OK 623.5ms
_client.py:1773 - HTTP Request: POST https://api.metronome.com/v1/ingest "HTTP/1.1 200 OK"
_client.py:1773 - HTTP Request: POST https://api.metronome.com/v1/ingest "HTTP/1.1 200 OK"
app.py:133 - Request 099f431a-3026-4bab-a348-ae09ec49023d complete. Model mistralai/Mistral-7B-Instruct-v0.1 generated 103 for user euser_p4u4i5e1di4ntlbnzrllfhhgjj. Billing fields: {}
app.py:133 - Request 14bc1871-4035-4b46-a6d0-500b12d0796b complete. Model mistralai/Mistral-7B-Instruct-v0.1 generated 17 for user euser_5662l5fp93kh8nfvn7uk5ivrhn. Billing fields: {}
_client.py:1773 - HTTP Request: POST https://api.metronome.com/v1/ingest "HTTP/1.1 200 OK"
base.py:61 - Completed: Generating streaming response
base.py:61 - Completed: Generating streaming response
middleware.py:126 - Handling of the request 099f431a-3026-4bab-a348-ae09ec49023d successfully completed
middleware.py:126 - Handling of the request 14bc1871-4035-4b46-a6d0-500b12d0796b successfully completed
replica.py:394 - __CALL__ OK 1435.2ms
replica.py:394 - __CALL__ OK 2559.8ms
replica.py:1113 - Started executing request to method '__call__'.
middleware.py:79 - Starting handling of the request a20b8185-b4ce-4ae9-813b-7ced3f505e1a
__init__.py:821 - Setting attribute on ended span.
base.py:45 - Starting: Generating streaming response
handle.py:126 - Created DeploymentHandle 'e6gaewlv' for Deployment(name='VLLMDeployment:mlabonne--NeuralHermes-2_5-Mistral-7B', app='default').
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Was able to create a minimal reproducing code
```
import logging
from ray import serve

logger = logging.getLogger("ray.serve")


@serve.deployment
class App:
    def __call__(self):
        try:
            raise Exception("fake_exception")
        except Exception as e:
            logger.info("log message", exc_info=e)
        return "foo"


app = App.bind()

```
The issue is at https://github.com/anyscale/ray-llm/blob/6762e24d2df5a718128e8969cad5ebe68ba9710d/rayllm/backend/server/utils.py#L285 where the traceback object is passed in as `exc_info` and being part of log record's `__dict__`

## PR Review Comments

**[user]** on `python/ray/serve/schema.py`:

This is just a doc change, since I saw it while reading it. Unrelated to the actual bug.

**[user]** on `python/ray/serve/_private/logging_utils.py`:

no idea why this was here in the first place...

**[user]** on `python/ray/serve/_private/logging_utils.py`:

nit: probably better to just get rid of this aliasing and use `record.__dict__` directly instead

**[user]** on `python/ray/serve/_private/logging_utils.py`:

I feel it's probably a copy pasta from the line above 😅

**[user]** on `python/ray/serve/_private/logging_utils.py`:

great idea, will push a change

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
