# GH246_core_120764: Yamaha device setup enhancement with unique id based on serial — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/111108
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

I used smart power plugs to unpower my Yamaha receiver quite often. Upon Home Assistant updates core gets restarted including the yamaha integration. The integration fails to setup the connection to my configured device, it only retries a few times and the finally fails. 

Q: What is missing?
A: There is no "unlimited" retry handling as other integrations do.

### What version of Home Assistant Core has the issue?

core-2024.2.2

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

yamaha

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/yamaha/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Logger: homeassistant.components.media_player
Source: helpers/entity_platform.py:344
Integration: Mediaplayer (documentation, issues)
First occurred: 19. Februar 2024 um 20:25:12 (1 occurrences)
Last logged: 19. Februar 2024 um 20:25:12

Error while setting up yamaha platform for media_player

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/urllib3/connection.py", line 174, in _new_conn
    conn = connection.create_connection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/urllib3/util/connection.py", line 95, in create_connection
    raise err
  File "/usr/local/lib/python3.12/site-packages/urllib3/util/connection.py", line 85, in create_connection
    sock.connect(sa)
OSError: [Errno 113] Host is unreachable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/urllib3/connectionpool.py", line 715, in urlopen
    httplib_response = self._make_request(
                       ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/urllib3/connectionpool.py", line 416, in _make_request
    conn.request(method, url, **httplib_request_kw)
  File "/usr/local/lib/python3.12/site-packages/urllib3/connection.py", line 244, in request
    super(HTTPConnection, self).request(method, url, body=body, headers=headers)
  File "/usr/local/lib/python3.12/http/client.py", line 1327, in request
    self._send_request(method, url, body, headers, encode_chunked)
  File "/usr/local/lib/python3.12/http/client.py", line 1373, in _send_request
    self.endheaders(body, encode_chunked=encode_chunked)
  File "/usr/local/lib/python3.12/http/client.py", line 1322, in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
  File "/usr/local/lib/python3.12/http/client.py", line 1081, in _send_output
    self.send(msg)
  File "/usr/local/lib/python3.12/http/client.py", line 1025, in send
    self.connect()
  File "/usr/local/lib/python3.12/site-packages/urllib3/connection.py", line 205, in connect
    conn = self._new_conn()
           ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/urllib3/connection.py", line 186, in _new_conn
    raise NewConnectionError(
urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x7f02f1f0bfb0>: Failed to establish a new connection: [Errno 113] Host is unreachable

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/requests/adapters.py", line 486, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/urllib3/connectionpool.py", line 799, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/urllib3/util/retry.py", line 592, in increment
    raise MaxRetryError(_pool, url, error or ResponseError(cause))
urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='10.0.xx.xx', port=80): Max retries exceeded with url: /YamahaRemoteControl/desc.xml (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f02f1f0bfb0>: Failed to establish a new connection: [Errno 113] Host is unreachable'))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 344, in _async_setup_platform
    await asyncio.shield(task)
  File "/usr/src/homeassistant/homeassistant/components/yamaha/media_player.py", line 145, in async_setup_platform
    receivers = await hass.async_add_executor_job(_discovery, config_info)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/yamaha/media_player.py", line 125, in _discovery
    receivers = rxv.RXV(config_info.ctrl_url, config_info.name).zone_controllers()
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/rxv/rxv.py", line 132, in __init__
    self._discover_features()
  File "/usr/local/lib/python3.12/site-packages/rxv/rxv.py", line 137, in _discover_features
    desc_xml = self._session.get(
               ^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/requests/sessions.py", line 602, in get
    return self.request("GET", url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/requests/adapters.py", line 519, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPConnectionPool(host='10.0.xx.xx', port=80): Max retries exceeded with url: /YamahaRemoteControl/desc.xml (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f02f1f0bfb0>: Failed to establish a new connection: [Errno 113] Host is unreachable'))
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[yamaha documentation](https://www.home-assistant.io/integrations/yamaha)
[yamaha source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/yamaha)

### Comment 2 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

## PR Review Comments

**[user]** on `homeassistant/components/yamaha/media_player.py`:

If I understand correctly, this changes the unique_id of the entities, we should not change that without a migration. For me its unclear what this is actually achieving right now since the unique id is the same but with the domain added in front

**[user]** on `homeassistant/components/yamaha/media_player.py`:

I agree and for Yamaha MusicCast enabled amps that the right solution, I was worried about this if I fixed up auto discovery but given I have the last generation of amp without it and that's 9 years old, I think the code will be good enough as is without this discovery, or at last deal with this then...

**[user]** on `homeassistant/components/yamaha/media_player.py`:

But what does this PR actually change? It looks like we only prepend `zone_`

**[user]** on `homeassistant/components/yamaha/media_player.py`:

Hi,  _discovery retrieve more info(serial)) if we can via discovery even for static host entries now and  async_setup_platform is changed to cope with the receiver not being there on planform init.

**[user]** on `homeassistant/components/yamaha/media_player.py`:

Please don't log on info

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
