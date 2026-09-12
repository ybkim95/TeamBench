# GH23_poetry_10721: Validate package names in poetry update command — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/python-poetry/poetry/issues/10422
- Repo: https://github.com/python-poetry/poetry

## Issue Description

### Description

`poetry update` will happily accept any and all names given to it with no complaints, even if they're not declared dependencies of the current project. This is very confusing, as it makes it look like an action succeeded if a mistake or typo sneaks in, when in reality it had no effect.

Example:

```
$ poetry update none of this is a real package
Updating dependencies
Resolving dependencies... (0.3s)

No dependencies to install or update
```

This also means it's not possible to request an update of a dependency to a specific version, because it will simply be taken as a non-existent dependency name and ignored, rather than a name + version:

```
$ poetry update "example==0.2.0"
Updating dependencies
Resolving dependencies... (0.5s)

No dependencies to install or update
```

 The user thus has no way to influence the locking decisions being made, and is entirely at the mercy of what happens to be in the available indices at the instant the command was run. Being able to control what version is being locked to is very important for the infrequent, but critical case when a specific dependency's latest release is broken, and a temporary override to an older version is required. Currently, it seems there's no way to do it, short of changing the declared dependency version via the `add` command, which should not be required.

### Workarounds

No.

### Poetry Installation Method

pipx

### Operating System

Ubuntu 24.04

### Poetry Version

Poetry (version 2.1.3)

### Poetry Configuration

```bash session
cache-dir = "/home/mkatafiasz/.cache/pypoetry"
data-dir = "/home/mkatafiasz/.local/share/pypoetry"
installer.max-workers = null
installer.no-binary = null
installer.only-binary = null
installer.parallel = true
installer.re-resolve = true
keyring.enabled = true
python.installation-dir = "{data-dir}/python"  # /home/mkatafiasz/.local/share/pypoetry/python
repositories.artifactory.url = "https://private/artifactory/api/pypi/repo"
requests.max-retries = 0
solver.lazy-wheel = true
system-git-client = false
virtualenvs.create = true
virtualenvs.in-project = null
virtualenvs.options.always-copy = false
virtualenvs.options.no-pip = false
virtualenvs.options.system-site-packages = false
virtualenvs.path = "{cache-dir}/virtualenvs"  # /home/mkatafiasz/.cache/pypoetry/virtualenvs
virtualenvs.prompt = "{project_name}-py{python_version}"
virtualenvs.use-poetry-python = false
```

### Python Sysconfig

_No response_

### Example pyproject.toml

```TOML

```

### Poetry Runtime Logs

<details>
  <summary>poetry-runtime.log</summary>
  <!-- Please leave one blank line below for enabling the code block rendering. -->

  ```$ poetry -vvvv update this is not a real package
Loading configuration file /home/mkatafiasz/.config/pypoetry/config.toml
Loading configuration file /home/mkatafiasz/.config/pypoetry/auth.toml
Adding repository artifactory (https://mkatafiasz:xxxx@private/artifactory/api/pypi/repo/simple) and setting it as supplemental
Using virtualenv: /home/mkatafiasz/.cache/pypoetry/virtualenvs/example-supervisor-8QUTkN6H-py3.12
Checking keyring availability: Checking if keyring is available
[keyring:keyring.backend] Loading KWallet
[keyring:keyring.backend] Loading SecretService
[keyring:keyring.backend] Loading Windows
[keyring:keyring.backend] Loading chainer
[keyring:keyring.backend] Loading libsecret
[keyring:keyring.backend] Loading macOS
Using keyring backend 'SecretService Keyring'
Available
Updating dependencies
Resolving dependencies...
   1: fact: example-supervisor is 0.2.0
   1: derived: example-supervisor
   1: fact: example-supervisor depends on fastapi[standard] (>=0.115.12,<0.116.0)
   1: fact: example-supervisor depends on click (<8.2.0)
   1: fact: example-supervisor depends on example-worker (>=0.1.0,<0.2.0)
   1: fact: example-supervisor depends on pytest (^8.3.5)
   1: fact: example-supervisor depends on pytest-testinfra (^10.2.2)
   1: fact: example-supervisor depends on pyro5 (^5.15)
   1: fact: example-supervisor depends on trio (^0.30.0)
   1: fact: example-supervisor depends on neo-sockpuppet (^0.2.0)
   1: selecting example-supervisor (0.2.0)
   1: derived: neo-sockpuppet (>=0.2.0,<0.3.0)
   1: derived: trio (>=0.30.0,<0.31.0)
   1: derived: pyro5 (>=5.15,<6.0)
   1: derived: pytest-testinfra (>=10.2.2,<11.0.0)
   1: derived: pytest (>=8.3.5,<9.0.0)
   1: derived: example-worker (>=0.1.0,<0.2.0)
   1: derived: click (<8.2.0)
   1: derived: fastapi[standard] (>=0.115.12,<0.116.0)
Source (PyPI): Getting info for neo-sockpuppet (0.2.0) from PyPI
Creating new session for pypi.org
[urllib3:urllib3.connectionpool] Starting new HTTPS connection (1): pypi.org:443
[urllib3:urllib3.connectionpool] https://pypi.org:443 "GET /pypi/neo-sockpuppet/0.2.0/json HTTP/1.1" 404 24
   1: fact: neo-sockpuppet (0.2.0) depends on anycorn (>=0.18.1,<0.19.0)
   1: fact: neo-sockpuppet (0.2.0) depends on anyio (>=4.9.0,<5.0.0)
   1: fact: neo-sockpuppet (0.2.0) depends on pyro5 (>=5.15,<6.0)
   1: selecting neo-sockpuppet (0.2.0)
   1: derived: anyio (>=4.9.0,<5.0.0)
   1: derived: anycorn (>=0.18.1,<0.19.0)
   1: fact: anycorn (0.18.1) depends on anyio (>=4.0,<5.0)
   1: fact: anycorn (0.18.1) depends on exceptiongroup (>=1.1.0,<2.0)
   1: fact: anycorn (0.18.1) depends on h11 (*)
   1: fact: anycorn (0.18.1) depends on h2 (>=3.1.0)
   1: fact: anycorn (0.18.1) depends on hpack (*)
   1: fact: anycorn (0.18.1) depends on priority (*)
   1: fact: anycorn (0.18.1) depends on rich-click (>=1.8.3,<2.0.0)
   1: fact: anycorn (0.18.1) depends on tomli (*)
   1: fact: anycorn (0.18.1) depends on typing-extensions (*)
   1: fact: anycorn (0.18.1) depends on wsproto (>=0.14.0)
   1: selecting anycorn (0.18.1)
   1: derived: wsproto (>=0.14.0)
   1: derived: typing-extensions
   1: derived: tomli
   1: derived: rich-click (>=1.8.3,<2.0.0)
   1: derived: priority
   1: derived: hpack
   1: derived: h2 (>=3.1.0)
   1: derived: h11
   1: derived: exceptiongroup (>=1.1.0,<2.0)
Source (PyPI): Getting info for example-worker (0.1.0) from PyPI
[urllib3:urllib3.connectionpool] https://pypi.org:443 "GET /pypi/example-worker/0.1.0/json HTTP/1.1" 404 24
   1: fact: example-worker (0.1.0) depends on click (<8.2.0)
   1: fact: example-worker (0.1.0) depends on fastapi[standard] (>=0.115.12,<0.116.0)
   1: selecting example-worker (0.1.0)
   1: fact: fastapi[standard] (0.115.12) depends on fastapi (0.115.12)
   1: fact: fastapi[standard] (0.115.12) depends on starlette (>=0.40.0,<0.47.0)
   1: fact: fastapi[standard] (0.115.12) depends on pydantic (>=1.7.4,<1.8 || >1.8,<1.8.1 || >1.8.1,<2.0.0 || >2.0.0,<2.0.1 || >2.0.1,<2.1.0 || >2.1.0,<3.0.0)
   1: fact: fastapi[standard] (0.115.12) depends on typing-extensions (>=4.8.0)
   1: fact: fastapi[standard] (0.115.12) depends on fastapi-cli[standard] (>=0.0.5)
   1: fact: fastapi[standard] (0.115.12) depends on httpx (>=0.23.0)
   1: fact: fastapi[standard] (0.115.12) depends on jinja2 (>=3.1.5)
   1: fact: fastapi[standard] (0.115.12) depends on python-multipart (>=0.0.18)
   1: fact: fastapi[standard] (0.115.12) depends on email-validator (>=2.0.0)
   1: fact: fastapi[standard] (0.115.12) depends on uvicorn[standard] (>=0.12.0)
   1: selecting fastapi[standard] (0.115.12)
   1: derived: uvicorn[standard] (>=0.12.0)
   1: derived: email-validator (>=2.0.0)
   1: derived: python-multipart (>=0.0.18)
   1: derived: jinja2 (>=3.1.5)
   1: derived: httpx (>=0.23.0)
   1: derived: fastapi-cli[standard] (>=0.0.5)
   1: derived: typing-extensions (>=4.8.0)
   1: derived: pydantic (>=1.7.4,!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0)
   1: derived: starlette (>=0.40.0,<0.47.0)
   1: derived: fastapi (==0.115.12)
   1: fact: h2 (4.2.0) depends on hyperframe (>=6.1,<7)
   1: fact: h2 (4.2.0) depends on hpack (>=4.1,<5)
   1: selecting h2 (4.2.0)
   1: derived: hpack (>=4.1,<5)
   1: derived: hyperframe (>=6.1,<7)
   1: fact: fastapi (0.115.12) depends on starlette (>=0.40.0,<0.47.0)
   1: fact: fastapi (0.115.12) depends on pydantic (>=1.7.4,<1.8 || >1.8,<1.8.1 || >1.8.1,<2.0.0 || >2.0.0,<2.0.1 || >2.0.1,<2.1.0 || >2.1.0,<3.0.0)
   1: fact: fastapi (0.115.12) depends on typing-extensions (>=4.8.0)
   1: selecting fastapi (0.115.12)
   1: fact: pytest (8.3.5) depends on colorama (*)
   1: fact: pytest (8.3.5) depends on exceptiongroup (>=1.0.0rc8)
   1: fact: pytest (8.3.5) depends on iniconfig (*)
   1: fact: pytest (8.3.5) depends on packaging (*)
   1: fact: pytest (8.3.5) depends on pluggy (>=1.5,<2)
   1: fact: pytest (8.3.5) depends on tomli (>=1)
   1: selecting pytest (8.3.5)
   1: derived: tomli (>=1)
   1: derived: pluggy (>=1.5,<2)
   1: derived: packaging
   1: derived: iniconfig
   1: derived: colorama
   1: fact: wsproto (1.2.0) depends on h11 (>=0.9.0,<1)
   1: selecting wsproto (1.2.0)
   1: derived: h11 (>=0.9.0,<1)
   1: fact: httpx (0.28.1) depends on anyio (*)
   1: fact: httpx (0.28.1) depends on certifi (*)
   1: fact: httpx (0.28.1) depends on httpcore (==1.*)
   1: fact: httpx (0.28.1) depends on idna (*)
   1: selecting httpx (0.28.1)
   1: derived: idna
   1: derived: httpcore (==1.*)
   1: derived: certifi
   1: fact: pydantic (2.11.4) depends on annotated-types (>=0.6.0)
   1: fact: pydantic (2.11.4) depends on pydantic-core (2.33.2)
   1: fact: pydantic (2.11.4) depends on typing-extensions (>=4.12.2)
   1: fact: pydantic (2.11.4) depends on typing-inspection (>=0.4.0)
   1: selecting pydantic (2.11.4)
   1: derived: typing-inspection (>=0.4.0)
   1: derived: typing-extensions (>=4.12.2)
   1: derived: pydantic-core (==2.33.2)
   1: derived: annotated-types (>=0.6.0)
   1: fact: starlette (0.46.2) depends on anyio (>=3.6.2,<5)
   1: selecting starlette (0.46.2)
   1: fact: trio (0.30.0) depends on attrs (>=23.2.0)
   1: fact: trio (0.30.0) depends on sortedcontainers (*)
   1: fact: trio (0.30.0) depends on idna (*)
   1: fact: trio (0.30.0) depends on outcome (*)
   1: fact: trio (0.30.0) depends on sniffio (>=1.3.0)
   1: fact: trio (0.30.0) depends on cffi (>=1.14)
   1: fact: trio (0.30.0) depends on exceptiongroup (*)
   1: selecting trio (0.30.0)
   1: derived: cffi (>=1.14)
   1: derived: sniffio (>=1.3.0)
   1: derived: outcome
   1: derived: sortedcontainers
   1: derived: attrs (>=23.2.0)
   1: fact: pyro5 (5.15) depends on serpent (>=1.41)
   1: selecting pyro5 (5.15)
   1: derived: serpent (>=1.41)
   1: fact: pytest-testinfra (10.2.2) depends on pytest (>=6)
   1: selecting pytest-testinfra (10.2.2)
   1: fact: click (8.1.8) depends on colorama (*)
   1: selecting click (8.1.8)
   1: derived: colorama
   1: fact: anyio (4.9.0) depends on exceptiongroup (>=1.0.2)
   1: fact: anyio (4.9.0) depends on idna (>=2.8)
   1: fact: anyio (4.9.0) depends on sniffio (>=1.1)
   1: fact: anyio (4.9.0) depends on typing_extensions (>=4.5)
   1: selecting anyio (4.9.0)
   1: derived: typing_extensions (>=4.5)
   1: derived: idna (>=2.8)
   1: fact: rich-click (1.8.9) depends on click (>=7)
   1: fact: rich-click (1.8.9) depends on rich (>=10.7)
   1: fact: rich-click (1.8.9) depends on typing_extensions (>=4)
   1: selecting rich-click (1.8.9)
   1: derived: rich (>=10.7)
   1: fact: rich (14.0.0) depends on typing-extensions (>=4.0.0,<5.0)
   1: fact: rich (14.0.0) depends on pygments (>=2.13.0,<3.0.0)
   1: fact: rich (14.0.0) depends on markdown-it-py (>=2.2.0)
   1: selecting rich (14.0.0)
   1: derived: markdown-it-py (>=2.2.0)
   1: derived: pygments (>=2.13.0,<3.0.0)
   1: derived: typing-extensions (>=4.0.0,<5.0)
   1: fact: markdown-it-py (3.0.0) depends on mdurl (>=0.1,<1.0)
   1: selecting markdown-it-py (3.0.0)
   1: derived: mdurl (>=0.1,<1.0)
   1: fact: exceptiongroup (1.3.0) depends on typing-extensions (>=4.6.0)
   1: selecting exceptiongroup (1.3.0)
   1: derived: typing-extensions (>=4.6.0)
   1: fact: uvicorn[standard] (0.34.2) depends on uvicorn (0.34.2)
   1: fact: uvicorn[standard] (0.34.2) depends on click (>=7.0)
   1: fact: uvicorn[standard] (0.34.2) depends on h11 (>=0.8)
   1: fact: uvicorn[standard] (0.34.2) depends on typing-extensions (>=4.0)
   1: fact: uvicorn[standard] (0.34.2) depends on colorama (>=0.4)
   1: fact: uvicorn[standard] (0.34.2) depends on httptools (>=0.6.3)
   1: fact: uvicorn[standard] (0.34.2) depends on python-dotenv (>=0.13)
   1: fact: uvicorn[standard] (0.34.2) depends on pyyaml (>=5.1)
   1: fact: uvicorn[standard] (0.34.2) depends on uvloop (>=0.14.0,<0.15.0 || >0.15.0,<0.15.1 || >0.15.1)
   1: fact: uvicorn[standard] (0.34.2) depends on watchfiles (>=0.13)
   1: fact: uvicorn[standard] (0.34.2) depends on websockets (>=10.4)
   1: selecting uvicorn[standard] (0.34.2)
   1: derived: websockets (>=10.4)
   1: derived: watchfiles (>=0.13)
   1: derived: uvloop (>=0.14.0,!=0.15.0,!=0.15.1)
   1: derived: pyyaml (>=5.1)
   1: derived: python-dotenv (>=0.13)
   1: derived: httptools (>=0.6.3)
   1: derived: colorama (>=0.4)
   1: derived: typing-extensions (>=4.0)
   1: derived: uvicorn (==0.34.2)
   1: fact: email-validator (2.2.0) depends on dnspython (>=2.0.0)
   1: fact: email-validator (2.2.0) depends on idna (>=2.0.0)
   1: selecting email-validator (2.2.0)
   1: derived: dnspython (>=2.0.0)
   1: fact: jinja2 (3.1.6) depends on MarkupSafe (>=2.0)
   1: selecting jinja2 (3.1.6)
   1: derived: MarkupSafe (>=2.0)
   0: Duplicate dependencies for uvicorn
   0: Merging requirements for uvicorn
   1: fact: fastapi-cli[standard] (0.0.7) depends on fastapi-cli (0.0.7)
   1: fact: fastapi-cli[standard] (0.0.7) depends on typer (>=0.12.3)
   1: fact: fastapi-cli[standard] (0.0.7) depends on uvicorn[standard] (>=0.15.0)
   1: fact: fastapi-cli[standard] (0.0.7) depends on rich-toolkit (>=0.11.1)
   1: selecting fastapi-cli[standard] (0.0.7)
   1: derived: rich-toolkit (>=0.11.1)
   1: derived: uvicorn[standard] (>=0.15.0)
   1: derived: typer (>=0.12.3)
   1: derived: fastapi-cli (==0.0.7)
   1: fact: httpcore (1.0.9) depends on certifi (*)
   1: fact: httpcore (1.0.9) depends on h11 (>=0.16)
   1: selecting httpcore (1.0.9)
   1: derived: h11 (>=0.16)
   1: fact: typing-inspection (0.4.1) depends on typing-extensions (>=4.12.0)
   1: selecting typing-inspection (0.4.1)
   1: fact: pydantic-core (2.33.2) depends on typing-extensions (>=4.6.0,<4.7.0 || >4.7.0)
   1: selecting pydantic-core (2.33.2)
   1: fact: cffi (1.17.1) depends on pycparser (*)
   1: selecting cffi (1.17.1)
   1: derived: pycparser
   1: fact: outcome (1.3.0.post0) depends on attrs (>=19.2.0)
   1: selecting outcome (1.3.0.post0)
   1: fact: watchfiles (1.0.5) depends on anyio (>=3.0.0)
   1: selecting watchfiles (1.0.5)
   1: fact: uvicorn (0.34.2) depends on click (>=7.0)
   1: fact: uvicorn (0.34.2) depends on h11 (>=0.8)
   1: fact: uvicorn (0.34.2) depends on typing-extensions (>=4.0)
   1: selecting uvicorn (0.34.2)
   1: derived: typing-extensions (>=4.0)
   1: fact: rich-toolkit (0.14.6) depends on click (>=8.1.7)
   1: fact: rich-toolkit (0.14.6) depends on rich (>=13.7.1)
   1: fact: rich-toolkit (0.14.6) depends on typing-extensions (>=4.12.2)
   1: selecting rich-toolkit (0.14.6)
   1: fact: typer (0.15.3) depends on click (>=8.0.0)
   1: fact: typer (0.15.3) depends on typing-extensions (>=3.7.4.3)
   1: fact: typer (0.15.3) depends on shellingham (>=1.3.0)
   1: fact: typer (0.15.3) depends on rich (>=10.11.0)
   1: selecting typer (0.15.3)
   1: derived: shellingham (>=1.3.0)
   1: fact: fastapi-cli (0.0.7) depends on typer (>=0.12.3)
   1: fact: fastapi-cli (0.0.7) depends on uvicorn[standard] (>=0.15.0)
   1: fact: fastapi-cli (0.0.7) depends on rich-toolkit (>=0.11.1)
   1: selecting fastapi-cli (0.0.7)
   1: selecting typing-extensions (4.13.2)
   1: selecting tomli (2.2.1)
   1: selecting priority (2.0.0)
   1: selecting hpack (4.1.0)
   1: selecting h11 (0.16.0)
   1: selecting python-multipart (0.0.20)
   1: selecting hyperframe (6.1.0)
   1: selecting pluggy (1.6.0)
   1: selecting packaging (25.0)
   1: selecting iniconfig (2.1.0)
   1: selecting colorama (0.4.6)
   1: selecting idna (3.10)
   1: selecting certifi (2025.4.26)
   1: selecting annotated-types (0.7.0)
   1: selecting sniffio (1.3.1)
   1: selecting sortedcontainers (2.4.0)
   1: selecting attrs (25.3.0)
   1: selecting serpent (1.41)
   1: selecting pygments (2.19.1)
   1: selecting mdurl (0.1.2)
   1: selecting websockets (15.0.1)
   1: selecting uvloop (0.21.0)
   1: selecting pyyaml (6.0.2)
   1: selecting python-dotenv (1.1.0)
   1: selecting httptools (0.6.4)
   1: selecting dnspython (2.7.0)
   1: selecting markupsafe (3.0.2)
   1: selecting pycparser (2.22)
   1: selecting shellingham (1.5.4)
   1: Version solving took 0.293 seconds.
   1: Tried 1 solutions.

Finding the necessary packages for the current system

No dependencies to install or update
  ```
</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Per the docs

> Note that this will not update versions for dependencies outside their [version constraints](https://python-poetry.org/docs/dependency-specification/#version-constraints) specified in the pyproject.toml file. In other terms, poetry update foo will be a no-op if the version constraint specified for foo is ~2.3 or 2.3 and 2.4 is available. In order for foo to be updated, you must update the constraint, for example ^2.3. You can do this using the add command

Why not use `poetry add`?  Why would it be an improvement for `poetry update` to do what `poetry add` already does?

### Comment 2 ([user]):

[user]: mostly because I would expect the command called `update` to allow me to update the dependencies :) And specifically, there needs to be a way to tell it to update *the resolution* to a specific version (i.e. what gets written to `poetry.lock`), independent of the project constraints that `add` manages. This is useful for all kinds of scenarios, including workaround for broken upstream releases, testing, etc. These are not super frequent needs individually, but they're frequent enough, and critical when you need them.

### Comment 3 ([user]):

the way to direct the resolution to a particular solution is to update the constraints in pyproject.toml (eg but not necessarily through `poetry add`).  I do not think it is likely that your proposed side-channel will be implemented.

### Comment 4 ([user]):

[user]: but there's a difference between dependency constraints (which are contained by `pyproject.toml` and mainly controlled by `poetry add`), and the concrete dependency resolution (which is contained by `poetry.lock` and controlled by `poetry update`). That is a pretty clear and unambiguous model, but if messing with the constraints is the only way to influence the resolution, that contradicts the basic concepts of the model in a pretty severe way. Not having any way to control the resolution and instead having it drift arbirtarily from run to run of `poetry update`, based purely on what happens to be in the index at the time, with no way for the user to exert influence on it, also feels very counter to the idea that the dependency resolution should be the tool for the user to achieve a stable, predictable state of the environment.

### Comment 5 ([user]):

Also, regardless of the above, `poetry update` will accept utter nonsense as arguments without so much as a peep, which is very clearly a bug.

### Comment 6 ([user]):

> If messing with the constraints is the only way to influence the resolution, that contradicts the basic concepts of the model in a pretty severe way

It does not.

> Also, regardless of the above ...

it was you who chose to try and squeeze two completely separate conversations into one issue report ;-)

## PR Review Comments

**[user]** on `src/poetry/console/commands/update.py`:

**issue:** Package name parsing is brittle and may break for extras or more complex specifiers.

Chaining `split` calls to drop version constraints is fragile and will mis-handle valid specs, e.g. `foo[extra]==1.0` (becoming `foo[extra`) or `foo>=1,<2`, and will ignore environment markers. Instead of manual splitting on operators, use `packaging.requirements.Requirement` (or an existing helper in this codebase) to parse the requirement and extract the project name safely.

✅ Addressed in 29b978473eb914a8ea04d8c78654d0ab853c9592: The brittle manual package-name parsing has been removed; version specifiers are now detected via a regex and rejected outright, so the original concern about safely extracting names from requirement strings no longer applies.

**[user]** on `tests/console/commands/test_update.py`:

**suggestion (testing):** Add a test case for a package with a version constraint (e.g. `pkg==1.0.0`) to ensure name extraction is covered

Since `UpdateCommand` now strips version constraints (`==`, `>=`, `<`, `!=`, etc.) before validating names, please add at least one test using a constrained specifier (e.g. `tester.execute("nonexistent==1.2.3")`, and optionally another with `>=` or a compound specifier) to verify that parsing works correctly and that the invalid package still appears in the error message.

✅ Addressed in cb20652dbb1561bbf9fd7dfd6613f948e7848833: The command no longer strips version constraints but instead rejects any arguments containing specifiers, so the original need to test name extraction with constrained specs is obsolete under the new behavior.

**[user]** on `src/poetry/console/commands/update.py`:

I do not think extracting the package name and ignoring the rest makes sense. The interface of `update` is to pass package names. When passing a requirement string instead, the command should probably fail because not respecting the version constraint is unexpected.

**[user]** on `src/poetry/console/commands/update.py`:

You're right, that makes more sense. I've removed the name extraction logic entirely - the command now just validates the argument as-is via canonicalize_name. So passing something like `poetry update "pkg==1.0.0"` will correctly fail with an error instead of silently stripping the version specifier. Pushed the simplified version.

**[user]** on `src/poetry/console/commands/update.py`:

Nit: `canonicalize_name()` is not necessary because `Dependency.name` is a `NormalizedName`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
