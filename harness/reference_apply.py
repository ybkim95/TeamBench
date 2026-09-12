"""
harness/reference_apply.py
==========================

Reconstruct the upstream reference solution inside a staged TeamBench workspace.

WHY THIS EXISTS
---------------
Gate G3 of ``scripts/task_admission_gate.py`` asks the SWE-bench-Verified
question: does a known-correct solution pass the task's own grader?  The
known-correct solution is ``tasks/<id>/reference/patch.diff``, the authoritative
upstream diff for the pull request the task was derived from.

Naively running ``git apply`` on the staged workspace answers a different and
much less interesting question, because the staged workspace is not the upstream
tree:

  1. GH task workspaces are *parameterised*.  ``generators/gh_deep_param.py``
     renames user identifiers and injects comment noise as a deterministic
     function of the seed, so the diff's context lines no longer match.
  2. The staged workspace holds only the files the PR touched, not the repo, so
     some file diffs have no target at all.
  3. Many workspaces already ship the PR's *test* files in their post-PR state
     (the tests are what defines the task), so those file diffs are already
     applied and a whole-patch ``git apply`` aborts on them.
  4. ``patch -p0`` "succeeds" on a ``diff --git`` patch by creating literal
     ``a/`` and ``b/`` directories.  The old applier had ``patch -p0`` in its
     ladder, so it recorded a *false* application for tasks it never patched.

The applier here answers the intended question.  Its preferred method does not
try to force an upstream diff onto a renamed tree at all; it applies the diff to
the *unparameterised* base the generator itself starts from and then re-runs the
generator's own parameterisation on the result, with the symbol rename map
frozen to the one the staged instance used.  What lands in the workspace is
therefore the upstream fix expressed in the seed's identifier space, which is
exactly what a correct agent would have written.

METHOD LADDER (first success wins, and the method used is always recorded)
-------------------------------------------------------------------------
``reparam``       Apply the diff to the generator's own ``_base_workspace()``
                  (pure upstream pre-PR text, so the diff applies as upstream
                  intended), then replay ``Generator.generate(seed)`` on the
                  patched base with ``gh_deep_param._build_rename_map`` frozen to
                  the map the pristine instance used.  Guarded by a self-check:
                  the replay's *base* run must reproduce the staged workspace
                  byte for byte, otherwise the method is refused.
``reparam-static``Same, for the 16 tasks whose generator module name is not
                  importable (task ids containing ``-`` or ``.``); those stage a
                  static, unparameterised snapshot, so the identity transform is
                  the correct parameterisation.
``merge3``        Per-file three-way merge with ``git merge-file``:
                  ancestor = unparameterised base, ours = staged (parameterised)
                  file, theirs = unparameterised patched file.  Accepted only on
                  a conflict-free merge.
``direct``        Apply into the staged workspace with the ladder below, whole
                  patch first, then per file, then per hunk.

Within a tree, every application uses this ladder, and per-hunk accounting is
recorded for every attempt:

    git apply -p1                    exact
    git apply -p1 --recount          tolerates wrong hunk line counts
    git apply -p1 -C1                one line of context
    git apply -p1 --3way             blob-level merge when the object is present
    patch -p1 -l -F3                 whitespace-loose, fuzz 3
    patch -p1 -l -F3 --ignore-whitespace

``patch -p0`` is deliberately absent.  Every application is followed by an
assertion that no top-level ``a/`` or ``b/`` directory was created.

WHAT IS NOT COUNTED AS A FAILURE
--------------------------------
already-applied   The file already equals its post-image (``git apply -R
                  --check`` succeeds).  This is the normal state of PR test
                  files in a TeamBench workspace.
out-of-scope      The diff modifies a path the workspace does not contain.  No
                  agent could have edited it and no grader can check it.

A task whose *every* in-scope file is out of scope or already applied produces
no effective change; that is recorded as ``no_effective_change`` and reported
separately, because it means the workspace does not contain the code the
upstream fix touches.

KNOWN COSMETIC DIVERGENCE
-------------------------
``gh_deep_param.add_realistic_noise`` draws from one RNG consumed across the
whole file dict in insertion order, so a file whose content changed can receive
different comment/blank-line noise on the replay than it had in the staged
instance.  Only patch-touched files are written back, and the noise consists of
comments, blank lines, import reordering and quote style, none of which any
grader check inspects.  It is recorded here rather than hidden because it means
the reference workspace is not byte-identical to "staged workspace + minimal
edit"; it is "staged workspace + the upstream edit + possibly different
cosmetic noise on the edited files".
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

_DIFF_GIT = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_MINUS_RE = re.compile(r"^--- (?:a/)?(\S+)")
_PLUS_RE = re.compile(r"^\+\+\+ (?:b/)?(\S+)")

# Ladder, in order.  Each entry is (name, is_git).
METHODS: list[tuple[str, bool]] = [
    ("git-apply", True),
    ("git-apply-recount", True),
    ("git-apply-C1", True),
    ("git-apply-3way", True),
    ("patch-fuzz3", False),
    ("patch-fuzz3-iws", False),
]

_SKIP_DIR_PARTS = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache"}


def _tool_env() -> dict:
    """Environment for every git/patch subprocess.

    Two reasons, one of which is a 3 s-per-call performance cliff:

    * ``HOME`` is redirected to a local scratch dir and the system/global git
      configs are disabled.  On an NFS home directory every single ``git``
      invocation pays the latency of reading ``~/.gitconfig``; measured here at
      3.3 s per call against 0.004 s with a local HOME.  The applier makes tens
      of git calls per task, so this is the difference between 30 s and 1 s.
    * Reproducibility.  Whether a reference patch applies must not depend on the
      operator's personal git configuration (``core.autocrlf``,
      ``apply.whitespace``, ``diff.*``).  Disabling user and system config makes
      the answer a property of the patch and the workspace only.
    """
    home = os.path.join(tempfile.gettempdir(), "teambench_refapply_home")
    os.makedirs(home, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_ASKPASS": "true",
        "LC_ALL": "C",
    })
    return env


_TOOL_ENV = _tool_env()


# ---------------------------------------------------------------------------
# Unified-diff parsing
# ---------------------------------------------------------------------------

@dataclass
class FileDiff:
    old_path: str
    new_path: str
    header: list[str] = field(default_factory=list)
    hunks: list[list[str]] = field(default_factory=list)
    new_file: bool = False
    deleted: bool = False
    binary: bool = False
    renamed: bool = False

    def text(self, hunks: list[list[str]] | None = None) -> str:
        hs = self.hunks if hunks is None else hunks
        body = "".join("".join(h) for h in hs)
        out = "".join(self.header) + body
        if out and not out.endswith("\n"):
            out += "\n"
        return out


def parse_patch(text: str) -> list[FileDiff]:
    """
    Split a unified diff into per-file blocks with their hunks.

    Handles both ``git format-patch`` style (a ``diff --git`` header per file)
    and bare unified diffs whose only header is the ``---``/``+++`` pair.
    """
    lines = text.splitlines(keepends=True)
    out: list[FileDiff] = []
    cur: FileDiff | None = None
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        # Bare unified diff: a --- / +++ pair with no preceding "diff --git".
        if (raw.startswith("--- ") and i + 1 < n and lines[i + 1].startswith("+++ ")
                and (cur is None or cur.hunks)):
            mo = _MINUS_RE.match(raw.rstrip("\n"))
            mn = _PLUS_RE.match(lines[i + 1].rstrip("\n"))
            if mo and mn:
                op, np_ = mo.group(1), mn.group(1)
                cur = FileDiff(old_path=op if op != "/dev/null" else np_,
                               new_path=np_ if np_ != "/dev/null" else op,
                               header=[raw, lines[i + 1]],
                               new_file=(op == "/dev/null"),
                               deleted=(np_ == "/dev/null"))
                out.append(cur)
                i += 2
                continue
        m = _DIFF_GIT.match(raw.rstrip("\n"))
        if m:
            cur = FileDiff(old_path=m.group(1), new_path=m.group(2), header=[raw])
            out.append(cur)
            i += 1
            while i < n:
                l = lines[i]
                if _HUNK_RE.match(l) or _DIFF_GIT.match(l.rstrip("\n")):
                    break
                cur.header.append(l)
                if l.startswith("new file mode"):
                    cur.new_file = True
                elif l.startswith("deleted file mode"):
                    cur.deleted = True
                elif l.startswith("rename from") or l.startswith("rename to"):
                    cur.renamed = True
                elif l.startswith("GIT binary patch") or l.startswith("Binary files"):
                    cur.binary = True
                i += 1
            continue
        if cur is not None and _HUNK_RE.match(raw):
            hunk = [raw]
            i += 1
            while i < n:
                l = lines[i]
                if _HUNK_RE.match(l) or _DIFF_GIT.match(l.rstrip("\n")):
                    break
                if l[:1] in (" ", "+", "-", "\\") or l == "\n":
                    hunk.append(l)
                    i += 1
                else:
                    break
            cur.hunks.append(hunk)
            continue
        i += 1
    return out


def rewrite_paths(fd: FileDiff, new_path: str) -> FileDiff:
    """Return a copy of fd whose a/ and b/ paths are rewritten to new_path."""
    hdr = []
    for l in fd.header:
        if l.startswith("diff --git "):
            hdr.append(f"diff --git a/{new_path} b/{new_path}\n")
        elif l.startswith("--- "):
            hdr.append("--- /dev/null\n" if l.startswith("--- /dev/null")
                       else f"--- a/{new_path}\n")
        elif l.startswith("+++ "):
            hdr.append("+++ /dev/null\n" if l.startswith("+++ /dev/null")
                       else f"+++ b/{new_path}\n")
        elif l.startswith("rename from") or l.startswith("rename to"):
            continue
        else:
            hdr.append(l)
    return FileDiff(old_path=new_path, new_path=new_path, header=hdr,
                    hunks=[list(h) for h in fd.hunks], new_file=fd.new_file,
                    deleted=fd.deleted, binary=fd.binary, renamed=False)


# ---------------------------------------------------------------------------
# Low-level application
# ---------------------------------------------------------------------------

def _argv(method: str, patch_file: str, dry: bool) -> list[str]:
    if method == "git-apply":
        a = ["git", "apply", "-p1", "--whitespace=nowarn"]
    elif method == "git-apply-recount":
        a = ["git", "apply", "-p1", "--recount", "--whitespace=nowarn"]
    elif method == "git-apply-C1":
        a = ["git", "apply", "-p1", "-C1", "--whitespace=nowarn"]
    elif method == "git-apply-3way":
        a = ["git", "apply", "-p1", "--3way", "--whitespace=nowarn"]
    elif method == "patch-fuzz3":
        a = ["patch", "-p1", "-l", "-F", "3", "--batch", "--forward",
             "--no-backup-if-mismatch"]
    elif method == "patch-fuzz3-iws":
        a = ["patch", "-p1", "-l", "--ignore-whitespace", "-F", "3", "--batch",
             "--forward", "--no-backup-if-mismatch"]
    else:
        raise ValueError(method)
    if a[0] == "git":
        if dry:
            a.append("--check")
        a.append(patch_file)
    else:
        if dry:
            a.append("--dry-run")
        a += ["-i", patch_file]
    return a


def _write_tmp_patch(text: str, tmpdir: str, tag: str) -> str:
    p = os.path.join(tmpdir, f"p_{tag}.diff")
    with open(p, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)
    return p


def _run(argv: list[str], cwd: str) -> tuple[int, str]:
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           errors="replace", timeout=120, env=_TOOL_ENV)
        return r.returncode, ((r.stdout or "") + (r.stderr or ""))[-600:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 255, f"{type(exc).__name__}: {exc}"[:600]


def _stray_ab(tree: str) -> bool:
    """True if a literal a/ or b/ directory appeared: the patch -p0 failure mode."""
    return any(os.path.isdir(os.path.join(tree, d)) for d in ("a", "b"))


def _try_ladder(text: str, tree: str, tmpdir: str, tag: str) -> tuple[str | None, list[dict]]:
    """Try every method on one patch text.  Returns (method_or_None, attempts)."""
    pf = _write_tmp_patch(text, tmpdir, tag)
    attempts = []
    for method, _is_git in METHODS:
        rc, err = _run(_argv(method, pf, dry=False), tree)
        ok = rc == 0
        if ok and _stray_ab(tree):
            # A method that "succeeded" by inventing a/ or b/ did not apply.
            shutil.rmtree(os.path.join(tree, "a"), ignore_errors=True)
            shutil.rmtree(os.path.join(tree, "b"), ignore_errors=True)
            ok = False
            err = "REJECTED: created a stray a/ or b/ directory"
        attempts.append({"method": method, "rc": rc, "err": err[:300] if not ok else ""})
        if ok:
            return method, attempts
    return None, attempts


def _already_applied(fd: FileDiff, tree: str, tmpdir: str, tag: str) -> bool:
    """True if reverse-applying the file diff would succeed: it is already at post state."""
    pf = _write_tmp_patch(fd.text(), tmpdir, f"rev_{tag}")
    rc, _ = _run(["git", "apply", "-p1", "-R", "--check", "--whitespace=nowarn", pf], tree)
    return rc == 0


def _hunk_already_applied(fd: FileDiff, hunk: list[str], tree: str,
                          tmpdir: str, tag: str) -> bool:
    pf = _write_tmp_patch(fd.text([hunk]), tmpdir, f"revh_{tag}")
    rc, _ = _run(["git", "apply", "-p1", "-R", "--check", "--whitespace=nowarn", pf], tree)
    return rc == 0


def _tree_files(tree: str) -> list[str]:
    out = []
    for root, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIR_PARTS]
        for f in files:
            out.append(os.path.relpath(os.path.join(root, f), tree))
    return out


def _suffix_match(target: str, candidates: list[str]) -> str | None:
    """Longest unique path-suffix match of `target` among workspace paths."""
    parts = target.split("/")
    for k in range(len(parts), 0, -1):
        suf = "/".join(parts[-k:])
        hits = [c for c in candidates if c == suf or c.endswith("/" + suf)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return None
    return None


# ---------------------------------------------------------------------------
# Whole-tree application with per-file / per-hunk accounting
# ---------------------------------------------------------------------------

def apply_to_tree(fds: list[FileDiff], tree: str, tmpdir: str,
                  allow_remap: bool = True) -> dict:
    """
    Apply a parsed patch to a directory tree, file by file then hunk by hunk.

    Returns a record with per-file outcomes and hunk counts.  Never raises.
    """
    rec: dict = {
        "files": [],
        "hunks_total": 0, "hunks_applied": 0, "hunks_already": 0, "hunks_failed": 0,
        "files_applied": 0, "files_already": 0, "files_failed": 0,
        "files_out_of_scope": 0, "files_unsupported": 0,
        "changed_paths": [], "deleted_paths": [], "methods": [],
    }
    present = _tree_files(tree)
    for idx, fd0 in enumerate(fds):
        fd = fd0
        tag = f"{idx}"
        entry = {"path": fd.new_path, "hunks": len(fd.hunks)}
        rec["hunks_total"] += len(fd.hunks)

        if fd.binary or fd.renamed:
            entry["outcome"] = "unsupported"
            entry["reason"] = "binary" if fd.binary else "rename"
            rec["files_unsupported"] += 1
            rec["hunks_failed"] += len(fd.hunks)
            rec["files"].append(entry)
            continue

        target = fd.new_path
        exists = os.path.exists(os.path.join(tree, target))
        if not exists and not fd.new_file:
            remap = _suffix_match(target, present) if allow_remap else None
            if remap:
                fd = rewrite_paths(fd, remap)
                target = remap
                exists = True
                entry["remapped_to"] = remap
            else:
                entry["outcome"] = "out_of_scope"
                rec["files_out_of_scope"] += 1
                rec["files"].append(entry)
                continue

        if exists and _already_applied(fd, tree, tmpdir, tag):
            entry["outcome"] = "already_applied"
            rec["files_already"] += 1
            rec["hunks_already"] += len(fd.hunks)
            rec["files"].append(entry)
            continue

        if fd.deleted and not exists:
            entry["outcome"] = "already_applied"
            rec["files_already"] += 1
            rec["hunks_already"] += len(fd.hunks)
            rec["files"].append(entry)
            continue

        method, attempts = _try_ladder(fd.text(), tree, tmpdir, tag)
        if method:
            entry["outcome"] = "applied"
            entry["method"] = method
            rec["files_applied"] += 1
            rec["hunks_applied"] += len(fd.hunks)
            rec["methods"].append(method)
            (rec["deleted_paths"] if fd.deleted else rec["changed_paths"]).append(target)
            rec["files"].append(entry)
            continue

        # Whole-file failed: descend to hunks.
        h_ok, h_already, h_bad, used = 0, 0, 0, []
        for hi, hunk in enumerate(fd.hunks):
            if _hunk_already_applied(fd, hunk, tree, tmpdir, f"{tag}_{hi}"):
                h_already += 1
                continue
            m2, _ = _try_ladder(fd.text([hunk]), tree, tmpdir, f"{tag}_{hi}")
            if m2:
                h_ok += 1
                used.append(m2)
            else:
                h_bad += 1
        rec["hunks_applied"] += h_ok
        rec["hunks_already"] += h_already
        rec["hunks_failed"] += h_bad
        entry["hunks_applied"] = h_ok
        entry["hunks_already"] = h_already
        entry["hunks_failed"] = h_bad
        if h_bad == 0 and (h_ok or h_already):
            entry["outcome"] = "applied"
            entry["method"] = "per-hunk:" + ",".join(sorted(set(used))) if used else "per-hunk"
            rec["files_applied"] += 1
            rec["methods"].append(entry["method"])
            (rec["deleted_paths"] if fd.deleted else rec["changed_paths"]).append(target)
        else:
            entry["outcome"] = "failed"
            entry["attempts"] = attempts[:6]
            rec["files_failed"] += 1
            if h_ok:
                (rec["deleted_paths"] if fd.deleted else rec["changed_paths"]).append(target)
        rec["files"].append(entry)
    return rec


# ---------------------------------------------------------------------------
# Base workspace recovery and generator replay
# ---------------------------------------------------------------------------

# The replay must be able to force gh_deep_param's rename map without any other
# worker thread seeing the forced map. An earlier version of this module swapped
# the module-global `_build_rename_map` under a lock; that silently corrupted the
# workspaces other threads were staging at the same moment, because
# `TaskGenerator.generate()` reads the same global. Their staged trees then no
# longer matched their own generator, which showed up later as a spurious
# "control run does not reproduce the staged workspace" and cost those tasks
# their reference solution.
#
# The override is therefore thread-local. The dispatcher below is installed once
# and is a pure pass-through for every thread that has not set an override, so
# generation outside a replay is bit-for-bit what it was before.
_TL = threading.local()
_ORIG_BUILD_RENAME_MAP = None


def _install_rename_map_dispatcher():
    global _ORIG_BUILD_RENAME_MAP
    try:
        import generators.gh_deep_param as gdp
    except Exception:
        return None
    if getattr(gdp._build_rename_map, "_teambench_dispatcher", False):
        return gdp
    _ORIG_BUILD_RENAME_MAP = gdp._build_rename_map

    def dispatcher(symbols, seed, strategy="synonym"):
        ov = getattr(_TL, "rename_override", None)
        if ov is None:
            return _ORIG_BUILD_RENAME_MAP(symbols, seed, strategy=strategy)
        return ov(symbols, seed, strategy)

    dispatcher._teambench_dispatcher = True          # type: ignore[attr-defined]
    gdp._build_rename_map = dispatcher
    return gdp


def _read_static_workspace(task_dir: str) -> dict[str, str]:
    src = os.path.join(task_dir, "workspace")
    out: dict[str, str] = {}
    if not os.path.isdir(src):
        return out
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIR_PARTS]
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, src)
            try:
                with open(p, encoding="utf-8", errors="surrogateescape") as fh:
                    out[rel] = fh.read()
            except OSError:
                continue
    return out


def base_workspace(task_id: str, task_dir: str) -> tuple[dict[str, str], str]:
    """
    The *unparameterised* pre-PR files the task was built from.

    Preference order: the generator's own ``_base_workspace()`` (the literal
    upstream pre-PR text), then the static snapshot under ``tasks/<id>/workspace``.
    """
    try:
        from generators.registry import has_generator, get_generator
        if has_generator(task_id):
            gen = get_generator(task_id)
            fn = getattr(gen, "_base_workspace", None)
            if callable(fn):
                files = fn()
                if isinstance(files, dict) and files:
                    return ({k: v for k, v in files.items() if isinstance(v, str)},
                            "generator._base_workspace")
    except Exception:
        pass
    return _read_static_workspace(task_dir), "tasks/<id>/workspace"


def _write_files(files: dict[str, str], tree: str) -> None:
    for rel, content in files.items():
        p = os.path.join(tree, rel)
        os.makedirs(os.path.dirname(p) or tree, exist_ok=True)
        with open(p, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(content)


def _read_tree(tree: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in _tree_files(tree):
        try:
            with open(os.path.join(tree, rel), encoding="utf-8",
                      errors="surrogateescape") as f:
                out[rel] = f.read()
        except OSError:
            continue
    return out


def reparameterize(task_id: str, seed: int, post_files: dict[str, str],
                   staged_files: dict[str, str]) -> tuple[dict[str, str] | None, str]:
    """
    Re-run the task's own generator on the *patched* base, with the symbol
    rename map frozen to the one the pristine instance used.

    Returns (files, note).  ``files`` is None when the method is refused; the
    note then says why.  The method is refused unless a control run of the
    generator over the unpatched base reproduces the staged workspace exactly,
    which is what makes the frozen map provably the staged instance's map.
    """
    try:
        from generators.registry import has_generator, get_generator
    except Exception as exc:                                    # pragma: no cover
        return None, f"registry import failed: {exc}"
    if not has_generator(task_id):
        return None, "no importable generator"
    gdp = _install_rename_map_dispatcher()
    if gdp is None:
        return None, "gh_deep_param import failed"

    captured: list[dict] = []

    def spy(symbols, s, strategy="synonym"):
        m = _ORIG_BUILD_RENAME_MAP(symbols, s, strategy=strategy)
        captured.append(m)
        return m

    try:
        _TL.rename_override = spy
        gen = get_generator(task_id)
        control = gen.generate(seed=seed)
    except Exception as exc:
        return None, f"control generate failed: {type(exc).__name__}: {exc}"
    finally:
        _TL.rename_override = None

    ctrl_files = {k: v for k, v in control.workspace_files.items()
                  if isinstance(v, str)}
    mismatched = [k for k, v in ctrl_files.items() if staged_files.get(k) != v]
    if mismatched:
        return None, ("control run does not reproduce the staged workspace "
                      f"({len(mismatched)}/{len(ctrl_files)} files differ)")

    idx = [0]

    def frozen(symbols, s, strategy="synonym"):
        i = idx[0]
        idx[0] += 1
        if i < len(captured):
            return captured[i]
        return _ORIG_BUILD_RENAME_MAP(symbols, s, strategy=strategy)

    try:
        _TL.rename_override = frozen
        gen2 = get_generator(task_id)
        gen2._base_workspace = lambda: dict(post_files)          # type: ignore[assignment]
        out = gen2.generate(seed=seed)
    except Exception as exc:
        return None, f"replay generate failed: {type(exc).__name__}: {exc}"
    finally:
        _TL.rename_override = None

    files = {k: v for k, v in out.workspace_files.items() if isinstance(v, str)}
    return files, f"frozen rename maps: {len(captured)}"


def merge3(base: str, ours: str, theirs: str, tmpdir: str, tag: str) -> str | None:
    """Conflict-free three-way merge, or None."""
    paths = {}
    for name, txt in (("base", base), ("ours", ours), ("theirs", theirs)):
        p = os.path.join(tmpdir, f"m_{tag}_{name}")
        with open(p, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(txt)
        paths[name] = p
    try:
        r = subprocess.run(["git", "merge-file", "-p", "--diff3",
                            paths["ours"], paths["base"], paths["theirs"]],
                           capture_output=True, text=True, errors="replace",
                           timeout=120, env=_TOOL_ENV)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_reference_workspace(task_id: str, task_dir: str, workspace: str,
                              seed: int = 0) -> dict:
    """
    Turn a freshly staged pristine workspace into the reference solution.

    ``workspace`` is mutated in place.  Returns a record describing exactly what
    was done, suitable for storing in the admission ledger.

    Record keys of interest:
      applied            bool  every in-scope file diff reached its post state
      method             str   reparam | reparam-static | merge3 | direct | mixed
      hunks_total/applied/already/failed
      files_*            counts by outcome
      no_effective_change  bool  nothing in the workspace actually changed
      base_source        where the unparameterised base came from
      notes              list[str]
    """
    out: dict = {
        "applied": False, "method": None, "notes": [],
        "hunks_total": 0, "hunks_applied": 0, "hunks_already": 0, "hunks_failed": 0,
        "files_total": 0, "files_applied": 0, "files_already": 0, "files_failed": 0,
        "files_out_of_scope": 0, "files_unsupported": 0,
        "written_paths": [], "no_effective_change": True, "base_source": None,
    }
    patch_path = os.path.join(task_dir, "reference", "patch.diff")
    if not os.path.isfile(patch_path):
        out["notes"].append("no reference/patch.diff")
        return out
    with open(patch_path, encoding="utf-8", errors="surrogateescape") as f:
        patch_text = f.read()
    fds = parse_patch(patch_text)
    out["files_total"] = len(fds)
    if not fds:
        out["notes"].append("patch parsed to zero file diffs")
        return out

    staged_files = _read_tree(workspace)
    tmpdir = tempfile.mkdtemp(prefix=f"refapply_{task_id}_")
    try:
        base_files, base_src = base_workspace(task_id, task_dir)
        out["base_source"] = base_src

        # ---- Stage 1: apply the diff to the unparameterised base -----------
        applied_base = None
        if base_files:
            base_tree = os.path.join(tmpdir, "base")
            post_tree = os.path.join(tmpdir, "post")
            os.makedirs(base_tree, exist_ok=True)
            _write_files(base_files, base_tree)
            shutil.copytree(base_tree, post_tree, symlinks=True)
            # No `git init` here. `git apply` and `git apply -R --check` both
            # work outside a repository, and the one method that needs one
            # (--3way) also needs upstream blob objects this tree does not have.
            applied_base = apply_to_tree(fds, post_tree, tmpdir)
            for k in ("hunks_total", "hunks_applied", "hunks_already", "hunks_failed",
                      "files_applied", "files_already", "files_failed",
                      "files_out_of_scope", "files_unsupported"):
                out[k] = applied_base[k]
            out["file_outcomes"] = applied_base["files"]
            post_files = _read_tree(post_tree)
            changed = {p for p in applied_base["changed_paths"]}
            deleted = {p for p in applied_base["deleted_paths"]}
            # Any file whose content moved, whether or not the applier said so.
            for p, txt in post_files.items():
                if base_files.get(p) != txt:
                    changed.add(p)
            for p in base_files:
                if p not in post_files:
                    deleted.add(p)

            if applied_base["files_failed"] == 0 and (changed or deleted):
                # ---- Stage 2: express the patched base in the seed's space --
                ref_files, note = reparameterize(task_id, seed, post_files, staged_files)
                if ref_files is not None:
                    method = ("reparam-static" if base_src.startswith("tasks/")
                              else "reparam")
                    out["notes"].append(f"reparam: {note}")
                elif base_src.startswith("tasks/") or staged_files == base_files:
                    # Unparameterised staging: the identity transform is correct.
                    ref_files, method = post_files, "reparam-static"
                    out["notes"].append(f"reparam refused ({note}); "
                                        "staged tree is unparameterised, identity used")
                else:
                    ref_files, method = None, None
                    out["notes"].append(f"reparam refused: {note}")

                if ref_files is not None:
                    wrote = []
                    for p in sorted(changed):
                        if p not in ref_files:
                            continue
                        dst = os.path.join(workspace, p)
                        os.makedirs(os.path.dirname(dst) or workspace, exist_ok=True)
                        with open(dst, "w", encoding="utf-8",
                                  errors="surrogateescape", newline="") as f:
                            f.write(ref_files[p])
                        wrote.append(p)
                    for p in sorted(deleted):
                        dst = os.path.join(workspace, p)
                        if os.path.exists(dst):
                            os.remove(dst)
                            wrote.append(f"-{p}")
                    out["applied"] = True
                    out["method"] = method
                    out["written_paths"] = wrote
                    out["no_effective_change"] = not any(
                        staged_files.get(p) != ref_files.get(p) for p in changed)
                    return out

                # ---- Stage 3: three-way merge into the staged tree ----------
                merged_all, wrote = True, []
                for p in sorted(changed):
                    if p not in post_files or p not in base_files:
                        continue
                    ours = staged_files.get(p)
                    if ours is None:
                        continue
                    m = merge3(base_files[p], ours, post_files[p], tmpdir,
                               re.sub(r"[^A-Za-z0-9]", "_", p))
                    if m is None:
                        merged_all = False
                        break
                    dst = os.path.join(workspace, p)
                    os.makedirs(os.path.dirname(dst) or workspace, exist_ok=True)
                    with open(dst, "w", encoding="utf-8",
                              errors="surrogateescape", newline="") as f:
                        f.write(m)
                    wrote.append(p)
                if merged_all and wrote:
                    out["applied"] = True
                    out["method"] = "merge3"
                    out["written_paths"] = wrote
                    out["no_effective_change"] = False
                    return out
                out["notes"].append("merge3 did not produce a clean merge")

        # ---- Stage 4: direct application into the staged workspace ---------
        direct = apply_to_tree(fds, workspace, tmpdir)
        if applied_base is None:
            for k in ("hunks_total", "hunks_applied", "hunks_already", "hunks_failed",
                      "files_applied", "files_already", "files_failed",
                      "files_out_of_scope", "files_unsupported"):
                out[k] = direct[k]
            out["file_outcomes"] = direct["files"]
        else:
            out["base_apply"] = {k: out[k] for k in
                                 ("hunks_total", "hunks_applied", "hunks_already",
                                  "hunks_failed", "files_applied", "files_already",
                                  "files_failed")}
            out["direct_fallback"] = {k: direct[k] for k in
                                      ("hunks_applied", "hunks_already", "hunks_failed",
                                       "files_applied", "files_already", "files_failed")}
            if direct["files_failed"] == 0:
                # The accepted result came from the direct attempt, so the
                # headline counters must describe that attempt, not the
                # abandoned base attempt. The base attempt is kept under
                # "base_apply" so the two are never confused.
                for k in ("hunks_total", "hunks_applied", "hunks_already",
                          "hunks_failed", "files_applied", "files_already",
                          "files_failed", "files_out_of_scope", "files_unsupported"):
                    out[k] = direct[k]
                out["file_outcomes"] = direct["files"]
        out["applied"] = direct["files_failed"] == 0
        out["method"] = "direct" if out["applied"] else None
        out["written_paths"] = direct["changed_paths"]
        out["no_effective_change"] = not direct["changed_paths"] and not direct["deleted_paths"]
        if not out["applied"]:
            out["notes"].append(
                f"{direct['files_failed']} file diff(s) could not be applied by any method")
        return out
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
