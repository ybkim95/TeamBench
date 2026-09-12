#!/usr/bin/env python3
"""
TeamBench task quality validation pipeline.

Validates that a task meets quality standards before entering the benchmark.
Runs 5 automated gates covering structure, grader discrimination, information
asymmetry, contamination, and produces a summary report.

Usage:
    python scripts/validate_task_quality.py --task SEC1_vuln_patch
    python scripts/validate_task_quality.py --batch SEC1_vuln_patch GH1_flask_session_ctx
    python scripts/validate_task_quality.py --all
    python scripts/validate_task_quality.py --new-only
    python scripts/validate_task_quality.py --task SEC1_vuln_patch --pilot-model gemini-3-flash-preview
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

VALIDATION_REPORTS_DIR = os.path.join(REPO_ROOT, "shared", "validation_reports")

# Gate result constants
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
SKIP = "SKIP"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    name: str
    status: str          # PASS / FAIL / WARN / SKIP
    details: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == PASS


@dataclass
class ValidationReport:
    task_id: str
    timestamp: str
    gates: list[GateResult] = field(default_factory=list)
    recommendation: str = "UNKNOWN"  # ACCEPT / REVISE / REJECT
    summary: dict = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def gate_by_name(self) -> dict[str, GateResult]:
        return {g.name: g for g in self.gates}

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "gates": [
                {
                    "name": g.name,
                    "status": g.status,
                    "details": g.details,
                    "errors": g.errors,
                    "warnings": g.warnings,
                }
                for g in self.gates
            ],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_dir(task_id: str) -> str:
    return os.path.join(REPO_ROOT, "tasks", task_id)


def _grade_sh(task_id: str) -> str:
    return os.path.join(_task_dir(task_id), "grade.sh")


def _tokenize(text: str) -> set[str]:
    """Return lowercase word tokens, excluding stopwords."""
    stopwords = {
        "the", "a", "an", "and", "or", "in", "of", "to", "for",
        "is", "are", "be", "that", "this", "with", "it", "at",
        "by", "on", "as", "if", "was", "from", "your", "you",
    }
    words = re.findall(r"[a-z][a-z0-9_-]{2,}", text.lower())
    return {w for w in words if w not in stopwords}


def _word_overlap(text_a: str, text_b: str) -> tuple[float, float]:
    """
    Return (overlap_ratio, asymmetry_ratio).
    overlap_ratio  = |shared| / |words_in_a|
    asymmetry_ratio = 1 - overlap_ratio  (higher = more info in a not in b)
    """
    words_a = _tokenize(text_a)
    words_b = _tokenize(text_b)
    if not words_a:
        return 0.0, 1.0
    shared = words_a & words_b
    overlap = len(shared) / len(words_a)
    return round(overlap, 4), round(1.0 - overlap, 4)


def _run_grader(task_id: str, workspace: str, reports: str) -> dict:
    """Run grade.sh and return the score dict (or failure sentinel)."""
    grade_script = os.path.abspath(_grade_sh(task_id))
    task_dir_abs = os.path.abspath(_task_dir(task_id))
    submission = os.path.join(reports, "submission")
    os.makedirs(submission, exist_ok=True)

    expected_path = os.path.join(reports, "expected.json")
    grade_args = ["bash", grade_script, workspace, reports, submission, task_dir_abs]
    if os.path.isfile(expected_path):
        grade_args.append(expected_path)

    # Inject venv bin so graders can find pip, mypy, ruff, etc.
    grade_env = os.environ.copy()
    venv_bin = os.path.dirname(os.path.abspath(sys.executable))
    grade_env["PATH"] = venv_bin + os.pathsep + grade_env.get("PATH", "")

    try:
        proc = subprocess.run(
            grade_args,
            capture_output=True, text=True, timeout=120, env=grade_env,
        )
    except subprocess.TimeoutExpired:
        return {"pass": False, "primary": {"success": 0}, "failure_modes": ["grader_timeout"]}
    except Exception as e:
        return {"pass": False, "primary": {"success": 0}, "failure_modes": [f"grader_error: {e}"]}

    score_path = os.path.join(reports, "score.json")
    if os.path.isfile(score_path):
        try:
            return json.loads(open(score_path).read())
        except json.JSONDecodeError:
            pass

    return {"pass": False, "primary": {"success": 0}, "failure_modes": ["grader_no_score"]}


def _primary_score(score_dict: dict) -> float:
    """Extract a scalar [0, 1] primary score from a grade result."""
    if score_dict.get("pass"):
        return 1.0
    primary = score_dict.get("primary", {})
    if isinstance(primary, dict):
        # Look for 'score', 'success', 'partial' keys
        for key in ("score", "partial", "success"):
            v = primary.get(key)
            if isinstance(v, (int, float)):
                return float(v)
    return 0.0


def _seed_diversity_score(lines_a: list[str], lines_b: list[str]) -> float:
    """Fraction of lines that differ between two file-content lists."""
    max_len = max(len(lines_a), len(lines_b), 1)
    diffs = sum(
        1 for i in range(max_len)
        if i >= len(lines_a) or i >= len(lines_b) or lines_a[i] != lines_b[i]
    )
    return round(diffs / max_len, 4)


def _has_generator(task_id: str) -> bool:
    try:
        from generators.registry import has_generator
        return has_generator(task_id)
    except Exception:
        return False


def _get_generator(task_id: str):
    from generators.registry import get_generator
    return get_generator(task_id)


def _static_workspace_files(task_id: str) -> dict[str, str]:
    """Read static workspace files (for tasks without generators)."""
    ws_dir = os.path.join(_task_dir(task_id), "workspace")
    files: dict[str, str] = {}
    if not os.path.isdir(ws_dir):
        return files
    for root, _dirs, fnames in os.walk(ws_dir):
        for fname in fnames:
            abs_path = os.path.join(root, fname)
            rel = os.path.relpath(abs_path, ws_dir)
            try:
                with open(abs_path, "r", errors="replace") as fh:
                    files[rel] = fh.read()
            except Exception:
                files[rel] = ""
    return files


# ---------------------------------------------------------------------------
# Gate 1: Structural Validity
# ---------------------------------------------------------------------------

def gate1_structural(task_id: str) -> GateResult:
    """
    Gate 1: Structural Validity.
    - Generator produces >0 workspace files for seeds 0, 1, 2 (or static workspace is non-empty)
    - Cross-seed produces different content
    - spec.md and brief.md are both non-empty
    - spec.md contains text NOT present in brief.md (information gap exists)
    - grade.sh exists and is valid bash syntax
    - Grader runs on generated workspace without crashing
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    td = _task_dir(task_id)
    has_gen = _has_generator(task_id)
    details["has_generator"] = has_gen

    # --- workspace files ---
    seed_file_counts: dict[int, int] = {}
    generated_tasks: dict[int, object] = {}

    if has_gen:
        try:
            gen = _get_generator(task_id)
        except Exception as e:
            errors.append(f"Failed to load generator: {e}")
            return GateResult("gate1_structural", FAIL, details, errors, warnings)

        for seed in [0, 1, 2]:
            try:
                gt = gen.generate(seed)
                n = len(gt.workspace_files)
                seed_file_counts[seed] = n
                generated_tasks[seed] = gt
                if n == 0:
                    errors.append(f"Seed {seed}: 0 workspace files generated")
            except Exception as e:
                errors.append(f"Seed {seed}: generation failed: {e}")

        # Cross-seed check
        if 0 in generated_tasks and 1 in generated_tasks:
            gt0 = generated_tasks[0]
            gt1 = generated_tasks[1]
            cross_seed_ok = (
                gt0.workspace_files != gt1.workspace_files
                or gt0.expected != gt1.expected
            )
            details["cross_seed_valid"] = cross_seed_ok
            if not cross_seed_ok:
                errors.append("Cross-seed validation failed: seeds 0 and 1 produce identical output")
        else:
            details["cross_seed_valid"] = False

        details["seed_file_counts"] = seed_file_counts

        # spec / brief from seed 0
        if 0 in generated_tasks:
            gt0 = generated_tasks[0]
            spec_text = gt0.spec_md
            brief_text = gt0.brief_md
        else:
            spec_text = ""
            brief_text = ""
    else:
        # Static task — check workspace dir
        ws_files = _static_workspace_files(task_id)
        n = len(ws_files)
        seed_file_counts[0] = n
        details["static_workspace_files"] = n
        details["cross_seed_valid"] = SKIP  # not applicable

        if n == 0:
            errors.append("Static workspace is empty (no files in tasks/{}/workspace/)".format(task_id))

        # Read spec / brief from task dir
        spec_path = os.path.join(td, "spec.md")
        brief_path = os.path.join(td, "brief.md")
        spec_text = open(spec_path).read() if os.path.isfile(spec_path) else ""
        brief_text = open(brief_path).read() if os.path.isfile(brief_path) else ""

    # --- spec.md and brief.md ---
    if not spec_text.strip():
        errors.append("spec.md is empty")
    if not brief_text.strip():
        errors.append("brief.md is empty")
    details["spec_len"] = len(spec_text)
    details["brief_len"] = len(brief_text)

    # Information gap: spec must have content not in brief
    if spec_text.strip() and brief_text.strip():
        spec_words = _tokenize(spec_text)
        brief_words = _tokenize(brief_text)
        unique_to_spec = spec_words - brief_words
        ratio = len(unique_to_spec) / max(len(spec_words), 1)
        details["spec_unique_word_ratio"] = round(ratio, 4)
        if ratio < 0.1:
            errors.append(
                f"spec.md has no unique information vs brief.md "
                f"(unique_word_ratio={ratio:.2f} < 0.10)"
            )

    # --- grade.sh syntax ---
    grade_path = _grade_sh(task_id)
    if not os.path.isfile(grade_path):
        errors.append(f"grade.sh not found at {grade_path}")
        details["grade_sh_exists"] = False
        details["grade_sh_syntax_ok"] = False
    else:
        details["grade_sh_exists"] = True
        try:
            result = subprocess.run(
                ["bash", "-n", grade_path],
                capture_output=True, text=True, timeout=10,
            )
            ok = result.returncode == 0
            details["grade_sh_syntax_ok"] = ok
            if not ok:
                errors.append(f"grade.sh has syntax errors: {result.stderr.strip()}")
        except Exception as e:
            details["grade_sh_syntax_ok"] = False
            errors.append(f"bash -n grade.sh failed: {e}")

    # --- Grader runs without crashing on generated workspace ---
    if details.get("grade_sh_exists") and not errors:
        with tempfile.TemporaryDirectory(prefix="tbq_gate1_") as tmpdir:
            ws = os.path.join(tmpdir, "workspace")
            rpts = os.path.join(tmpdir, "reports")
            os.makedirs(ws, exist_ok=True)
            os.makedirs(rpts, exist_ok=True)

            if has_gen and 0 in generated_tasks:
                gt0 = generated_tasks[0]
                for rel, content in gt0.workspace_files.items():
                    abs_p = os.path.join(ws, rel)
                    os.makedirs(os.path.dirname(abs_p), exist_ok=True)
                    mode = "wb" if isinstance(content, bytes) else "w"
                    open(abs_p, mode).write(content)
                if hasattr(gt0, "expected") and gt0.expected:
                    json.dump(gt0.expected, open(os.path.join(rpts, "expected.json"), "w"), indent=2)
            else:
                src_ws = os.path.join(td, "workspace")
                if os.path.isdir(src_ws):
                    shutil.copytree(src_ws, ws, dirs_exist_ok=True)

            score = _run_grader(task_id, ws, rpts)
            fm = score.get("failure_modes", [])
            crashed = any("error" in m or "crash" in m or "timeout" in m for m in fm)
            details["grader_runs_without_crash"] = not crashed
            if crashed:
                errors.append(f"Grader crashed on generated workspace: {fm}")
    else:
        details["grader_runs_without_crash"] = SKIP

    status = FAIL if errors else PASS
    return GateResult("gate1_structural", status, details, errors, warnings)


# ---------------------------------------------------------------------------
# Gate 2: Grader Discrimination
# ---------------------------------------------------------------------------

def gate2_grader_discrimination(task_id: str) -> GateResult:
    """
    Gate 2: Grader Discrimination.
    - Buggy workspace scores < 1.0
    - Empty submission scores <= 0.1
    - The scores differ (grader discriminates)
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    td = _task_dir(task_id)
    has_gen = _has_generator(task_id)

    with tempfile.TemporaryDirectory(prefix="tbq_gate2_") as tmpdir:
        # --- Buggy workspace score ---
        ws_buggy = os.path.join(tmpdir, "buggy", "workspace")
        rpts_buggy = os.path.join(tmpdir, "buggy", "reports")
        os.makedirs(ws_buggy, exist_ok=True)
        os.makedirs(rpts_buggy, exist_ok=True)

        if has_gen:
            try:
                gen = _get_generator(task_id)
                gt = gen.generate(seed=0)
                for rel, content in gt.workspace_files.items():
                    abs_p = os.path.join(ws_buggy, rel)
                    os.makedirs(os.path.dirname(abs_p), exist_ok=True)
                    mode = "wb" if isinstance(content, bytes) else "w"
                    open(abs_p, mode).write(content)
                if gt.expected:
                    json.dump(gt.expected, open(os.path.join(rpts_buggy, "expected.json"), "w"), indent=2)
            except Exception as e:
                errors.append(f"Failed to generate seed 0 for buggy workspace: {e}")
                return GateResult("gate2_grader_discrimination", FAIL, details, errors, warnings)
        else:
            src_ws = os.path.join(td, "workspace")
            if os.path.isdir(src_ws):
                shutil.copytree(src_ws, ws_buggy, dirs_exist_ok=True)
            else:
                errors.append("No workspace found for grader discrimination test")
                return GateResult("gate2_grader_discrimination", FAIL, details, errors, warnings)

        buggy_score = _run_grader(task_id, ws_buggy, rpts_buggy)
        buggy_primary = _primary_score(buggy_score)
        details["buggy_score"] = buggy_primary
        details["buggy_pass"] = buggy_score.get("pass", False)

        if buggy_primary >= 1.0:
            errors.append(
                f"Buggy workspace scores {buggy_primary:.3f} >= 1.0 — "
                "the grader cannot distinguish buggy from fixed"
            )

        # --- Empty submission score ---
        ws_empty = os.path.join(tmpdir, "empty", "workspace")
        rpts_empty = os.path.join(tmpdir, "empty", "reports")
        os.makedirs(ws_empty, exist_ok=True)
        os.makedirs(rpts_empty, exist_ok=True)

        # Write a failing score.json stub to simulate agent that did nothing
        stub_score = {"pass": False, "primary": {"success": 0}, "secondary": {}}
        json.dump(stub_score, open(os.path.join(rpts_empty, "score.json"), "w"))

        # Create empty workspace (just one sentinel file so grader doesn't error on missing dir)
        open(os.path.join(ws_empty, ".empty"), "w").close()

        empty_score = _run_grader(task_id, ws_empty, rpts_empty)
        empty_primary = _primary_score(empty_score)
        details["empty_score"] = empty_primary

        if empty_primary > 0.1:
            errors.append(
                f"Empty submission scores {empty_primary:.3f} > 0.1 — "
                "grader may be too lenient or scoring constant"
            )

        # --- Discrimination check ---
        discriminates = abs(buggy_primary - empty_primary) > 0.01 or buggy_primary != empty_primary
        # Actually the key check is buggy < 1.0 AND empty <= 0.1 AND they differ
        details["score_difference"] = round(abs(buggy_primary - empty_primary), 4)
        details["grader_discriminates"] = discriminates

        if buggy_primary == empty_primary and buggy_primary > 0:
            warnings.append(
                "Buggy and empty workspace produce identical non-zero scores — "
                "check that grader inspects workspace content"
            )

    status = FAIL if errors else PASS
    return GateResult("gate2_grader_discrimination", status, details, errors, warnings)


# ---------------------------------------------------------------------------
# Gate 3: Information Asymmetry Measurement
# ---------------------------------------------------------------------------

def gate3_information_asymmetry(task_id: str) -> GateResult:
    """
    Gate 3: Information Asymmetry.
    - Compute text overlap between spec.md and brief.md
    - asymmetry_ratio = 1 - (shared_words / spec_words)
    - Flag if asymmetry_ratio < 0.3
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    td = _task_dir(task_id)
    has_gen = _has_generator(task_id)

    if has_gen:
        try:
            gen = _get_generator(task_id)
            gt = gen.generate(seed=0)
            spec_text = gt.spec_md
            brief_text = gt.brief_md
        except Exception as e:
            errors.append(f"Failed to generate seed 0: {e}")
            return GateResult("gate3_information_asymmetry", FAIL, details, errors, warnings)
    else:
        spec_path = os.path.join(td, "spec.md")
        brief_path = os.path.join(td, "brief.md")
        spec_text = open(spec_path).read() if os.path.isfile(spec_path) else ""
        brief_text = open(brief_path).read() if os.path.isfile(brief_path) else ""

    if not spec_text.strip() or not brief_text.strip():
        errors.append("Cannot compute asymmetry: spec.md or brief.md is empty (caught by Gate 1)")
        return GateResult("gate3_information_asymmetry", FAIL, details, errors, warnings)

    overlap_ratio, asymmetry_ratio = _word_overlap(spec_text, brief_text)
    spec_words = len(_tokenize(spec_text))
    brief_words = len(_tokenize(brief_text))
    shared_words = int(round(overlap_ratio * spec_words))

    details["spec_word_count"] = spec_words
    details["brief_word_count"] = brief_words
    details["shared_word_count"] = shared_words
    details["overlap_ratio"] = overlap_ratio
    details["asymmetry_ratio"] = asymmetry_ratio

    if asymmetry_ratio < 0.3:
        errors.append(
            f"Asymmetry ratio {asymmetry_ratio:.3f} < 0.30 — "
            "spec.md and brief.md are too similar; agents won't benefit from role separation"
        )
    elif asymmetry_ratio < 0.5:
        warnings.append(
            f"Asymmetry ratio {asymmetry_ratio:.3f} is marginal (0.30–0.50); "
            "consider making brief.md less detailed"
        )

    status = FAIL if errors else PASS
    return GateResult("gate3_information_asymmetry", status, details, errors, warnings)


# ---------------------------------------------------------------------------
# Gate 4: Contamination Check
# ---------------------------------------------------------------------------

_TEMPLATE_MARKERS = [
    r"__PLACEHOLDER__",
    r"TODO:.*FILL",
    r"<FIXME>",
    r"REPLACE_ME",
    r"YOUR_VALUE_HERE",
    r"<<<.*>>>",
    r"\[INSERT",
    r"TEMPLATE_",
]
_TEMPLATE_RE = re.compile("|".join(_TEMPLATE_MARKERS), re.IGNORECASE)

# {{ var }} is only a marker in non-template file types; HTML/Jinja/Handlebars use it legitimately
_JINJA_RE = re.compile(r"\{\{.*?\}\}")
_TEMPLATE_EXTENSIONS = {".html", ".htm", ".jinja", ".jinja2", ".j2", ".hbs", ".mustache"}


def gate4_contamination(task_id: str) -> GateResult:
    """
    Gate 4: Contamination Check.
    - Check that workspace files don't contain obvious template markers
    - Check that variable names change across seeds (parameterization works)
    - Report seed diversity score = fraction of lines that differ between seed 0 and seed 1
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    has_gen = _has_generator(task_id)

    if has_gen:
        try:
            gen = _get_generator(task_id)
            gt0 = gen.generate(seed=0)
            files0 = {k: v for k, v in gt0.workspace_files.items() if isinstance(v, str)}
        except Exception as e:
            errors.append(f"Failed to generate seed 0: {e}")
            return GateResult("gate4_contamination", FAIL, details, errors, warnings)

        try:
            gt1 = gen.generate(seed=1)
            files1 = {k: v for k, v in gt1.workspace_files.items() if isinstance(v, str)}
        except Exception as e:
            warnings.append(f"Seed 1 generation failed, skipping diversity score: {e}")
            files1 = {}
    else:
        # Static task — only seed 0 is available; read from disk
        files0 = _static_workspace_files(task_id)
        files1 = {}  # No parameterization expected

    # --- Template marker check ---
    template_hits: list[str] = []
    for rel, content in files0.items():
        if not isinstance(content, str):
            continue
        ext = os.path.splitext(rel)[1].lower()
        is_template_file = ext in _TEMPLATE_EXTENSIONS
        for line_no, line in enumerate(content.splitlines(), 1):
            hit = _TEMPLATE_RE.search(line)
            # Only flag {{ }} in non-template files (HTML/Jinja use it legitimately)
            if not hit and not is_template_file:
                hit = _JINJA_RE.search(line)
            if hit:
                template_hits.append(f"{rel}:{line_no}: {line.strip()[:80]}")

    details["template_marker_count"] = len(template_hits)
    if template_hits:
        errors.append(
            f"Found {len(template_hits)} template marker(s) in seed 0 workspace. "
            f"First: {template_hits[0]}"
        )
        details["template_marker_examples"] = template_hits[:3]

    # --- Seed diversity score ---
    if files1:
        # Concatenate all text across files (sorted by key for stability)
        all_keys = sorted(set(files0) | set(files1))
        lines0: list[str] = []
        lines1: list[str] = []
        for key in all_keys:
            lines0.extend(files0.get(key, "").splitlines())
            lines1.extend(files1.get(key, "").splitlines())

        diversity = _seed_diversity_score(lines0, lines1)
        details["seed_diversity_score"] = diversity

        if has_gen and diversity < 0.05:
            errors.append(
                f"Seed diversity score {diversity:.3f} < 0.05 — "
                "seeds 0 and 1 are nearly identical; parameterization may not be working"
            )
        elif has_gen and diversity < 0.15:
            warnings.append(
                f"Seed diversity score {diversity:.3f} is low (< 0.15); "
                "consider varying more content across seeds"
            )
    else:
        if has_gen:
            details["seed_diversity_score"] = None
            warnings.append("Could not compute seed diversity score (seed 1 unavailable)")
        else:
            details["seed_diversity_score"] = SKIP
            details["note"] = "Static task — seed diversity not applicable"

    status = FAIL if errors else PASS
    return GateResult("gate4_contamination", status, details, errors, warnings)


# ---------------------------------------------------------------------------
# Gate 5: Summary / optional pilot model (stub)
# ---------------------------------------------------------------------------

def gate5_summary(
    task_id: str,
    gates: list[GateResult],
    pilot_model: Optional[str] = None,
) -> GateResult:
    """
    Gate 5: Summary Report.
    Aggregates gate results and decides recommendation.
    Optionally runs a model-in-the-loop difficulty calibration (--pilot-model).
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    failed_gates = [g.name for g in gates if not g.passed]
    warned_gates = [g.name for g in gates if g.warnings]
    details["failed_gates"] = failed_gates
    details["warned_gates"] = warned_gates

    n_fail = len(failed_gates)
    if n_fail == 0:
        recommendation = "ACCEPT"
    elif n_fail <= 2:
        recommendation = "REVISE"
    else:
        recommendation = "REJECT"

    details["recommendation"] = recommendation

    if pilot_model:
        details["pilot_model"] = pilot_model
        details["pilot_note"] = (
            "Pilot model calibration is a placeholder. "
            "Pass --pilot-model to enable future difficulty scoring via model inference."
        )
        warnings.append("Pilot model gate is not yet implemented; skipping model inference.")

    status = PASS if n_fail == 0 else (WARN if n_fail <= 2 else FAIL)
    return GateResult("gate5_summary", status, details, errors, warnings)


# ---------------------------------------------------------------------------
# Top-level validate_task
# ---------------------------------------------------------------------------

def validate_task(
    task_id: str,
    pilot_model: Optional[str] = None,
    save_report: bool = True,
) -> ValidationReport:
    """
    Run all 5 quality gates for a task and return a ValidationReport.

    This function is importable so other scripts can call it directly:
        from scripts.validate_task_quality import validate_task
        report = validate_task("SEC1_vuln_patch")
    """
    timestamp = _now_utc()
    gates: list[GateResult] = []

    print(f"\n{'='*65}")
    print(f"  Validating: {task_id}")
    print(f"{'='*65}")

    # Gate 1
    print("  [Gate 1] Structural Validity ...", end=" ", flush=True)
    g1 = gate1_structural(task_id)
    gates.append(g1)
    print(g1.status)
    for e in g1.errors:
        print(f"           ERROR: {e}")
    for w in g1.warnings:
        print(f"           WARN:  {w}")

    # Gate 2
    print("  [Gate 2] Grader Discrimination ...", end=" ", flush=True)
    g2 = gate2_grader_discrimination(task_id)
    gates.append(g2)
    print(g2.status)
    for e in g2.errors:
        print(f"           ERROR: {e}")
    for w in g2.warnings:
        print(f"           WARN:  {w}")

    # Gate 3
    print("  [Gate 3] Information Asymmetry ...", end=" ", flush=True)
    g3 = gate3_information_asymmetry(task_id)
    gates.append(g3)
    print(g3.status)
    for e in g3.errors:
        print(f"           ERROR: {e}")
    for w in g3.warnings:
        print(f"           WARN:  {w}")
    if g3.passed:
        print(f"           asymmetry_ratio = {g3.details.get('asymmetry_ratio', 'N/A')}")

    # Gate 4
    print("  [Gate 4] Contamination Check ...", end=" ", flush=True)
    g4 = gate4_contamination(task_id)
    gates.append(g4)
    print(g4.status)
    for e in g4.errors:
        print(f"           ERROR: {e}")
    for w in g4.warnings:
        print(f"           WARN:  {w}")
    if "seed_diversity_score" in g4.details and g4.details["seed_diversity_score"] not in (None, SKIP):
        print(f"           seed_diversity_score = {g4.details['seed_diversity_score']}")

    # Gate 5 (summary)
    g5 = gate5_summary(task_id, gates, pilot_model=pilot_model)
    gates.append(g5)
    recommendation = g5.details.get("recommendation", "UNKNOWN")

    # Build report
    summary = {
        "gates_passed": sum(1 for g in gates[:4] if g.passed),
        "gates_total": 4,
        "failed_gates": g5.details.get("failed_gates", []),
        "warned_gates": g5.details.get("warned_gates", []),
        "recommendation": recommendation,
    }
    if "buggy_score" in g2.details:
        summary["buggy_score"] = g2.details["buggy_score"]
    if "asymmetry_ratio" in g3.details:
        summary["asymmetry_ratio"] = g3.details["asymmetry_ratio"]
    if "seed_diversity_score" in g4.details:
        summary["seed_diversity_score"] = g4.details["seed_diversity_score"]

    report = ValidationReport(
        task_id=task_id,
        timestamp=timestamp,
        gates=gates,
        recommendation=recommendation,
        summary=summary,
    )

    # Print final verdict
    verdict_line = f"  Recommendation: {recommendation}"
    print(f"\n{'─'*65}")
    print(verdict_line)
    print(f"  Gates passed: {summary['gates_passed']}/{summary['gates_total']}")
    if summary["failed_gates"]:
        print(f"  Failed: {', '.join(summary['failed_gates'])}")
    if summary["warned_gates"]:
        print(f"  Warnings in: {', '.join(summary['warned_gates'])}")
    print(f"{'─'*65}")

    # Save report
    if save_report:
        os.makedirs(VALIDATION_REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(VALIDATION_REPORTS_DIR, f"{task_id}.json")
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"  Report saved: {report_path}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _find_all_tasks() -> list[str]:
    tasks_dir = os.path.join(REPO_ROOT, "tasks")
    tasks = []
    for name in sorted(os.listdir(tasks_dir)):
        if os.path.isfile(os.path.join(tasks_dir, name, "task.yaml")):
            tasks.append(name)
    return tasks


def _find_tasks_without_reports() -> list[str]:
    all_tasks = _find_all_tasks()
    return [
        t for t in all_tasks
        if not os.path.isfile(os.path.join(VALIDATION_REPORTS_DIR, f"{t}.json"))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TeamBench task quality validation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--task", metavar="TASK_ID", help="Validate a single task")
    mode.add_argument("--batch", nargs="+", metavar="TASK_ID", help="Validate multiple tasks")
    mode.add_argument("--all", action="store_true", help="Validate all tasks")
    mode.add_argument("--new-only", action="store_true", help="Validate tasks without existing reports")

    parser.add_argument(
        "--pilot-model", metavar="MODEL",
        help="Optional: run a model-in-the-loop difficulty calibration (Gate 3 extension)"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Do not save reports to shared/validation_reports/"
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Write batch summary JSON to this file"
    )

    args = parser.parse_args()

    if args.task:
        task_ids = [args.task]
    elif args.batch:
        task_ids = args.batch
    elif getattr(args, "all"):
        task_ids = _find_all_tasks()
        if not task_ids:
            print("No tasks found in tasks/ directory.")
            sys.exit(1)
        print(f"Found {len(task_ids)} tasks.")
    else:  # --new-only
        task_ids = _find_tasks_without_reports()
        if not task_ids:
            print("All tasks already have validation reports.")
            sys.exit(0)
        print(f"Found {len(task_ids)} tasks without reports.")

    save = not args.no_save
    reports: list[ValidationReport] = []
    accept = revise = reject = 0

    for task_id in task_ids:
        report = validate_task(task_id, pilot_model=args.pilot_model, save_report=save)
        reports.append(report)
        if report.recommendation == "ACCEPT":
            accept += 1
        elif report.recommendation == "REVISE":
            revise += 1
        else:
            reject += 1

    # Batch summary
    if len(task_ids) > 1:
        print(f"\n{'='*65}")
        print(f"  BATCH SUMMARY  ({len(task_ids)} tasks)")
        print(f"{'='*65}")
        print(f"  ACCEPT: {accept}  |  REVISE: {revise}  |  REJECT: {reject}")
        for r in reports:
            flag = "✓" if r.recommendation == "ACCEPT" else ("~" if r.recommendation == "REVISE" else "✗")
            print(f"  {flag} {r.task_id:40s} {r.recommendation}")

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        batch_summary = {
            "timestamp": _now_utc(),
            "total": len(reports),
            "accept": accept,
            "revise": revise,
            "reject": reject,
            "tasks": [r.to_dict() for r in reports],
        }
        with open(args.output, "w") as f:
            json.dump(batch_summary, f, indent=2)
        print(f"\n  Batch summary written to: {args.output}")

    # Exit code: 0 if all accepted, 1 otherwise
    sys.exit(0 if reject == 0 and revise == 0 else 1)


if __name__ == "__main__":
    main()
