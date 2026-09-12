# GH98_urllib3_3769: Fix readinto type hint to accept memoryview for BufferedReader compatibility — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/urllib3/urllib3/issues/3764
- Repo: https://github.com/urllib3/urllib3

## Issue Description

### Subject

`BaseHTTPResponse.readinto` is implemented to provide compatibility with the io module 

https://github.com/urllib3/urllib3/blob/b90b2794cb3b462a1a190cecba2999c1d3c353e9/src/urllib3/response.py#L665-L673

However the implementation's typehinting is not compatible with what python docs say are valid inputs for the method.

https://docs.python.org/3/library/io.html#io.RawIOBase.readinto
> Read bytes into a pre-allocated, writable [bytes-like object](https://docs.python.org/3/glossary.html#term-bytes-like-object) b

Where bytes-like objects can be any of: 
> object that supports the [Buffer Protocol](https://docs.python.org/3/c-api/buffer.html#bufferobjects) and can export a C-[contiguous](https://docs.python.org/3/glossary.html#term-contiguous) buffer. This includes all [bytes](https://docs.python.org/3/library/stdtypes.html#bytes), [bytearray](https://docs.python.org/3/library/stdtypes.html#bytearray), and [array.array](https://docs.python.org/3/library/array.html#array.array) objects, as well as many common [memoryview](https://docs.python.org/3/library/stdtypes.html#memoryview) objects. ...

And detail most relevant here would be the read-write variant of bytes-like object https://docs.python.org/3/glossary.html#term-bytes-like-object
> Some operations need the binary data to be mutable. The documentation often refers to these as “read-write bytes-like objects”. Example mutable buffer objects include [bytearray](https://docs.python.org/3/library/stdtypes.html#bytearray) and a [memoryview](https://docs.python.org/3/library/stdtypes.html#memoryview) of a [bytearray](https://docs.python.org/3/library/stdtypes.html#bytearray).

### Environment

(not a runtime issue)

### Steps to Reproduce

```py
import io
import requests
from urllib3.response import HTTPResponse

with requests.get(url, stream=True) as response:
        data_stream = response.raw
        assert isinstance(data_stream, HTTPResponse)
        _ = io.BufferedReader(data_stream)
```

Run mypy on this snippet using typeshed for annotations for the io module

### Expected Behavior

mypy should pass this piece of code

### Actual Behavior

```
error: Argument 1 to "BufferedReader" has incompatible type "HTTPResponse"; expected "_BufferedReaderStream"  [arg-type]
note: Following member(s) of "HTTPResponse" have conflicts:
note:     Expected:
note:         def readinto(self, memoryview[int], /) -> int | None
note:     Got:
note:         def readinto(self, b: bytearray) -> int
```

---

I am also filing a issue with typeshed to improve the typing they provide for`_BufferedReaderStream`
https://github.com/python/typeshed/issues/15311

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
