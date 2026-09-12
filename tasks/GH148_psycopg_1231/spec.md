# GH148_psycopg_1231: fix: adapters: avoid race condition when replacing class name with itself — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/1230
- Repo: https://github.com/psycopg/psycopg

## Issue Description

We've noticed these at program startup when using multiple threads:

```
psycopg.ProgrammingError: cannot adapt type 'UUID' using placeholder '%s' (format: AUTO)
```

My guess is that the code in https://github.com/psycopg/psycopg/blob/6a24300ad2392e502a7c9d3c244ead6852890d90/psycopg/psycopg/_adapters_map.py#L218-L223 is not thread-safe, as `dmap[scls] = dmap.pop(fqn)` is not atomic.

To reproduce:

```
% mkdir /tmp/psycopg-adapter-get-dumper-race; cd /tmp/psycopg-adapter-get-dumper-race
% python3.13 -m venv venv
% venv/bin/pip install --quiet --force ~/src/psycopg/psycopg ~/src/psycopg/psycopg_c 
% cat <<EOF > race_get_dumper_uuid.py
import sys
import threading
import uuid

import psycopg

def test_uuid_adapter() -> bool:
    conn = psycopg.connect()
    res = conn.execute("select gen_random_uuid() = %s", [uuid.uuid4()]).fetchone()[0]

if __name__ == "__main__":
    sys.setswitchinterval(0.00001)

    threads = [threading.Thread(target=test_uuid_adapter) for _ in range(5)]
    for t in threads:
        t.start()

    for t in threads:
        t.join()
EOF
% pg_virtualenv 
Creating new PostgreSQL cluster 18/regress ...
% while ./venv/bin/python race_get_dumper_uuid.py; do : ; done ; # wait a few seconds / minutes
Exception in thread Thread-4 (test_uuid_adapter):
Traceback (most recent call last):
  File "/usr/lib/python3.13/threading.py", line 1043, in _bootstrap_inner
    self.run()
    ~~~~~~~~^^
  File "/usr/lib/python3.13/threading.py", line 994, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/psycopg-adapter-get-dumper-race/race_get_dumper_uuid.py", line 10, in test_uuid_adapter
    res = conn.execute("select gen_random_uuid() = %s", [uuid.uuid4()]).fetchone()[0]
          ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/psycopg-adapter-get-dumper-race/venv/lib/python3.13/site-packages/psycopg/connection.py", line 299, in execute
    raise ex.with_traceback(None)
psycopg.ProgrammingError: cannot adapt type 'UUID' using placeholder '%s' (format: AUTO)
```

(I'm using `sys.setswitchinterval` here to try and trigger the bug faster)

## PR Review Comments

**[user]** on `docs/news.rst`:

This will go in 3.3.2

**[user]** on `docs/news.rst`:

Obviously, that's my bad ! Thanks for the quick review; I moved this into its own new 3.3.2 section.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
