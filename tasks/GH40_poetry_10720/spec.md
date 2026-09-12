# GH40_poetry_10720: Fix non-deterministic dependency constraint ordering in lock file — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/python-poetry/poetry/issues/10702
- Repo: https://github.com/python-poetry/poetry

## Issue Description

### Description

Consecutive runs of `poetry install` after `poetry update` change markers or versions restriction order in a non-consequential way.
This also seems to reproduce when running `install` across different Linux distributions and machines, as well as with the update-install sequence on the same machine.

Ex:

```
[[package]]
name = "google-api-core"
version = "2.29.0"
...
[package.dependencies]
proto-plus = [
    + {version = ">=1.22.3,<2.0.0"},
    {version = ">=1.25.0,<2.0.0", markers = "python_version >= \"3.13\""},
    - {version = ">=1.22.3,<2.0.0"},
]
```

```
description = "Fast implementation of asyncio event loop on top of libuv"
optional = false
python-versions = ">=3.8.1"
groups = ["main"]
- markers = "sys_platform != \"win32\" and sys_platform != \"cygwin\" and platform_python_implementation != \"PyPy\""
+ markers = "platform_python_implementation != \"PyPy\" and sys_platform != \"win32\" and sys_platform != \"cygwin\""
```

The first reordering occurred in Poetry 2.2.1. I did not see the second one before upgrading to 2.3.1.

This issue is especially disruptive with Coding Agents, especially cloud-deployed ones like GitHub Copilot, because it creates unnecessary noise in the pull requests.

It would be great if this issue could be mitigated by deterministic ordering of markers and version ranges by hash or lexicographically.

### Workarounds

Adding .lock files to .gitignore and committing them only when needed.

### Poetry Installation Method

pip

### Operating System

Ubuntu 25.10

### Poetry Version

Poetry (version 2.3.1)

### Poetry Configuration

```bash session
cache-dir = "/home/dmitry/.cache/pypoetry"
data-dir = "/home/dmitry/.local/share/pypoetry"
installer.max-workers = null
installer.no-binary = null
installer.only-binary = null
installer.parallel = true
installer.re-resolve = false
keyring.enabled = true
python.installation-dir = "{data-dir}/python"
requests.max-retries = 0
solver.lazy-wheel = true
system-git-client = false
virtualenvs.create = true
virtualenvs.in-project = null
virtualenvs.options.always-copy = false
virtualenvs.options.no-pip = false
virtualenvs.options.system-site-packages = false
virtualenvs.path = "{cache-dir}/virtualenvs"
virtualenvs.prompt = "{project_name}-py{python_version}"
virtualenvs.use-poetry-python = false
```

### Python Sysconfig

<details>
  <summary>sysconfig.log</summary>
  <!-- Please leave one blank line below for enabling the code block rendering. -->

  ```
  Paste the output of 'python -m sysconfig', over this line.
  ```
</details>

### Example pyproject.toml

```TOML
[tool.poetry]
name = "adk-chat-demo"
version = "0.1.0"
readme = ""

[tool.poetry.dependencies]
python = ">=3.12,<3.14"
google-adk = "1.23.0"

[tool.poetry.group.dev.dependencies]
ruff = "0.14.13"

[tool.pytest.ini_options]
pythonpath = [
    "src/"
]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Also find two lock files attached:
The [poetry.lock.zip](https://github.com/user-attachments/files/24848443/poetry.lock.zip) was produced by poetry 2.2.1 during `poetry update`, and [poetry_install.lock.zip](https://github.com/user-attachments/files/24848421/poetry_install.lock.zip) includes modifications that an immediate follow-up `poetry install` does.

### Poetry Runtime Logs

<details>
  <summary>poetry-runtime.log</summary>
  <!-- Please leave one blank line below for enabling the code block rendering. -->

  ```
  Paste the output of 'poetry -vvv <command>', over this line.
  ```
</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

You didn't provide the details that the issue template asks for.  Please give a way to reproduce.

### Comment 2 ([user]):

[user] Unfortunately, I do not have a reproduction to submit, as I don't exactly see a pattern in such reorderings. They seem to happen as one-offs rather than be stable and reproducible. Feel free to close the issue if this isn't enough information to determine how it may be happening. 
I will reopen with additional details when I'm able to capture them.

### Comment 3 ([user]):

You could look for places to add `sorted(...)` eg [here](https://github.com/python-poetry/poetry/blob/4a8031f646b2bcca7f616a5c1c7a46ae172fa0c3/src/poetry/packages/locker.py#L619) looks plausible.

But if you can't reproduce a problem it's going to be hard to tell whether you've fixed anything.

### Comment 4 ([user]):

[user] I was able to reproduce the issue on poetry 2.2.1. But I observed similar behavior with 2.3.1 with the same kind of reorderings.
I added a project .toml file and two corresponding lock files: 
- one produced by `poetry update` after changing a dependency version (new dependency version is in .toml)
- another produced by an immediate follow-up `poetry install`

Please let me know if it's not enough. I can also provide the state of the .toml and lock files before the dependency version was upgraded and `poetry update` was called.

### Comment 5 ([user]):

This issue has been automatically locked since there has not been any recent activity after it was closed. Please open a new issue for related bugs.

## PR Review Comments

**[user]** on `src/poetry/packages/locker.py`:

sorting is probably better achieved at line 524
```
          for dependency in sorted(
              package.requires,
              key=lambda d: d.name,
          ):
```
Seems unlikely that `optional` should be used - its likely a bug if the same dependency appears as both optional and not optional

**[user]** on `src/poetry/packages/locker.py`:

Thanks [user], good call. I've simplified the sort key to just `(name, marker)` — removed `pretty_constraint` from the tuple. This keeps deterministic ordering for same-name deps with different markers (the actual issue) without unnecessarily reordering entries that differ only by version/optional status. The mixed-types test now preserves its original insertion order.

**[user]** on `tests/packages/test_locker.py`:

```suggestion
    name and marker to ensure deterministic lock file output
```

**[user]** on `tests/packages/test_locker.py`:

Fixed, thanks for catching that.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
