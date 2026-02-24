"""
TeamBench schemas for messages, attestations, and scoring.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Message:
    ts: str
    role: str  # planner | executor | verifier
    type: str  # message | command | artifact | attestation
    content: str = ""
    to: str = ""
    cmd: str = ""
    cwd: str = ""
    exit_code: Optional[int] = None
    path: str = ""
    sha256: str = ""

    def to_jsonl(self) -> str:
        d = {k: v for k, v in asdict(self).items() if v != "" and v is not None}
        return json.dumps(d, ensure_ascii=False)


@dataclass
class ChecklistItem:
    id: str
    ok: bool
    note: str = ""


@dataclass
class Attestation:
    task_id: str
    run_id: str
    verdict: str  # pass | fail
    checklist: list[ChecklistItem] = field(default_factory=list)
    workspace_sha256: str = ""
    reports_sha256: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "verdict": self.verdict,
            "checklist": [asdict(c) for c in self.checklist],
            "workspace_sha256": self.workspace_sha256,
            "reports_sha256": self.reports_sha256,
        }


@dataclass
class Score:
    passed: bool
    primary: dict = field(default_factory=lambda: {"success": 0})
    secondary: dict = field(default_factory=dict)
    failure_modes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pass": self.passed,
            "primary": self.primary,
            "secondary": self.secondary,
            "failure_modes": self.failure_modes,
        }


@dataclass
class TaskConfig:
    task_id: str
    domain: str
    network: bool = False
    time_limit_sec: int = 900
    budget: Optional[int] = None
    seeds: list[int] = field(default_factory=lambda: [0, 1, 2])
    # Enhanced fields (v2)
    difficulty: str = "medium"  # easy | medium | hard | expert
    languages: list[str] = field(default_factory=lambda: ["python"])
    tags: list[str] = field(default_factory=list)
    workspace_file_count: int = 0  # Approximate files in workspace
    lines_changed_expected: int = 0  # Approximate solution size
    parameterized: bool = False  # True if generator exists for this task
