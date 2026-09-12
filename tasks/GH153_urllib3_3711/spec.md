# GH153_urllib3_3711: Improve speed of `BytesQueueBuffer.get()` by using memoryview — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/urllib3/urllib3/issues/3710
- Repo: https://github.com/urllib3/urllib3

## Issue Description

### Subject

`BytesQueueBuffer.get()` is slow when downloading gzipped, unchunked data.

By profiling with `line_profiler`, I identified the slowest part in the `BytesQueueBuffer.get()`, specifically the following line:
https://github.com/urllib3/urllib3/blob/b20c8368ec02421ecc4e49d796cd5eff1e04f325/src/urllib3/response.py#L259

### Environment

```
OS Linux-6.12.48-1-MANJARO-x86_64-with-glibc2.42
Python 3.12.5
OpenSSL 3.0.14 4 Jun 2024
urllib3 0.1.dev4309
```

I also confirmed this with python 3.14.

As this is a performance issue, I will put the CPU and memory info just in case:
```
CPU: 13th Gen Intel(R) Core(TM) i5-13500

> free
               total        used        free      shared  buff/cache   available
Mem:           31833       11164       15246        1254        7134       20669
Swap:              0           0           0
```

### Steps to Reproduce

1. Clone https://gist.github.com/phenylshima/0af2d0692db455d2d040805289689fef
2. Install `urllib3==2.5.0`, `fastapi==0.121.1`, and `uvicorn==0.38.0`
3. Start test_server.py
4. Run test_client.py, and check the "Content retrieval time" line.

### Expected Behavior

The two "Content retrieval time" are almost the same.

### Actual Behavior

Content retrieval time is about 9x slower when decode_content=True, compared to taking the whole data with decode_content=False and then unzipping.

```
Response time: 0.001905202865600586 seconds
Content retrieval time: 2.0758426189422607 seconds
Response time: 0.0009431838989257812 seconds
Content retrieval and decompression time: 0.2243025302886963 seconds
```

### Profiling

I think this result contains significant overhead associated with line_profiler, but it shows that the aforementioned line is taking considerably longer time than others.

<details>
<summary>line_profiler result</summary>

```python
Timer unit: 1e-06 s

Total time: 2.37476 s
File: /home/user/0af2d0692db455d2d040805289689fef/.venv/lib/python3.12/site-packages/urllib3/response.py
Function: BytesQueueBuffer.get at line 282

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   282                                               @line_profiler.profile
   283                                               def get(self, n: int) -> bytes:
   284    134218      39514.2      0.3      1.7          if n == 0:
   285                                                       return b""
   286    134218      40398.6      0.3      1.7          elif not self.buffer:
   287                                                       raise RuntimeError("buffer is empty")
   288    134218      38182.3      0.3      1.6          elif n < 0:
   289                                                       raise ValueError("n should be > 0")
   290                                           
   291    134218      37615.7      0.3      1.6          fetched = 0
   292    134218      49670.3      0.4      2.1          ret = io.BytesIO()
   293    134361      39164.8      0.3      1.6          while fetched < n:
   294    134361      38041.0      0.3      1.6              remaining = n - fetched
   295    134361      38083.3      0.3      1.6              chunk = self.buffer.popleft()
   296    134361      38311.4      0.3      1.6              chunk_length = len(chunk)
   297    134361      34412.0      0.3      1.4              if remaining < chunk_length:
   298    134217    1740781.8     13.0     73.3                  left_chunk, right_chunk = chunk[:remaining], chunk[remaining:]
   299    134217      57110.2      0.4      2.4                  ret.write(left_chunk)
   300    134217      39958.4      0.3      1.7                  self.buffer.appendleft(right_chunk)
   301    134217      38834.6      0.3      1.6                  self._size -= remaining
   302    134217      35020.9      0.3      1.5                  break
   303                                                       else:
   304       144         80.0      0.6      0.0                  ret.write(chunk)
   305       144         49.4      0.3      0.0                  self._size -= chunk_length
   306       144         44.4      0.3      0.0              fetched += chunk_length
   307                                           
   308       144         39.9      0.3      0.0              if not self.buffer:
   309         1          0.3      0.3      0.0                  break
   310                                           
   311    134218      69447.3      0.5      2.9          return ret.getvalue()

Total time: 4.33477 s
File: /home/user/0af2d0692db455d2d040805289689fef/.venv/lib/python3.12/site-packages/urllib3/response.py
Function: HTTPResponse.stream at line 1071

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1071                                               @line_profiler.profile
  1072                                               def stream(
  1073                                                   self, amt: int | None = 2**16, decode_content: bool | None = None
  1074                                               ) -> typing.Generator[bytes]:
  1075                                                   """
  1076                                                   A generator wrapper for the read() method. A call will block until
  1077                                                   ``amt`` bytes have been read from the connection or until the
  1078                                                   connection is closed.
  1079                                           
  1080                                                   :param amt:
  1081                                                       How much of the content to read. The generator will return up to
  1082                                                       much data per iteration, but may return less. This is particularly
  1083                                                       likely when using compressed data. However, the empty string will
  1084                                                       never be returned.
  1085                                           
  1086                                                   :param decode_content:
  1087                                                       If True, will attempt to decode the body based on the
  1088                                                       'content-encoding' header.
  1089                                                   """
  1090         1          0.9      0.9      0.0          if self.chunked and self.supports_chunked_reads():
  1091                                                       yield from self.read_chunked(amt, decode_content=decode_content)
  1092                                                   else:
  1093    134219     206651.4      1.5      4.8              while not is_fp_closed(self._fp) or len(self._decoded_buffer) > 0:
  1094    134218    4038064.2     30.1     93.2                  data = self.read(amt=amt, decode_content=decode_content)
  1095                                           
  1096    134218      38546.2      0.3      0.9                  if data:
  1097    134218      51505.8      0.4      1.2                      yield data

  2.37 seconds - /home/user/0af2d0692db455d2d040805289689fef/.venv/lib/python3.12/site-packages/urllib3/response.py:282 - BytesQueueBuffer.get
  4.33 seconds - /home/user/0af2d0692db455d2d040805289689fef/.venv/lib/python3.12/site-packages/urllib3/response.py:1071 - HTTPResponse.stream
```

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

FYI, we did further improvements in c19571de34c47de3a766541b041637ba5f716ed7.

Benchmarks for the following script reading 32 KiB chunks of a 1 GiB response

```python
from compression import zstd
import io
import timeit

from urllib3.response import HTTPResponse

data = b"A" * (1024 * 1024 * 1024)  # 1 GB
compressed_data = zstd.ZstdCompressor().compress(data)

def decompress():
    fp = io.BytesIO(compressed_data)
    r = HTTPResponse(fp, headers={"content-encoding": "zstd"}, preload_content=False)
    while r.read(32 * 1024):
        pass

time_taken = timeit.timeit(decompress, number=10)
print(f"Decompression time: {time_taken:.2f} seconds")
```

Results:
* Before 18af0a10efc4c99dd028f7ad5a461470b9a8b0fd – even one `decompress()` call did not finish under a minute. It decompressed 1 GB during the first `read` call and then `BytesQueueBuffer.get` was splitting chunks by creating copies of the data which was extremely slow.
* 18af0a10efc4c99dd028f7ad5a461470b9a8b0fd – 13.69 seconds for ten `decompress()` calls
* c19571de34c47de3a766541b041637ba5f716ed7 – 0.66 seconds for ten `decompress()` calls

## PR Review Comments

**[user]** on `src/urllib3/response.py`:

data will only be bytes then, right?

**[user]** on `src/urllib3/response.py`:

It can be memoryview. In line 259, the existing chunk is converted to memoryview, and in line 262, the memoryview is written back to the buffer. Therefore, the buffer can have both bytes and memoryview.

The get and get_all methods are written so that, if the memoryview is in the buffer, it will be converted to bytes.

**[user]** on `test/test_response.py`:

The tests that assert on the time delta might be a bit fragile across different environments. Machines with different performance characteristics can cause these timing-based tests to pass or fail inconsistently.

The patched version does clearly improve performance, though: on my machine `TestBytesQueueBuffer.test_performance_single_chunk[get]` shows that it allocates almost half as much memory. Would it make sense to rely on this and add an explicit test that checks the memory allocation instead of the timing-based tests?

**[user]** on `src/urllib3/response.py`:

Since line 262 calls `self.buffer.appendleft`, `BytesQueueBuffer.put` is never called with a memory view, right?

**[user]** on `src/urllib3/response.py`:

Yeah, right. My initial intention was that "maybe allowing memoryview here could benefit someone", but on my second thought, I removed the `memoryview[bytes]`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
