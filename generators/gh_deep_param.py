"""
Deep parameterization infrastructure for GH task generators.

Provides seed-deterministic transformations that go far beyond simple
single-symbol renaming, making cross-seed memorization much harder.

All functions are DETERMINISTIC: same seed → same output.
All functions preserve code correctness: ast.parse still succeeds on Python files.

Usage in a GH generator's generate() method:
    from generators.gh_deep_param import deep_rename_symbols, add_realistic_noise, vary_file_structure

    files = self._base_workspace()
    # ... existing simple rename for backward compat ...
    files = deep_rename_symbols(files, seed)
    files = add_realistic_noise(files, seed, noise_level=0.15)
"""
from __future__ import annotations

import ast
import keyword
import re
import tokenize
import io
from typing import Optional
from generators.primitives import SeededRandom

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Python stdlib top-level module names (not exhaustive, covers common ones)
_STDLIB_MODULES = frozenset({
    "os", "sys", "re", "io", "abc", "ast", "builtins", "collections",
    "contextlib", "copy", "dataclasses", "datetime", "enum", "functools",
    "hashlib", "heapq", "inspect", "itertools", "json", "logging", "math",
    "operator", "pathlib", "pickle", "queue", "random", "shutil", "signal",
    "socket", "string", "struct", "subprocess", "tempfile", "threading",
    "time", "traceback", "typing", "unittest", "urllib", "uuid", "warnings",
    "weakref", "xml", "zipfile", "zlib", "argparse", "configparser",
    "csv", "decimal", "difflib", "fractions", "gc", "getopt", "getpass",
    "glob", "gzip", "html", "http", "imaplib", "importlib", "keyword",
    "locale", "mimetypes", "multiprocessing", "numbers", "optparse",
    "platform", "pprint", "profile", "secrets", "select", "shelve",
    "smtplib", "sqlite3", "ssl", "stat", "statistics", "textwrap",
    "tkinter", "token", "tokenize", "tracemalloc", "tty", "types",
    "unicodedata", "venv", "xmlrpc",
})

# Common third-party library names to preserve
_THIRD_PARTY_PRESERVE = frozenset({
    "numpy", "np", "pandas", "pd", "scipy", "sklearn", "torch", "tf",
    "tensorflow", "keras", "matplotlib", "plt", "seaborn", "sns",
    "requests", "flask", "django", "fastapi", "aiohttp", "asyncio",
    "pytest", "unittest", "mock", "click", "typer", "pydantic",
    "sqlalchemy", "alembic", "celery", "redis", "boto3", "botocore",
    "yaml", "toml", "dotenv", "PIL", "cv2", "transformers", "datasets",
    "ray", "dask", "airflow", "mlflow", "wandb", "optuna",
    "attrs", "attr", "cattrs", "marshmallow", "cerberus",
    "cryptography", "jwt", "passlib", "bcrypt",
    "httpx", "aiofiles", "starlette", "uvicorn", "gunicorn",
    "paramiko", "fabric", "ansible", "docker", "kubernetes",
    "psycopg2", "pymysql", "motor", "pymongo",
    "spacy", "nltk", "gensim", "huggingface_hub",
    "deno", "node", "npm", "cargo", "rustc",
})

# Python builtins to never rename.
#
# This was `frozenset(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))`,
# whose two branches are identical and which, inside an imported module, evaluates
# `dir()` on the builtins DICT rather than the builtins module. It therefore
# returned 45 dict dunder methods instead of the ~150 builtin names, leaving
# `len`, `str`, `set`, `ValueError`, `isinstance` and every stdlib import target
# eligible for renaming. Staged workspaces emitted lines such as
#   from typing import Any_v2, Dict_core, List_ext
# which parse but raise ImportError, so 593 of 650 GitHub-sourced tasks (91.2%)
# could not be executed by any agent under any condition.
#
# Also exclude the standard library's own module names, since the renamer sees
# them as ordinary symbols in `from <module> import <name>` targets.
import builtins as _builtins
import importlib as _importlib
import sys as _sys


def _stdlib_exported_names() -> frozenset:
    """Every public name exported by an importable stdlib module.

    Protecting only builtins and module NAMES is not enough: the renamer also
    sees the targets of `from <stdlib module> import <name>`, which is how
    `from pathlib import Path_base` and `from __future__ import annotations_new`
    were emitted. Those parse and then fail at import.
    """
    # `this` prints the Zen of Python and `antigravity` opens a browser on import.
    # Importing them here would pollute the stdout of every process that loads a
    # generator, including graders whose score is parsed from stdout.
    side_effects = {"this", "antigravity", "idlelib", "turtledemo", "tkinter"}
    # Submodules whose members are imported by name but do not appear in dir() of
    # the parent package: `from unittest.mock import patch`, `from urllib.parse
    # import quote_from_bytes`, `from http.client import HTTPResponse`.
    submodules = [
        "unittest.mock", "urllib.parse", "urllib.request", "urllib.error",
        "http.client", "http.server", "http.cookies", "os.path",
        "collections.abc", "concurrent.futures", "importlib.util",
        "importlib.metadata", "xml.etree.ElementTree", "xml.dom.minidom",
        "email.mime.text", "email.utils", "logging.handlers", "logging.config",
        "json.decoder", "json.encoder", "sqlite3.dbapi2", "multiprocessing.pool",
        "distutils.version", "ctypes.util", "wsgiref.simple_server",
    ]
    names = set()
    for mod in list(_sys.stdlib_module_names) + submodules:
        if mod in side_effects or (mod.startswith("_") and mod != "__future__"):
            continue
        try:
            m = _importlib.import_module(mod)
        except Exception:
            continue  # optional or platform-specific module
        try:
            names.update(n for n in dir(m) if not n.startswith("__"))
        except Exception:
            continue
    return frozenset(names)


_PYTHON_BUILTINS = (
    frozenset(dir(_builtins))
    | frozenset(_sys.stdlib_module_names)
    | _stdlib_exported_names()
    | frozenset({
        # dunder attributes that appear at module scope
        "__name__", "__file__", "__doc__", "__package__", "__spec__",
        "__loader__", "__builtins__", "__all__", "__version__", "__path__",
        # __future__ features, which are import targets but not module members
        "annotations", "division", "print_function", "unicode_literals",
        "absolute_import", "generator_stop", "nested_scopes", "with_statement",
        # typing names newer than the interpreter running the generator, which
        # therefore do not appear in dir(typing) here but do appear in the
        # upstream sources we parameterise
        "Required", "NotRequired", "Unpack", "Self", "TypeAlias", "TypeGuard",
        "LiteralString", "Never", "assert_type", "assert_never", "reveal_type",
        "dataclass_transform", "override", "TypeAliasType", "ParamSpec",
        "Concatenate", "TypedDict", "Annotated", "Final", "final",
    })
)

# Common comment templates for noise injection
_COMMENT_TEMPLATES = [
    "# TODO: refactor this",
    "# handle edge case",
    "# NOTE: this is intentional",
    "# FIXME: review later",
    "# workaround for upstream issue",
    "# see documentation for details",
    "# preserve existing behavior",
    "# check bounds",
    "# validate input",
    "# ensure thread safety",
    "# legacy compatibility",
    "# performance optimization",
    "# temporary fix",
    "# may need update in future version",
    "# consistent with spec",
]

# Synonym mappings for realistic variable renaming
_SYNONYM_GROUPS: list[list[str]] = [
    ["result", "output", "ret", "value", "val"],
    ["index", "idx", "pos", "position", "offset"],
    ["count", "num", "n", "total", "size"],
    ["data", "payload", "content", "body", "info"],
    ["error", "err", "exc", "exception", "failure"],
    ["config", "cfg", "conf", "settings", "options"],
    ["handler", "processor", "worker", "executor", "runner"],
    ["client", "conn", "connection", "session", "transport"],
    ["buffer", "buf", "chunk", "block", "segment"],
    ["message", "msg", "text", "line", "record"],
    ["path", "filepath", "filename", "fpath", "location"],
    ["source", "src", "origin", "input", "from_"],
    ["target", "dst", "dest", "destination", "to_"],
    ["callback", "cb", "hook", "listener", "fn"],
    ["items", "elements", "entries", "records", "rows"],
    ["key", "name", "label", "tag", "identifier"],
    ["mapping", "lookup", "table", "registry", "store"],
    ["wrapper", "proxy", "facade", "adapter", "shim"],
    ["factory", "builder", "creator", "maker", "constructor"],
    ["manager", "controller", "coordinator", "supervisor", "scheduler"],
]

# Build reverse lookup: word → synonym group index
_WORD_TO_GROUP: dict[str, int] = {}
for _gidx, _group in enumerate(_SYNONYM_GROUPS):
    for _word in _group:
        _WORD_TO_GROUP[_word] = _gidx


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def _detect_language(filepath: str) -> str:
    """Return language tag for a given file path."""
    ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
    return {
        "py": "python",
        "go": "go",
        "rs": "rust",
        "ts": "typescript",
        "js": "javascript",
        "tsx": "typescript",
        "jsx": "javascript",
        "svelte": "svelte",
    }.get(ext, "other")


# ---------------------------------------------------------------------------
# Python symbol extraction
# ---------------------------------------------------------------------------

def _extract_python_user_symbols(source: str) -> set[str]:
    """
    Parse Python source and return user-defined identifiers:
    function names, variable names, class names — excluding stdlib/builtins.
    Returns empty set if source fails to parse.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                symbols.add(arg.arg)
            if node.args.vararg:
                symbols.add(node.args.vararg.arg)
            if node.args.kwarg:
                symbols.add(node.args.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            symbols.add(node.name)
        elif isinstance(node, ast.Name):
            symbols.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Only collect the root name, not attribute access
            pass

    # Filter out builtins, stdlib, keywords, short names, dunder names
    filtered: set[str] = set()
    for sym in symbols:
        if sym in _PYTHON_BUILTINS:
            continue
        if sym in _STDLIB_MODULES:
            continue
        if sym in _THIRD_PARTY_PRESERVE:
            continue
        if keyword.iskeyword(sym):
            continue
        if sym.startswith("__") and sym.endswith("__"):
            continue
        if len(sym) <= 1:
            continue
        filtered.add(sym)

    return filtered


# ---------------------------------------------------------------------------
# Rename map generation
# ---------------------------------------------------------------------------

def _build_rename_map(symbols: set[str], seed: int, strategy: str = "synonym") -> dict[str, str]:
    """
    Build a deterministic symbol rename mapping.

    Strategies:
    - "synonym": replace with synonym from same group when available
    - "suffix": append a seed-derived suffix
    - "mixed": combine both
    """
    rng = SeededRandom(seed ^ 0xDEADBEEF)
    rename_map: dict[str, str] = {}

    # Suffix pool derived from seed
    suffix_options = ["_v2", "_impl", "_new", "_base", "_core", "_alt", "_ext", "_mod"]
    rng.shuffle(suffix_options)

    for sym in sorted(symbols):  # sort for determinism
        if strategy in ("synonym", "mixed"):
            if sym in _WORD_TO_GROUP:
                group_idx = _WORD_TO_GROUP[sym]
                group = _SYNONYM_GROUPS[group_idx]
                # Pick a different member of the same group
                candidates = [s for s in group if s != sym]
                if candidates:
                    chosen = rng.choice(candidates)
                    rename_map[sym] = chosen
                    continue

        if strategy in ("suffix", "mixed"):
            # Use a suffix for non-synonym symbols
            suffix = rng.choice(suffix_options)
            rename_map[sym] = sym + suffix

    return rename_map


# ---------------------------------------------------------------------------
# Python rename application (token-aware)
# ---------------------------------------------------------------------------

def _apply_python_renames(source: str, rename_map: dict[str, str]) -> str:
    """
    Apply a rename mapping to Python source code using the tokenizer.
    Only renames NAME tokens (not strings, comments, imports).
    Preserves whitespace exactly.
    """
    if not rename_map:
        return source

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return source  # Can't tokenize; return unchanged

    result_tokens = []
    for tok_type, tok_string, tok_start, tok_end, tok_line in tokens:
        if tok_type == tokenize.NAME and tok_string in rename_map:
            result_tokens.append((tok_type, rename_map[tok_string], tok_start, tok_end, tok_line))
        else:
            result_tokens.append((tok_type, tok_string, tok_start, tok_end, tok_line))

    try:
        return tokenize.untokenize(result_tokens)
    except Exception:
        return source  # Fallback


# ---------------------------------------------------------------------------
# Simple regex-based rename for non-Python files
# ---------------------------------------------------------------------------

def _apply_generic_renames(source: str, rename_map: dict[str, str], lang: str) -> str:
    """
    Apply renames to Go/Rust/JS/TS using whole-word regex replacement.
    Conservative: only replaces identifiers that look like user-defined names.
    """
    if not rename_map:
        return source

    # Sort by length descending to avoid partial replacements
    for old, new in sorted(rename_map.items(), key=lambda x: -len(x[0])):
        # Only match whole word boundaries
        pattern = r'\b' + re.escape(old) + r'\b'
        source = re.sub(pattern, new, source)
    return source


def _extract_generic_user_symbols(source: str, lang: str) -> set[str]:
    """
    Extract user-defined symbols from Go/Rust/JS/TS using simple regex patterns.
    Returns a conservative set (may miss some, but won't accidentally rename stdlib).
    """
    symbols: set[str] = set()

    if lang == "go":
        # func declarations, var declarations, type declarations
        for pat in [
            r'\bfunc\s+(\w+)',
            r'\bvar\s+(\w+)',
            r'\btype\s+(\w+)',
            r'\b(\w+)\s*:=',
        ]:
            symbols.update(re.findall(pat, source))
        # Filter Go builtins
        go_builtins = frozenset({
            "append", "cap", "close", "complex", "copy", "delete", "imag",
            "len", "make", "new", "panic", "print", "println", "real",
            "recover", "bool", "byte", "complex64", "complex128", "error",
            "float32", "float64", "int", "int8", "int16", "int32", "int64",
            "rune", "string", "uint", "uint8", "uint16", "uint32", "uint64",
            "uintptr", "true", "false", "nil", "iota",
            "fmt", "os", "io", "log", "net", "http", "sync", "time",
            "context", "errors", "strings", "strconv", "bytes", "bufio",
            "math", "sort", "reflect", "encoding", "json", "xml",
            "testing", "flag", "path", "filepath", "runtime",
        })
        symbols -= go_builtins

    elif lang == "rust":
        for pat in [
            r'\bfn\s+(\w+)',
            r'\bstruct\s+(\w+)',
            r'\benum\s+(\w+)',
            r'\btype\s+(\w+)',
            r'\blet\s+(?:mut\s+)?(\w+)',
        ]:
            symbols.update(re.findall(pat, source))
        rust_builtins = frozenset({
            "i8", "i16", "i32", "i64", "i128", "isize",
            "u8", "u16", "u32", "u64", "u128", "usize",
            "f32", "f64", "bool", "char", "str", "String",
            "Vec", "Box", "Option", "Result", "Some", "None", "Ok", "Err",
            "Self", "self", "super", "crate", "use", "mod", "pub", "fn",
            "let", "mut", "const", "static", "return", "if", "else",
            "for", "while", "loop", "match", "impl", "trait", "where",
            "println", "eprintln", "print", "eprint", "format",
            "panic", "assert", "assert_eq", "assert_ne",
            "std", "core", "alloc",
        })
        symbols -= rust_builtins

    elif lang in ("javascript", "typescript"):
        for pat in [
            r'\bfunction\s+(\w+)',
            r'\bconst\s+(\w+)',
            r'\blet\s+(\w+)',
            r'\bvar\s+(\w+)',
            r'\bclass\s+(\w+)',
        ]:
            symbols.update(re.findall(pat, source))
        js_builtins = frozenset({
            "undefined", "null", "true", "false", "NaN", "Infinity",
            "console", "process", "require", "module", "exports",
            "Array", "Object", "String", "Number", "Boolean", "Symbol",
            "Promise", "Error", "Map", "Set", "WeakMap", "WeakSet",
            "Date", "RegExp", "JSON", "Math", "parseInt", "parseFloat",
            "setTimeout", "setInterval", "clearTimeout", "clearInterval",
            "fetch", "URL", "URLSearchParams", "Buffer",
            "window", "document", "navigator", "location", "history",
        })
        symbols -= js_builtins

    # Filter short names and underscores
    return {s for s in symbols if len(s) > 2 and not s.startswith("_")}


# ---------------------------------------------------------------------------
# Public API: deep_rename_symbols
# ---------------------------------------------------------------------------

def deep_rename_symbols(
    files: dict[str, str],
    seed: int,
    strategy: str = "mixed",
    min_rename_count: int = 3,
) -> dict[str, str]:
    """
    Rename user-defined identifiers consistently across all files.

    - Parses Python/Go/Rust/JS/TS files to find user-defined names.
    - Builds a consistent rename mapping from the seed.
    - Applies across ALL files (not just one).
    - Preserves: imports, stdlib names, string literals (for Python, via tokenizer).

    Args:
        files: dict mapping filepath -> source content
        seed: deterministic seed for randomization
        strategy: "synonym" | "suffix" | "mixed"
        min_rename_count: minimum symbols to rename (skip if too few found)

    Returns:
        New dict with renamed files. Non-code files passed through unchanged.
    """
    # Step 1: Collect all user-defined symbols across all files
    all_symbols: set[str] = set()
    file_languages: dict[str, str] = {}

    for fpath, content in files.items():
        lang = _detect_language(fpath)
        file_languages[fpath] = lang
        if not isinstance(content, str):
            continue

        if lang == "python":
            syms = _extract_python_user_symbols(content)
        elif lang in ("go", "rust", "javascript", "typescript"):
            syms = _extract_generic_user_symbols(content, lang)
        else:
            syms = set()

        all_symbols.update(syms)

    if len(all_symbols) < min_rename_count:
        # Not enough symbols to safely rename — return unchanged
        return dict(files)

    # Step 2: Build rename map
    rename_map = _build_rename_map(all_symbols, seed, strategy=strategy)

    if not rename_map:
        return dict(files)

    # Step 3: Apply renames across all files
    result: dict[str, str] = {}
    for fpath, content in files.items():
        if not isinstance(content, str):
            result[fpath] = content
            continue

        lang = file_languages[fpath]
        if lang == "python":
            result[fpath] = _apply_python_renames(content, rename_map)
        elif lang in ("go", "rust", "javascript", "typescript", "svelte"):
            result[fpath] = _apply_generic_renames(content, rename_map, lang)
        else:
            result[fpath] = content  # pass through .json, .md, .yml, etc.

    return result


# ---------------------------------------------------------------------------
# Public API: add_realistic_noise
# ---------------------------------------------------------------------------

def add_realistic_noise(
    files: dict[str, str],
    seed: int,
    noise_level: float = 0.2,
) -> dict[str, str]:
    """
    Add realistic code noise that doesn't change semantics:
    - Add/remove blank lines between functions
    - Reorder imports (within groups, preserving semantics)
    - Add realistic inline comments
    - Change string quote style (single ↔ double, where safe)

    All transformations preserve code validity (ast.parse still works for Python).

    Args:
        files: dict mapping filepath -> source content
        seed: deterministic seed for randomization
        noise_level: fraction of opportunities to apply noise (0.0 to 1.0)

    Returns:
        New dict with noise-injected files.
    """
    rng = SeededRandom(seed ^ 0xCAFEBABE)
    result: dict[str, str] = {}

    for fpath, content in files.items():
        if not isinstance(content, str):
            result[fpath] = content
            continue

        lang = _detect_language(fpath)

        if lang == "python":
            content = _noise_python(content, rng, noise_level)
        elif lang in ("go", "rust", "javascript", "typescript"):
            content = _noise_generic(content, rng, noise_level, lang)
        # Other files passed through

        result[fpath] = content

    return result


def _noise_python(source: str, rng: SeededRandom, noise_level: float) -> str:
    """Apply Python-specific noise transformations."""
    lines = source.splitlines(keepends=True)
    output_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip("\n\r")

        # 1. Blank line insertion before function/class defs
        if re.match(r'^(def |async def |class )', stripped.lstrip()):
            if rng.random() < noise_level * 0.5:
                output_lines.append("\n")

        # 2. Comment injection after function signature lines
        if re.match(r'^(def |async def )', stripped.lstrip()) and stripped.endswith(':'):
            output_lines.append(line)
            # Look ahead for docstring or first statement
            if i + 1 < len(lines) and '"""' not in lines[i + 1] and "'''" not in lines[i + 1]:
                if rng.random() < noise_level * 0.4:
                    # Determine indentation of the body
                    indent = _get_body_indent(lines, i + 1)
                    comment = rng.choice(_COMMENT_TEMPLATES)
                    output_lines.append(f"{indent}{comment}\n")
            i += 1
            continue

        # 3. Trailing comment injection on assignment lines
        if (
            "=" in stripped
            and not stripped.startswith("#")
            and not stripped.startswith("def ")
            and not stripped.startswith("class ")
            and not stripped.startswith("import ")
            and not stripped.startswith("from ")
            and rng.random() < noise_level * 0.15
        ):
            comment = rng.choice(_COMMENT_TEMPLATES)
            stripped_no_nl = stripped.rstrip()
            nl = "\n"
            output_lines.append(f"{stripped_no_nl}  {comment}{nl}")
            i += 1
            continue

        output_lines.append(line)
        i += 1

    result = "".join(output_lines)

    # 4. Reorder imports (within import groups at top of file)
    result = _reorder_python_imports(result, rng, noise_level)

    # 5. Validate: if ast.parse fails, return original source
    try:
        ast.parse(result)
    except SyntaxError:
        return source

    return result


def _get_body_indent(lines: list[str], start_idx: int) -> str:
    """Get the indentation of the first non-empty line at or after start_idx."""
    for i in range(start_idx, min(start_idx + 5, len(lines))):
        if lines[i].strip():
            m = re.match(r'^(\s+)', lines[i])
            if m:
                return m.group(1)
    return "    "


def _reorder_python_imports(source: str, rng: SeededRandom, noise_level: float) -> str:
    """
    Reorder imports within contiguous import groups (consecutive import lines).
    Groups of 1 or 2 lines are left alone. Only shuffles within a block.
    """
    lines = source.splitlines(keepends=True)
    result: list[str] = []
    i = 0

    while i < len(lines):
        # Detect start of import block
        if re.match(r'^(import |from )', lines[i]):
            block_start = i
            while i < len(lines) and re.match(r'^(import |from )', lines[i]):
                i += 1
            block = lines[block_start:i]
            if len(block) > 2 and rng.random() < noise_level * 0.6:
                rng.shuffle(block)
            result.extend(block)
        else:
            result.append(lines[i])
            i += 1

    return "".join(result)


def _noise_generic(source: str, rng: SeededRandom, noise_level: float, lang: str) -> str:
    """Apply generic (Go/Rust/JS/TS) noise transformations."""
    lines = source.splitlines(keepends=True)
    output_lines: list[str] = []

    # Comment prefix for the language
    comment_prefix = "//"

    for line in lines:
        stripped = line.rstrip("\n\r")

        # Blank line before function declarations
        is_fn_decl = False
        if lang == "go" and re.match(r'^\s*func\s+', stripped):
            is_fn_decl = True
        elif lang == "rust" and re.match(r'^\s*(pub\s+)?(async\s+)?fn\s+', stripped):
            is_fn_decl = True
        elif lang in ("javascript", "typescript") and re.match(
            r'^\s*(export\s+)?(async\s+)?(function\s+|const\s+\w+\s*=\s*(async\s+)?\()', stripped
        ):
            is_fn_decl = True

        if is_fn_decl and rng.random() < noise_level * 0.4:
            output_lines.append("\n")

        # Inline comment on simple assignments
        if (
            "=" in stripped
            and not stripped.strip().startswith(comment_prefix)
            and not stripped.strip().startswith("//")
            and not stripped.strip().startswith("/*")
            and rng.random() < noise_level * 0.1
        ):
            comment = rng.choice(_COMMENT_TEMPLATES).replace("#", comment_prefix)
            nl = "\n"
            output_lines.append(f"{stripped.rstrip()}  {comment}{nl}")
            continue

        output_lines.append(line)

    return "".join(output_lines)


# ---------------------------------------------------------------------------
# Public API: vary_file_structure
# ---------------------------------------------------------------------------

def vary_file_structure(
    files: dict[str, str],
    seed: int,
) -> dict[str, str]:
    """
    Optionally restructure files: rename files by varying filename suffixes/alternatives.

    This does NOT move functions between files (that would risk breaking imports).
    Instead it renames files where the name is generic enough to have alternatives.

    Args:
        files: dict mapping filepath -> source content
        seed: deterministic seed for randomization

    Returns:
        New dict with potentially renamed file keys. Content unchanged.
    """
    rng = SeededRandom(seed ^ 0xF00DBABE)

    # File renaming alternatives for common generic filenames
    _FILE_RENAMES: dict[str, list[str]] = {
        "utils.py": ["helpers.py", "common.py", "util.py", "shared.py"],
        "utils.go": ["helpers.go", "common.go", "util.go", "shared.go"],
        "utils.rs": ["helpers.rs", "common.rs", "util.rs", "shared.rs"],
        "utils.ts": ["helpers.ts", "common.ts", "util.ts", "shared.ts"],
        "utils.js": ["helpers.js", "common.js", "util.js", "shared.js"],
        "helpers.py": ["utils.py", "common.py", "shared.py", "support.py"],
        "helpers.go": ["utils.go", "common.go", "shared.go", "support.go"],
        "common.py": ["utils.py", "helpers.py", "shared.py", "base.py"],
        "types.py": ["models.py", "schemas.py", "structs.py", "entities.py"],
        "types.ts": ["models.ts", "schemas.ts", "interfaces.ts", "entities.ts"],
        "models.py": ["entities.py", "schemas.py", "types.py", "data.py"],
        "client.py": ["connector.py", "transport.py", "connection.py", "interface.py"],
        "handler.py": ["processor.py", "worker.py", "executor.py", "dispatcher.py"],
        "server.py": ["app.py", "service.py", "main.py", "application.py"],
        "config.py": ["settings.py", "configuration.py", "options.py", "conf.py"],
    }

    result: dict[str, str] = {}

    for fpath, content in files.items():
        # Extract just the basename
        basename = fpath.rsplit("/", 1)[-1] if "/" in fpath else fpath
        prefix = fpath[: -len(basename)] if "/" in fpath else ""

        if basename in _FILE_RENAMES and rng.random() < 0.4:
            alternatives = _FILE_RENAMES[basename]
            new_name = rng.choice(alternatives)
            new_path = prefix + new_name
            # Avoid collision with existing file
            if new_path not in files:
                result[new_path] = content
                continue

        result[fpath] = content

    return result


# ---------------------------------------------------------------------------
# Convenience: apply_all
# ---------------------------------------------------------------------------

def apply_all(
    files: dict[str, str],
    seed: int,
    rename: bool = True,
    noise: bool = True,
    restructure: bool = False,
    noise_level: float = 0.15,
    rename_strategy: str = "mixed",
) -> dict[str, str]:
    """
    Apply all deep parameterization transforms in the recommended order.

    Args:
        files: workspace files dict
        seed: deterministic seed
        rename: whether to apply deep symbol renaming
        noise: whether to add realistic noise
        restructure: whether to vary file structure (disabled by default — can break graders)
        noise_level: noise intensity (0.0–1.0)
        rename_strategy: "synonym" | "suffix" | "mixed"

    Returns:
        Transformed files dict.
    """
    if rename:
        files = deep_rename_symbols(files, seed, strategy=rename_strategy)
    if noise:
        files = add_realistic_noise(files, seed, noise_level=noise_level)
    if restructure:
        files = vary_file_structure(files, seed)
    return files
