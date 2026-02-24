"""
TeamBench utility functions.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import subprocess
from datetime import datetime, timezone


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sh(cmd: list[str], env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(">>", " ".join(cmd))
    if check:
        return subprocess.run(cmd, env=env, check=True, text=True, capture_output=True)
    return subprocess.run(cmd, env=env, check=False, text=True, capture_output=True)


def write_json(path: str, obj: dict) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_sha256(root: str) -> str:
    """Deterministic hash over file contents + relative paths."""
    root_path = pathlib.Path(root)
    h = hashlib.sha256()
    for p in sorted(root_path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root_path)).encode()
            h.update(rel)
            h.update(file_sha256(str(p)).encode())
    return h.hexdigest()


def append_message(messages_dir: str, msg_dict: dict) -> None:
    """Append a message to the dialogue JSONL log."""
    log_path = os.path.join(messages_dir, "dialogue.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg_dict, ensure_ascii=False) + "\n")
