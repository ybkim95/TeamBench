#!/usr/bin/env python3
"""Rebuild GH tasks from a full upstream checkout, and keep only the ones that work.

Why the corpus never measured anything
--------------------------------------
The task scraper copied only the files a pull request touched. That leaves the
package in pieces, so the test suite a grader runs cannot even be collected. The
failure is three layers deep, all the same cause:

  1. conftest.py absent            541 of 553 tasks with tests; pytest cannot
                                   resolve fixtures ("fixture 'lang_locales' not
                                   found")
  2. package incomplete            spacy/tests/test_cli.py present without
                                   spacy/util.py, so "No module named spacy.util"
  3. test-only dependencies absent  pytest-mock and friends

Traced on GH444_arrow_1184: with the reference patch applied to the shipped
workspace, checks C9 and C10 flip FAIL -> OK, so the fix is recognised. Only C1
("test suite passes") stays red, and only because the suite never runs. This is
the whole explanation for the corpus-level symptoms: no GH task passing under any
model, the upstream reference reaching 1.0 on 0 of 153 tasks, and the reference
being worth only +2.0 pp over doing nothing.

What this does
--------------
For each task, check out the upstream repo at its recorded base_sha, install it,
and verify the task actually discriminates:

    G_fail   the grader's test target FAILS before the reference patch
    G_pass   the same target PASSES after applying the reference patch

Both must hold. A task that fails G_fail has no bug left to find; a task that
fails G_pass cannot be solved even by the maintainers' own merged fix. Only tasks
satisfying both enter the verified core, and the count that survives is the
honest size of the benchmark.

Nothing here edits a grader, a spec, a reference patch, or any recorded result.
It supplies the repository state the task always needed in order to run.

Usage:
  python scripts/build_verified_core.py --list-repos
  python scripts/build_verified_core.py --repos arrow-py/arrow --limit 3
  python scripts/build_verified_core.py --pure-python --workers 4
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
OUT = os.path.join(REPO, "shared", "paper", "quality")

# Deliberately absent: psycopg. `from psycopg import pq` needs the compiled
# psycopg_c companion, and its suite loads a `tests.fix_db` plugin that expects a
# live PostgreSQL server. All 14 of its tasks failed for that reason alone, so
# counting them as corpus defects would be wrong; they are simply not testable in
# a network-isolated container.
#
# Repos that are importable from a plain `pip install -e .` without a compiler
# toolchain or a multi-gigabyte checkout. Heavy scientific repos (numpy, pytorch,
# scipy, matplotlib) are excluded here: they need a build, and a partially built
# extension produces exactly the import errors this script exists to remove.
PURE_PYTHON = {
    "arrow-py/arrow", "pallets/flask", "pallets/click", "pallets/jinja",
    "pallets/werkzeug", "pallets/quart", "encode/httpx", "encode/starlette",
    "Kludex/starlette", "celery/celery", "python-attrs/attrs",
    "marshmallow-code/marshmallow", "aio-libs/aiohttp",
    "urllib3/urllib3", "pydantic/pydantic", "redis/redis-py",
}


# Tier 2: the repo's own source is pure Python, but it depends on packages that
# arrive as prebuilt wheels (numpy, pyarrow, pandas). Nothing here needs a
# compiler for the repo itself, which is the only thing `pip install -e .` builds.
# Held back deliberately: numpy, scipy, pandas, matplotlib, scikit-learn,
# statsmodels, spaCy, pytorch and ray all compile their OWN extensions, and a
# half-built extension produces exactly the import errors this script exists to
# eliminate. Also held back: transformers, keras, pytorch-lightning, gpytorch,
# darts, pymc, autogluon and airflow, whose installs pull multi-gigabyte
# frameworks, so they are worth attempting only once the cheap tier is settled.
TIER2 = {
    "dask/dask", "mlflow/mlflow", "great-expectations/great_expectations",
    "plotly/plotly.py", "alteryx/featuretools", "django/django", "boto/boto3",
    "sktime/sktime", "home-assistant/core", "microsoft/FLAML", "wandb/wandb",
}


# Tier 3: the long tail. Pure-Python source, small checkouts, and a nonzero
# ceiling. poetry (6 of 6) and napari (6 of 7) have the highest add-a-test rate
# in the whole corpus.
TIER3 = {
    "python-poetry/poetry", "napari/napari", "narwhals-dev/narwhals",
    "mitmproxy/mitmproxy", "astropy/astropy", "huggingface/evaluate",
    "scikit-hep/pyhf", "pymovements/pymovements", "music-assistant/server",
    "Flagsmith/flagsmith", "aramis-lab/clinica", "ITISFoundation/osparc-simcore",
    "NVIDIA/NeMo-Agent-Toolkit", "tile-ai/TileOPs", "linagora/openrag",
    "dbbs-lab/bsb-core",
}

# Recorded rather than merely omitted, so the exclusions are auditable.
# COMPILED: the repo builds its own C/Cython/Rust extension, so `pip install -e .`
#   needs a toolchain and a half-built extension reproduces the very import
#   errors this script exists to remove. 165 tasks, ceiling 53.
# GIANT: the install pulls torch or tensorflow. 94 tasks, ceiling 23.
COMPILED = {
    "numpy/numpy", "scipy/scipy", "pandas-dev/pandas", "matplotlib/matplotlib",
    "pytorch/pytorch", "scikit-learn/scikit-learn", "statsmodels/statsmodels",
    "explosion/spaCy", "ray-project/ray", "psycopg/psycopg", "pymc-devs/pymc",
}
GIANT = {
    "huggingface/transformers", "keras-team/keras",
    "Lightning-AI/pytorch-lightning", "cornellius-gp/gpytorch",
    "autogluon/autogluon", "unit8co/darts", "apache/airflow",
    "NVIDIA/TensorRT-LLM", "oven-sh/bun",
}


PYTHONS_DIR = os.path.join(REPO, ".cache", "pythons")


def available_pythons() -> list:
    """(version tuple, interpreter path), newest first.

    The running interpreter plus any standalone CPython unpacked under
    .cache/pythons. Needed because a repo's `requires-python` is a hard gate:
    32 of home-assistant's 37 tasks failed with "requires a different Python:
    3.10.12 not in '>=3.13.2'", and mitmproxy, astropy, NeMo and
    music-assistant fail the same way. That is 26 ceiling tasks lost to the
    interpreter rather than to anything about the corpus.
    """
    out = [(sys.version_info[:3], sys.executable)]
    if os.path.isdir(PYTHONS_DIR):
        for d in sorted(os.listdir(PYTHONS_DIR)):
            exe = os.path.join(PYTHONS_DIR, d, "bin", "python3")
            m = re.match(r"py(\d+)\.(\d+)\.(\d+)$", d)
            if m and os.access(exe, os.X_OK):
                out.append((tuple(int(x) for x in m.groups()), exe))
    return sorted(set(out), reverse=True)


def requires_python(tree: str) -> str:
    for name in ("pyproject.toml", "setup.cfg"):
        p = os.path.join(tree, name)
        if not os.path.isfile(p):
            continue
        m = re.search(r"""^\s*(?:requires-python|python_requires)\s*=\s*["']?([^"'\n]+)""",
                      open(p, encoding="utf-8", errors="replace").read(), re.M)
        if m:
            return m.group(1).strip()
    return ""


def satisfies(ver: tuple, spec: str) -> bool:
    """Enough of PEP 440 for `requires-python`: comma-joined comparators."""
    if not spec:
        return True
    for part in spec.split(","):
        part = part.strip()
        m = re.match(r"(>=|<=|==|!=|>|<|~=)?\s*([0-9][0-9.*]*)", part)
        if not m:
            continue
        op, raw = m.group(1) or ">=", m.group(2).replace(".*", "")
        want = tuple(int(x) for x in raw.split(".") if x.isdigit())
        cur = ver[: len(want)] if want else ver
        if op == ">=" and not cur >= want: return False
        if op == ">" and not cur > want: return False
        if op == "<=" and not cur <= want: return False
        if op == "<" and not cur < want: return False
        if op == "==" and cur != want: return False
        if op == "!=" and cur == want: return False
        if op == "~=" and not (cur >= want and cur[:1] == want[:1]): return False
    return True


def pick_python(tree: str):
    """Oldest interpreter that satisfies requires-python, else the newest."""
    spec = requires_python(tree)
    cands = [(v, p) for v, p in available_pythons() if satisfies(v, spec)]
    if not cands:
        return sys.executable, spec, False
    v, p = sorted(cands)[0]
    return p, spec, True


def sh(cmd, cwd=None, timeout=600, env=None):
    return subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd, capture_output=True,
                          text=True, timeout=timeout,
                          env={**os.environ, **(env or {})})


def notes(task):
    p = os.path.join(TASKS, task, "curation_notes.json")
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def test_target(task):
    """The path the grader's C1 actually runs pytest against."""
    g = os.path.join(TASKS, task, "grade.sh")
    if not os.path.isfile(g):
        return None
    src = open(g, errors="ignore").read()
    m = re.search(r"pytest\s+([^\n|)]*?)\s+-x", src)
    if m:
        t = m.group(1).strip()
        if t and not t.startswith("-"):
            return t
    n = notes(task) or {}
    tf = n.get("test_files") or []
    if tf:
        return tf[0]
    # 33 graders run a bare `python -m pytest` with no path. Against the shipped
    # fragment that meant "the two files present"; against a full checkout it
    # would mean the repo's entire suite, which no single fix makes green. The
    # equivalent target is the test files the reference patch touches.
    return None


def patch_test_files(patch_path: str) -> list[str]:
    """Test files the patch touches, in +++ order."""
    out = []
    for line in open(patch_path, encoding="utf-8", errors="replace"):
        if line.startswith("+++ "):
            q = line[4:].strip()
            q = q[2:] if q.startswith("b/") else q
            if re.search(r"(^|/)(test_[^/]*|[^/]*_test)\.py$", q) and q not in out:
                out.append(q)
    return out


def added_test_names(patch_path: str):
    """(test files the patch touches, bare names of the test functions it adds).

    Names, not node ids. Building an id as `<file>::<func>` was wrong: the added
    test is often a METHOD, so its real id carries the class
    (`tests/test_funcs.py::TestAsDict::test_non_atomic_types`), and pytest
    answered "no match in any of [<Module test_funcs.py>]" for every one of them.
    Parametrised tests have the same problem with their `[case]` suffix. The ids
    are resolved from a real collection instead, in collect_ids.
    """
    cur, files, names = None, [], []
    for line in open(patch_path, encoding="utf-8", errors="replace"):
        if line.startswith("+++ "):
            q = line[4:].strip()
            q = q[2:] if q.startswith("b/") else q
            cur = q if re.search(r"(^|/)(test_[^/]*|[^/]*_test)\.py$", q) else None
            if cur and cur not in files:
                files.append(cur)
        elif cur and line.startswith("+"):
            m = re.match(r"\+\s*(?:async\s+)?def (test_\w+)", line)
            if m and m.group(1) not in names:
                names.append(m.group(1))
    return files, names


def collect_ids(py: str, tree: str, files: list, names: list, timeout: int) -> list:
    """Real node ids for the added tests, whatever class or parametrisation."""
    r = sh([py, "-m", "pytest", *files, "--collect-only", "-q",
            "-p", "no:cacheprovider", "-p", "no:cov", "--override-ini=addopts=",
            "--override-ini=filterwarnings="], cwd=tree, timeout=timeout)
    want, ids = set(names), []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if "::" not in line:
            continue
        if line.split("::")[-1].split("[")[0] in want:
            ids.append(line)
    return ids


# Module -> distribution where the two names differ. Everything else is tried as
# the module name with underscores turned into hyphens, which is right far more
# often than not.
ALIAS = {"pytest_mock": "pytest-mock", "pytest_asyncio": "pytest-asyncio",
         "pytest_httpbin": "pytest-httpbin", "yaml": "PyYAML", "attr": "attrs",
         "dateutil": "python-dateutil", "OpenSSL": "pyOpenSSL",
         "zope": "zope.interface", "pkg_resources": "setuptools",
         "Crypto": "pycryptodome", "dotenv": "python-dotenv",
         "jwt": "PyJWT", "PIL": "pillow", "bs4": "beautifulsoup4"}

MISSING_RE = re.compile(r"""No module named ['"]([A-Za-z_][\w.]*)['"]""")
# A half-present dependency reports this instead, with no "No module named" line.
PARTIAL_RE = re.compile(r"""cannot import name ['"][^'"]+['"] from ['"]([A-Za-z_][\w.]*)['"]""")


def own_packages(tree: str) -> set:
    """Top-level packages the checkout itself provides.

    These must never be pip-installed to satisfy an import error: doing so would
    fetch a RELEASED version of the library under test and silently measure the
    wrong code. A missing submodule of one of these is a real defect, not a
    dependency gap.
    """
    out = set()
    for base in (tree, os.path.join(tree, "src")):
        if not os.path.isdir(base):
            continue
        for d in os.listdir(base):
            if os.path.isfile(os.path.join(base, d, "__init__.py")):
                out.add(d)
    return out


def assert_source_wins(py: str, pip: str, tree: str, own: set) -> list:
    """Guarantee the package under test still resolves to the checkout.

    Installing a repo's dev requirements can drag in a RELEASED copy of the very
    library under test: pallets/jinja's requirements/dev.txt pulls sphinx, sphinx
    depends on Jinja2, and pip then replaces the editable install with the
    release. `import jinja2` starts resolving to site-packages, the reference
    patch to the source tree stops having any effect, and eight jinja tasks that
    had verified cleanly flipped to "the maintainers' own fix does not work".

    Same failure mode as --system-site-packages, arriving by a different route,
    so it gets an explicit assertion rather than an ordering convention.
    """
    tree_real = os.path.realpath(tree)
    bad = []
    for pkg in sorted(own):
        r = sh([py, "-c", "import %s as _m, os; print(os.path.dirname(_m.__file__))" % pkg],
               cwd=tree, timeout=120)
        if r.returncode:
            continue
        where = os.path.realpath((r.stdout or "").strip())
        if where and not where.startswith(tree_real):
            bad.append(pkg)
    if bad:
        sh([pip, "install", "-q", "--no-deps", "--force-reinstall", "-e", "."],
           cwd=tree, timeout=900)
    return bad


def pytest_run(py: str, tree: str, args: list, timeout: int) -> dict:
    # -p no:cacheprovider keeps the tree clean between runs, and a repo's own
    # coverage gate in addopts must not decide the verdict.
    # filterwarnings is cleared, not just addopts. Three starlette tasks failed
    # on `DeprecationWarning: anyio.abc.BlockingPortal alias is deprecated`,
    # raised as an ERROR by the repo's own filterwarnings=error against an anyio
    # newer than the commit. That warning is emitted by a DEPENDENCY and has
    # nothing to do with the bug under test.
    #
    # Clearing it can only lose tasks, never admit a bad one: if a task's fix is
    # precisely "stop emitting this warning", then without escalation its test
    # passes unfixed, G_fail is false, and the task is REJECTED. So the
    # normalisation is conservative in the safe direction.
    r = sh([py, "-m", "pytest", *args, "-q", "--no-header", "-p", "no:cacheprovider",
            "-p", "no:cov", "--override-ini=addopts=",
            "--override-ini=filterwarnings="], cwd=tree, timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"(\d+) passed", out)
    bad = re.search(r"no tests ran|ERROR .*collect|Interrupted|"
                    r"while loading conftest|file or directory not found|"
                    r"No module named", out)
    # 2 interrupted, 3 internal error, 4 usage error (a missing path lands here).
    # None of the three means a test executed and disagreed with the code.
    return {"rc": r.returncode, "passed": int(m.group(1)) if m else 0,
            "failed": bool(re.search(r"\d+ (failed|error)", out)),
            "collected": r.returncode not in (2, 3, 4) and not bad,
            "out": out, "tail": out.strip()[-260:]}


def declared_test_groups(tree: str) -> list:
    """Extra / dependency-group names in pyproject that look test related.

    Read with a regex rather than tomllib, which is 3.11+, and this runs on 3.10.
    Only section keys are needed, so a full TOML parse buys nothing.
    """
    pp = os.path.join(tree, "pyproject.toml")
    if not os.path.isfile(pp):
        return []
    txt = open(pp, encoding="utf-8", errors="replace").read()
    out = []
    for sect, kind in (("project.optional-dependencies", "extra"),
                       ("dependency-groups", "group")):
        m = re.search(r"^\[%s\](.*?)(?=^\[|\Z)" % re.escape(sect), txt,
                      re.S | re.M)
        if not m:
            continue
        for key in re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*=", m.group(1), re.M):
            # `all` and `linting` are skipped: they drag in doc and lint
            # toolchains that no test needs and that often conflict.
            if re.search(r"test|dev", key, re.I) and (kind, key) not in out:
                out.append((kind, key))
    return out


def resolve_deps(py, pip, tree, args, timeout, own, rounds=12) -> list:
    """Install the test-only dependencies the run turns out to need.

    A repo's test extra is the declared answer, but declaring it is not reliable:
    pip accepts `-e .[test]` with rc 0 even when no such extra exists, merely
    warning, so attrs installed nothing and every run died in tests/conftest.py
    on `import hypothesis`. Reading the requirement off the actual failure works
    for every repo without a per-repo table.
    """
    # 12 rounds, not 4. Collection of a single test file stops at its FIRST
    # ImportError, so each round can reveal only one missing module. pydantic's
    # tests need dirty_equals, cloudpickle, jsonschema, pytest_examples and
    # email_validator among others, and a cap of 4 left every one of those files
    # uncollectable, which was then misread as the task failing to discriminate.
    got = []
    for _ in range(rounds):
        r = pytest_run(py, tree, args, timeout)
        if r["rc"] == 0:
            break
        want = {m.split(".")[0] for m in MISSING_RE.findall(r["out"])}
        want |= {m.split(".")[0] for m in PARTIAL_RE.findall(r["out"])}
        want -= own
        want -= {g.split("==")[0] for g in got}
        if not want:
            break
        pkgs = [ALIAS.get(w, w.replace("_", "-")) for w in sorted(want)]
        ok = sh([pip, "install", "-q", *pkgs], timeout=timeout)
        if ok.returncode:
            # try them one at a time so one bad guess does not sink the rest
            for pkg in pkgs:
                if sh([pip, "install", "-q", pkg], timeout=timeout).returncode == 0:
                    got.append(pkg)
            if not got:
                break
        else:
            got.extend(pkgs)
    assert_source_wins(py, pip, tree, own)
    return got


def fail_to_pass(py, tree, patch_path, target, timeout, pip=None, own=frozenset()) -> dict:
    """Apply ONLY the patch's test-file hunks, then check those tests fail.

    The source fix is deliberately withheld: if the new tests still pass, the task
    does not discriminate and must not enter the core.
    """
    files, names = added_test_names(patch_path)
    if not names:
        return {"added": 0, "names": [], "files": files,
                "fails_without_fix": None, "why": "patch adds no test"}
    # MUST run on a pristine tree. The first version ran after the full patch had
    # been applied and used `git stash`, which does not stash untracked files: a
    # test file the patch newly CREATED survived the stash, so re-applying the
    # test hunks failed with "already exists" and the task was misfiled as
    # undecided. The caller now resets the tree and calls this first.
    r = sh(f"git apply --include='*test*' {patch_path!r}", cwd=tree, timeout=120)
    if r.returncode:
        reset(tree)
        return {"added": len(names), "names": names, "files": files,
                "fails_without_fix": None, "why": "test-only apply failed",
                "tail": r.stderr[-200:]}
    # The patch's new tests may import a test-only dependency the pristine tree
    # never needed. Resolve that FIRST, or a missing import would be recorded as
    # "fails without the fix" for the wrong reason.
    deps = resolve_deps(py, pip, tree, files, timeout, own) if pip else []
    nodes = collect_ids(py, tree, files, names, timeout)
    if not nodes:
        reset(tree)
        return {"added": len(names), "names": names, "files": files,
                "deps_installed": deps, "fails_without_fix": None,
                "why": "added tests are not collectible on the pristine tree"}
    rr = pytest_run(py, tree, nodes, timeout)
    reset(tree)
    # An import or collection error is not evidence that the fix is needed, so
    # only a genuine test failure counts as FAIL. Anything that never ran is
    # undecided rather than either verdict.
    if not rr["collected"]:
        verdict, why = None, "added tests did not collect"
    else:
        verdict, why = rr["rc"] != 0, None
    return {"added": len(names), "names": names, "files": files, "nodes": nodes,
            "deps_installed": deps, "fails_without_fix": verdict, "why": why,
            "tail": rr["tail"]}


def reset(tree: str) -> None:
    """Back to base_sha exactly: tracked edits reverted, new files removed."""
    sh(["git", "checkout", "--quiet", "--", "."], cwd=tree, timeout=120)
    sh(["git", "clean", "-fdq"], cwd=tree, timeout=120)


def run_added(py: str, tree: str, nodes: list[str], timeout: int) -> dict:
    """Do the patch's own new tests pass? The SWE-bench PASS side of the pair."""
    if not nodes:
        return {"rc": None}
    r = pytest_run(py, tree, nodes, timeout)
    r.pop("out", None)
    return r


def build(task, keep=False, timeout=900):
    n = notes(task)
    if not n or not n.get("repo") or not n.get("base_sha"):
        return {"task": task, "status": "no_repo_or_sha"}
    repo, sha = n["repo"], n["base_sha"]
    patch = os.path.join(TASKS, task, "reference", "patch.diff")
    if not os.path.isfile(patch):
        return {"task": task, "status": "no_reference_patch", "repo": repo}
    target = test_target(task)
    target_from = "grader"
    if not target:
        tf = patch_test_files(patch)
        target, target_from = " ".join(tf), "patch"
    if not target:
        return {"task": task, "status": "no_test_target", "repo": repo}

    work = tempfile.mkdtemp(prefix=f"core_{task[:14]}_")
    tree = os.path.join(work, "r")
    try:
        r = sh(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
                f"https://github.com/{repo}.git", tree], timeout=600)
        if r.returncode:
            return {"task": task, "status": "clone_failed", "repo": repo,
                    "err": r.stderr[-160:]}
        r = sh(["git", "checkout", "--quiet", sha], cwd=tree, timeout=600)
        if r.returncode:
            return {"task": task, "status": "checkout_failed", "repo": repo,
                    "err": r.stderr[-160:]}

        # NOT --system-site-packages. With it, /usr/lib/python3/dist-packages/attr
        # and ~/.local/.../pydantic_core shadowed the checkout, so the tests ran
        # against a foreign version of the very library under test: 9 of the 73
        # G_pass failures named a system path outright. The venv must be sealed.
        venv = os.path.join(work, "venv")
        base_py, req_spec, req_ok = pick_python(tree)
        sh([base_py, "-m", "venv", venv], timeout=300)
        pip = os.path.join(venv, "bin", "pip")
        py = os.path.join(venv, "bin", "python")
        # A fresh venv ships whatever pip ensurepip bundled. PEP 660 editable
        # installs of hatchling/setuptools>=64 projects need a current pip, and
        # its absence is what failed the install on 49 of 110 tasks.
        sh([pip, "install", "-q", "-U", "pip", "setuptools", "wheel"], timeout=600)
        # Prefer the repo's own test extra so its test-only deps come along.
        inst, extra_used = None, None
        for spec in ('.[test]', '.[tests]', '.[dev]', '.[testing]', '.'):
            inst = sh([pip, "install", "-q", "-e", spec], cwd=tree, timeout=timeout)
            if inst.returncode == 0:
                extra_used = spec
                break
        # Declared test extras. Asked by name because pip accepts an extra that
        # does not exist with rc 0 and only a warning, so a blind `.[test]`
        # cannot tell "installed" from "silently skipped".
        # An extra is requested as `.[name]`; a PEP 735 dependency-group is not
        # an extra at all and needs `--group name`, which pip grew in 25.1. The
        # pip upgrade above is what makes that available.
        groups = []
        for kind, name in declared_test_groups(tree):
            arg = ["-e", f".[{name}]"] if kind == "extra" else ["--group", name]
            if sh([pip, "install", "-q", *arg], cwd=tree, timeout=timeout).returncode == 0:
                groups.append(f"{kind}:{name}")
        # Every matching file, not the first one: celery splits its test deps
        # across requirements/test.txt and requirements/default.txt, and stopping
        # at the first match left `redis` uninstalled. Its test module then read
        # the failed optional import as None and died with "NoneType takes no
        # arguments", which carries no module name for the resolver to catch.
        #
        # `requirements.txt` matters most of all: it is where starlette PINS its
        # dependency versions for this commit. Without it pip fetched a newer
        # anyio, whose DeprecationWarning became an error under the repo's own
        # filterwarnings=error and failed every starlette task on a warning that
        # has nothing to do with the bug.
        if inst is not None and inst.returncode:
            # The declared dependency set could not be installed. home-assistant
            # pins lru-dict and ciso8601 at versions that do not build on 3.13,
            # and one commit pins home-assistant-bluetooth==1.12.1, which is not
            # on PyPI at all. One unsatisfiable pin should not cost the whole
            # task, so install the package without its dependencies and let
            # resolve_deps find what the tests genuinely import.
            inst_nodeps = sh([pip, "install", "-q", "--no-deps", "-e", "."],
                             cwd=tree, timeout=timeout)
            if inst_nodeps.returncode == 0:
                extra_used = ".  (--no-deps fallback)"
                inst = inst_nodeps

        for req in ("requirements.txt", "requirements-tests.txt",
                    "requirements/tests.txt", "requirements-dev.txt",
                    "requirements/dev.txt", "requirements/testing.txt",
                    "requirements/test.txt", "requirements/default.txt"):
            rp = os.path.join(tree, req)
            if os.path.isfile(rp):
                sh([pip, "install", "-q", "-r", req], cwd=tree, timeout=timeout)
        sh([pip, "install", "-q", "pytest", "pytest-mock", "pytest-asyncio"],
           timeout=600)

        # target can name several files; splitting matters because pytest treats
        # a single argument containing spaces as one missing path.
        targs = target.split()

        def run_tests():
            r = pytest_run(py, tree, targs, timeout)
            r.pop("out", None)
            return r

        own = own_packages(tree)
        shadowed = assert_source_wins(py, pip, tree, own)
        deps = resolve_deps(py, pip, tree, targs, timeout, own)
        before = run_tests()
        # A fix PR usually ADDS the test that proves it. At base_sha that test
        # does not exist yet, so the suite passes before the patch and passes
        # again after, and "fails before" would reject a perfectly good task.
        # The discriminating question is SWE-bench's FAIL_TO_PASS: do the tests
        # the patch introduces fail without the source fix? Asked on the
        # PRISTINE tree, before the fix is anywhere near it.
        reset(tree)
        f2p = fail_to_pass(py, tree, patch, target, timeout, pip=pip, own=own)
        reset(tree)

        ap = sh(["git", "apply", patch], cwd=tree, timeout=120)
        if ap.returncode:
            ap = sh(["git", "apply", "-3", patch], cwd=tree, timeout=120)
        if ap.returncode:
            return {"task": task, "status": "patch_failed", "repo": repo,
                    "before": before, "fail_to_pass": f2p,
                    "err": ap.stderr[-160:]}
        after = run_tests()
        # Re-resolve the ids with the fix applied. A test that could not even be
        # COLLECTED on the pristine tree has no id there, so the first version
        # left after_added empty and 24 tasks were filed as undecided on no
        # evidence. Collection is what the missing fix broke, which is precisely
        # the situation SWE-bench counts as FAIL_TO_PASS.
        post_nodes = f2p.get("nodes") or []
        if not post_nodes and f2p.get("names"):
            post_nodes = collect_ids(py, tree, f2p.get("files") or [],
                                     f2p["names"], timeout)
        after_added = run_added(py, tree, post_nodes, timeout)

        g_pass_added_ = after_added.get("rc") == 0
        fw = f2p.get("fails_without_fix")
        if fw is True:
            g_fail, g_fail_via = True, "added tests fail without the fix"
        elif fw is None and f2p.get("names") and g_pass_added_:
            # Undecided on the pristine tree (would not collect, or the test
            # hunks would not apply on their own) yet green once the fix lands.
            # The fix is therefore what makes them runnable at all.
            g_fail, g_fail_via = True, "added tests do not even run without the fix"
        elif fw is None and not f2p.get("names") and before["rc"] != 0 and after["rc"] == 0:
            # The PR adds no test of its own. Then the grader's own target is the
            # only available signal, and it is a valid one when it flips.
            g_fail, g_fail_via = True, "grader target flips fail -> pass"
        else:
            g_fail, g_fail_via = False, None
        # Two readings of "the fix works", reported separately because they
        # answer different questions. `whole` is the grader's own C1 target: if
        # it cannot go green with the maintainers' merged fix, the task is
        # unsolvable AS GRADED. `added` is SWE-bench's: it isolates the tests the
        # fix is actually about, so it still holds when the target file carries
        # unrelated pre-existing failures.
        # Freeze the environment that actually made this task measurable. The
        # benchmark cannot ship a vendored copy of 90 upstream projects (the
        # licences differ and no NOTICE files exist), so a task has to be staged
        # by cloning `repo` at `sha` and installing a pinned dependency set. This
        # IS that set: recorded from the interpreter that just ran the tests,
        # rather than re-resolved later against whatever PyPI serves that day.
        frozen = sh([pip, "freeze", "--exclude-editable"], timeout=300)
        env_freeze = sorted(l.strip() for l in (frozen.stdout or "").splitlines()
                            if l.strip() and not l.startswith("-"))

        g_pass_whole = after["rc"] == 0
        g_pass_added = g_pass_added_ if f2p.get("names") else g_pass_whole
        return {"task": task, "repo": repo, "sha": sha, "target": target,
                "target_from": target_from, "status": "ok",
                "install_rc": inst.returncode if inst else None,
                "install_extra": extra_used, "install_groups": groups,
                "python": base_py, "requires_python": req_spec,
                "requires_python_met": req_ok, "env_freeze": env_freeze,
                "shadowed_by_release": shadowed,
                "deps_installed": deps,
                "install_err": (inst.stderr or "")[-200:] if inst and inst.returncode else None,
                "before": before, "after": after, "after_added": after_added, "post_nodes": post_nodes[:8],
                "fail_to_pass": f2p,
                "G_fail": g_fail, "G_fail_via": g_fail_via,
                "G_pass": g_pass_added, "G_pass_whole": g_pass_whole,
                "verified": bool(g_fail and g_pass_added),
                "verified_strict": bool(g_fail and g_pass_whole)}
    except subprocess.TimeoutExpired:
        return {"task": task, "status": "timeout", "repo": repo}
    except Exception as e:
        return {"task": task, "status": "error", "repo": repo, "err": str(e)[:160]}
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--pure-python", action="store_true")
    ap.add_argument("--tier2", action="store_true",
                    help="pure-Python source with binary dependencies from wheels")
    ap.add_argument("--tier3", action="store_true",
                    help="the long tail: small pure-Python repos")
    ap.add_argument("--tasks", nargs="+", default=None,
                    help="explicit task ids, for isolating one case")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900,
                    help="per-step seconds; tier-2 installs need more")
    ap.add_argument("--list-repos", action="store_true")
    ap.add_argument("--out", default=os.path.join(OUT, "verified_core.json"))
    a = ap.parse_args()

    rows = []
    for d in sorted(os.listdir(TASKS)):
        if not d.startswith("GH"):
            continue
        n = notes(d)
        if n and n.get("repo") and n.get("base_sha"):
            rows.append((d, n["repo"]))

    if a.list_repos:
        c = collections.Counter(r for _, r in rows)
        for k, v in c.most_common():
            mark = ("*" if k in PURE_PYTHON else "2" if k in TIER2 else
                "3" if k in TIER3 else "C" if k in COMPILED else
                "G" if k in GIANT else " ")
            print(f" {mark} {v:4}  {k}")
        print(f"\n* = pure-python set ({sum(v for k,v in c.items() if k in PURE_PYTHON)} tasks)"
              f"   2 = tier 2 ({sum(v for k,v in c.items() if k in TIER2)} tasks)")
        return 0

    want = set(a.repos) if a.repos else None
    if want is None:
        pick = set()
        if a.pure_python:
            pick |= PURE_PYTHON
        if a.tier2:
            pick |= TIER2
        if a.tier3:
            pick |= TIER3
        want = pick or None
    sel = [t for t, r in rows if want is None or r in want]
    if a.tasks:
        sel = [t for t in sel if t in set(a.tasks)] or list(a.tasks)
    if a.limit:
        sel = sel[: a.limit]
    print(f"tasks to build: {len(sel)}  (workers={a.workers})", flush=True)

    done = []
    if os.path.isfile(a.out):
        done = json.load(open(a.out))
        seen = {d["task"] for d in done}
        sel = [t for t in sel if t not in seen]
        print(f"  resuming, {len(seen)} already built, {len(sel)} to go", flush=True)

    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(build, t, False, a.timeout): t for t in sel}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            done.append(fut.result())
            if i % 5 == 0 or i == len(sel):
                v = sum(1 for d in done if d.get("verified"))
                json.dump(done, open(a.out, "w"), indent=1)
                print(f"  [{i}/{len(sel)}] verified so far: {v}", flush=True)

    json.dump(done, open(a.out, "w"), indent=1)
    c = collections.Counter(d["status"] for d in done)
    ok = [d for d in done if d["status"] == "ok"]
    print(f"\nbuilt {len(done)} tasks")
    for k, v in c.most_common():
        print(f"  {k:22} {v}")
    if ok:
        bad = sum(1 for d in ok if d.get("install_rc"))
        gf = sum(1 for d in ok if d["G_fail"])
        gp = sum(1 for d in ok if d["G_pass"])
        gpw = sum(1 for d in ok if d.get("G_pass_whole"))
        ver = sum(1 for d in ok if d["verified"])
        vs = sum(1 for d in ok if d.get("verified_strict"))
        print(f"\n  of {len(ok)} that built  (install still failed on {bad}):")
        print(f"    G_fail  new tests fail without the fix : {gf}")
        print(f"    G_pass  new tests pass with the fix    : {gp}")
        print(f"            whole grader target passes     : {gpw}")
        print(f"    VERIFIED        (G_fail and G_pass)    : {ver}")
        print(f"    VERIFIED strict (whole target green)   : {vs}")
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
