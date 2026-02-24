"""
TeamBench Task Generator Framework.

Provides parameterized, seed-aware task generation for contamination resistance
and scale. Each seed produces a genuinely different task instance with different
data, bugs, expected values, and corpus content.

Usage:
    from generators.registry import get_generator
    gen = get_generator("D1_schema_drift")
    gen.generate(seed=42, workspace_dir="path/to/workspace", reports_dir="path/to/reports")
"""
