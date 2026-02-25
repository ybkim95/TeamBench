"""
Abstract base class for all TeamBench task generators.

Every task that supports parameterized generation must implement a subclass
of TaskGenerator. The generator produces seed-specific:
  - workspace files (buggy code/data the agent must fix)
  - expected.json (ground-truth values for grading — never seen by agents)
  - spec.md (full specification for Planner/Verifier)
  - brief.md (summary for Executor)
  - corpus files (optional, for IR/Policy tasks)
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeneratedTask:
    """Output of a task generator — everything needed for one task instance."""
    task_id: str
    seed: int
    spec_md: str
    brief_md: str
    expected: dict  # Ground-truth for grading
    workspace_files: dict[str, str | bytes] = field(default_factory=dict)
    corpus_files: dict[str, str] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)  # Difficulty hints, etc.


class TaskGenerator(ABC):
    """
    Abstract base class for parameterized task generators.

    Subclasses must implement generate() which takes a seed and produces
    a complete, self-contained task instance.
    """

    task_id: str
    domain: str
    difficulty: str = "medium"
    languages: list[str] = ["python"]

    @abstractmethod
    def generate(self, seed: int) -> GeneratedTask:
        """
        Generate a complete task instance for the given seed.

        The seed MUST deterministically control all randomness so that:
        - Same seed → identical output (reproducibility)
        - Different seed → genuinely different instance (contamination resistance)

        Returns:
            GeneratedTask with all files and expected values.
        """
        raise NotImplementedError

    def write_to_disk(
        self,
        generated: GeneratedTask,
        workspace_dir: str,
        reports_dir: str,
        task_dir: str = "",
        corpus_dir: str = "",
    ) -> None:
        """Write generated task instance to disk."""
        os.makedirs(workspace_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        # Write workspace files
        for rel_path, content in generated.workspace_files.items():
            abs_path = os.path.join(workspace_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            mode = "wb" if isinstance(content, bytes) else "w"
            with open(abs_path, mode) as f:
                f.write(content)

        # Write expected.json (grader-only, never accessible to agents)
        expected_path = os.path.join(reports_dir, "expected.json")
        with open(expected_path, "w", encoding="utf-8") as f:
            json.dump(generated.expected, f, indent=2, ensure_ascii=False)

        # Write spec.md and brief.md if task_dir provided
        if task_dir:
            os.makedirs(task_dir, exist_ok=True)
            with open(os.path.join(task_dir, "spec.md"), "w") as f:
                f.write(generated.spec_md)
            with open(os.path.join(task_dir, "brief.md"), "w") as f:
                f.write(generated.brief_md)

        # Write corpus files (default to workspace/corpus so graders can find them)
        if generated.corpus_files:
            c_dir = corpus_dir if corpus_dir else (os.path.join(task_dir, "corpus") if task_dir else os.path.join(workspace_dir, "corpus"))
            if c_dir:
                os.makedirs(c_dir, exist_ok=True)
                for rel_path, content in generated.corpus_files.items():
                    abs_path = os.path.join(c_dir, rel_path)
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(content)

    def validate_cross_seed(self, seed_a: int, seed_b: int) -> bool:
        """
        Verify that two seeds produce genuinely different instances.
        Used by contamination resistance tests.
        """
        gen_a = self.generate(seed_a)
        gen_b = self.generate(seed_b)

        # Expected values must differ
        if gen_a.expected == gen_b.expected:
            return False

        # Workspace content must differ
        if gen_a.workspace_files == gen_b.workspace_files:
            return False

        return True
