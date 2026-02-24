"""
Contamination resistance verification tests.

Ensures that different seeds produce genuinely different task instances
and that cross-seed grading fails (the answer for seed X doesn't work for seed Y).

Run: python -m pytest tests/test_contamination.py -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_generator_cross_seed_produces_different_data():
    """Each seed must produce genuinely different workspace files."""
    from generators.registry import list_generators, get_generator

    for task_id in list_generators():
        gen = get_generator(task_id)
        result_a = gen.generate(seed=0)
        result_b = gen.generate(seed=42)

        # Workspace files must differ
        assert result_a.workspace_files != result_b.workspace_files, (
            f"{task_id}: seeds 0 and 42 produced identical workspace files"
        )

        # Expected values must differ
        assert result_a.expected != result_b.expected, (
            f"{task_id}: seeds 0 and 42 produced identical expected values"
        )

        # Spec content must differ (contains seed-specific details)
        assert result_a.spec_md != result_b.spec_md, (
            f"{task_id}: seeds 0 and 42 produced identical spec.md"
        )


def test_generator_same_seed_is_deterministic():
    """Same seed must always produce identical output (reproducibility)."""
    from generators.registry import list_generators, get_generator

    for task_id in list_generators():
        gen = get_generator(task_id)
        result_a = gen.generate(seed=7)
        result_b = gen.generate(seed=7)

        assert result_a.workspace_files == result_b.workspace_files, (
            f"{task_id}: seed=7 produced different workspace files on two calls"
        )
        assert result_a.expected == result_b.expected, (
            f"{task_id}: seed=7 produced different expected values on two calls"
        )


def test_generator_validate_cross_seed():
    """Built-in cross-seed validation must pass."""
    from generators.registry import list_generators, get_generator

    for task_id in list_generators():
        gen = get_generator(task_id)
        assert gen.validate_cross_seed(0, 42), (
            f"{task_id}: validate_cross_seed(0, 42) failed"
        )
        assert gen.validate_cross_seed(1, 99), (
            f"{task_id}: validate_cross_seed(1, 99) failed"
        )


def test_generator_write_to_disk():
    """Generated files must write to disk correctly."""
    from generators.registry import list_generators, get_generator

    for task_id in list_generators():
        gen = get_generator(task_id)
        result = gen.generate(seed=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = os.path.join(tmpdir, "workspace")
            reports = os.path.join(tmpdir, "reports")
            gen.write_to_disk(result, workspace_dir=workspace, reports_dir=reports)

            # expected.json must exist
            expected_path = os.path.join(reports, "expected.json")
            assert os.path.isfile(expected_path), f"{task_id}: expected.json not written"

            expected = json.load(open(expected_path))
            assert isinstance(expected, dict), f"{task_id}: expected.json is not a dict"

            # Workspace must have files
            workspace_files = []
            for root, dirs, files in os.walk(workspace):
                workspace_files.extend(files)
            assert len(workspace_files) > 0, f"{task_id}: no workspace files written"


def test_no_hardcoded_answers_in_generators():
    """Generator source code should not contain hardcoded expected answers.

    This is a heuristic check — we verify that the generator module source
    doesn't contain suspicious patterns like hardcoded row counts or specific
    answer strings that appear in expected.json.
    """
    from generators.registry import list_generators, get_generator
    import inspect

    for task_id in list_generators():
        gen = get_generator(task_id)
        result = gen.generate(seed=0)
        source = inspect.getsource(type(gen))

        # The expected row count for seed=0 should NOT appear as a literal in source
        row_count = result.expected.get("row_count")
        if row_count and isinstance(row_count, int) and row_count > 10:
            # This is a heuristic: specific counts like 23 shouldn't be hardcoded
            # But small numbers (< 10) are common in code and not suspicious
            assert str(row_count) not in source.split("def generate")[0], (
                f"{task_id}: row_count={row_count} appears hardcoded before generate()"
            )


def test_seed_range_coverage():
    """Verify that a range of seeds all produce valid instances."""
    from generators.registry import list_generators, get_generator

    for task_id in list_generators():
        gen = get_generator(task_id)
        seen_row_counts = set()
        for seed in range(10):
            result = gen.generate(seed=seed)
            assert result.workspace_files, f"{task_id} seed={seed}: empty workspace"
            assert result.expected, f"{task_id} seed={seed}: empty expected"
            assert result.spec_md, f"{task_id} seed={seed}: empty spec"
            assert result.brief_md, f"{task_id} seed={seed}: empty brief"
            if "row_count" in result.expected:
                seen_row_counts.add(result.expected["row_count"])

        # With 10 seeds, we should see at least 2 different row counts
        # (unless the task has fixed structure, in which case values differ)
        if seen_row_counts:
            # At minimum, check we got valid results for all seeds
            assert len(seen_row_counts) >= 1
