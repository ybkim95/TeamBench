"""
TeamBench CLI — `teambench` entry point.

Uses click for a self-documenting, professional CLI.

Usage examples:
    teambench run --model gemini-3-flash-preview
    teambench run --model gpt-4o --tasks S1_hidden_spec D1_schema_drift --seeds 0
    teambench list-tasks --category SEC --difficulty hard
    teambench list-models
    teambench generate --task S1_hidden_spec --seed 0 --output-dir /tmp/out
    teambench grade --task S1_hidden_spec --run-dir /tmp/run
    teambench validate --task S1_hidden_spec --seeds 0 1 2
    teambench info --task S1_hidden_spec
    teambench submit result.json
"""
from __future__ import annotations

import json
import os
import sys

import click


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_dotenv(repo_root: str) -> None:
    env_path = os.path.join(repo_root, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _echo_ok(msg: str) -> None:
    """Print a success-styled message (green if rich is available)."""
    try:
        from rich.console import Console
        Console().print(f"[green]✓[/green] {msg}")
    except ImportError:
        click.echo(f"OK  {msg}")


def _echo_err(msg: str) -> None:
    """Print an error-styled message (red if rich is available)."""
    try:
        from rich.console import Console
        Console().print(f"[red]✗[/red] {msg}")
    except ImportError:
        click.echo(f"ERR {msg}", err=True)


def _echo_info(msg: str) -> None:
    """Print an info-styled message (cyan if rich is available)."""
    try:
        from rich.console import Console
        Console().print(f"[cyan]→[/cyan] {msg}")
    except ImportError:
        click.echo(f"    {msg}")


def _load_task_yaml(task_dir: str) -> dict:
    """Load task.yaml from a task directory. Returns {} on failure."""
    yaml_path = os.path.join(task_dir, "task.yaml")
    if not os.path.isfile(yaml_path):
        return {}
    try:
        import yaml  # type: ignore[import]
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Minimal fallback parser for simple key: value lines
        data: dict = {}
        with open(yaml_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                k, _, v = line.partition(":")
                v = v.strip()
                # Parse inline lists like [python, bash]
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip() for x in v[1:-1].split(",") if x.strip()]  # type: ignore[assignment]
                data[k.strip()] = v
        return data


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="0.1.0", prog_name="teambench")
def main() -> None:
    """TeamBench — multi-agent LLM benchmark with OS-enforced role separation.

    Evaluate model teams across 100+ tasks spanning security, data engineering,
    incident response, SWE, and more. Metrics include TNI, planning value, and
    verification value.
    """


# ---------------------------------------------------------------------------
# teambench run
# ---------------------------------------------------------------------------

@main.command("run")
@click.option(
    "--model", required=True,
    help="Model name (e.g. gpt-4o, gemini-3-flash-preview, claude-3-5-sonnet).",
)
@click.option(
    "--tasks", multiple=True, metavar="TASK",
    help="Task IDs to run. Repeat for multiple. Default: all tasks.",
)
@click.option(
    "--seeds", multiple=True, type=int, default=(0, 1, 2), show_default=True,
    help="Random seeds. Repeat for multiple (e.g. --seeds 0 --seeds 1).",
)
@click.option(
    "--conditions", multiple=True,
    default=("oracle", "restricted", "full", "team_no_plan", "team_no_verify"),
    show_default=True,
    help="Ablation conditions to run. Repeat for multiple.",
)
@click.option(
    "--tasks-dir", default="tasks", show_default=True,
    help="Directory containing task folders.",
)
@click.option(
    "--output-dir", default="shared/leaderboard", show_default=True,
    help="Directory where the leaderboard JSON is written.",
)
@click.option(
    "--max-turns", type=int, default=20, show_default=True,
    help="Maximum turns per agent phase.",
)
@click.option(
    "--max-remediation", type=int, default=2, show_default=True,
    help="Maximum remediation loops.",
)
@click.option(
    "--dry-run", is_flag=True,
    help="Skip agent execution; grade the initial workspace state only (useful for testing).",
)
def cmd_run(
    model: str,
    tasks: tuple[str, ...],
    seeds: tuple[int, ...],
    conditions: tuple[str, ...],
    tasks_dir: str,
    output_dir: str,
    max_turns: int,
    max_remediation: int,
    dry_run: bool,
) -> None:
    """Run the full evaluation pipeline for a model.

    Executes each ablation condition for every task/seed combination and writes
    a standardized leaderboard JSON file under OUTPUT_DIR.

    \b
    Examples:
      teambench run --model gpt-4o
      teambench run --model gemini-3-flash-preview --tasks S1_hidden_spec --seeds 0
      teambench run --model gpt-4o --conditions oracle full --dry-run
    """
    root = _repo_root()
    _load_dotenv(root)
    sys.path.insert(0, root)

    from harness.run_all import discover_tasks
    from harness.ablation import AblationCondition

    # Import run_leaderboard from scripts/ — add scripts/ to path
    sys.path.insert(0, os.path.join(root, "scripts"))
    from run_leaderboard import run_leaderboard  # type: ignore[import]

    tasks_dir_abs = os.path.abspath(tasks_dir)
    task_names = list(tasks) if tasks else discover_tasks(tasks_dir_abs)
    if not task_names:
        _echo_err(f"No tasks found in {tasks_dir_abs}")
        sys.exit(1)

    valid_conditions = {c.value for c in AblationCondition}
    bad = [c for c in conditions if c not in valid_conditions]
    if bad:
        _echo_err(f"Unknown conditions: {bad}")
        _echo_info(f"Valid conditions: {sorted(valid_conditions)}")
        sys.exit(1)

    ablation_conditions = [AblationCondition(c) for c in conditions]

    run_leaderboard(
        model=model,
        task_names=task_names,
        seeds=list(seeds),
        tasks_dir=tasks_dir_abs,
        output_dir=os.path.abspath(output_dir),
        conditions=ablation_conditions,
        max_turns=max_turns,
        max_remediation=max_remediation,
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# teambench list-tasks
# ---------------------------------------------------------------------------

@main.command("list-tasks")
@click.option("--category", default=None, help="Filter by category/domain prefix (e.g. SEC, DATA, INC).")
@click.option(
    "--difficulty", default=None,
    type=click.Choice(["easy", "medium", "hard", "expert"], case_sensitive=False),
    help="Filter by difficulty level.",
)
@click.option(
    "--tasks-dir", default="tasks", show_default=True,
    help="Directory containing task folders.",
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON.")
def cmd_list_tasks(
    category: str | None,
    difficulty: str | None,
    tasks_dir: str,
    output_json: bool,
) -> None:
    """List all available tasks with metadata.

    \b
    Examples:
      teambench list-tasks
      teambench list-tasks --category SEC --difficulty hard
      teambench list-tasks --json | jq '.[].task_id'
    """
    root = _repo_root()
    sys.path.insert(0, root)

    from harness.run_all import discover_tasks

    tasks_dir_abs = os.path.abspath(tasks_dir)
    all_tasks = discover_tasks(tasks_dir_abs)

    rows = []
    for tid in all_tasks:
        task_dir = os.path.join(tasks_dir_abs, tid)
        meta = _load_task_yaml(task_dir)

        task_category = (meta.get("category") or meta.get("domain") or "").upper()
        task_diff = (meta.get("difficulty") or "").lower()
        langs = meta.get("languages") or []
        if isinstance(langs, str):
            langs = [langs]

        if category and not task_category.startswith(category.upper()):
            continue
        if difficulty and task_diff != difficulty.lower():
            continue

        rows.append({
            "task_id": tid,
            "category": task_category,
            "difficulty": task_diff,
            "languages": langs,
            "parameterized": bool(meta.get("parameterized")),
            "seeds": meta.get("seeds") or [],
        })

    if output_json:
        click.echo(json.dumps(rows, indent=2))
        return

    if not rows:
        click.echo("No tasks match the given filters.")
        return

    col_w = 42
    header = f"{'TASK_ID':<{col_w}} {'CAT':<10} {'DIFF':<8} {'LANGUAGES':<22} PARAM"
    click.echo(header)
    click.echo("-" * (col_w + 10 + 8 + 22 + 8))
    for r in rows:
        click.echo(
            f"{r['task_id']:<{col_w}}"
            f"{r['category']:<10}"
            f"{r['difficulty']:<8}"
            f"{','.join(r['languages']):<22}"
            f"{'yes' if r['parameterized'] else 'no'}"
        )
    click.echo(f"\n{len(rows)} task(s) listed.")


# ---------------------------------------------------------------------------
# teambench list-models
# ---------------------------------------------------------------------------

@main.command("list-models")
def cmd_list_models() -> None:
    """List supported model backends and example model names.

    Each backend requires its own SDK package and API key environment variable.
    Install backend packages with: pip install teambench[<backend>]
    """
    backends = [
        {
            "backend": "gemini",
            "extra": "gemini",
            "package": "google-genai>=1.0",
            "env_var": "GEMINI_API_KEY",
            "prefix": "gemini-*",
            "examples": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-2.5-flash"],
        },
        {
            "backend": "openai",
            "extra": "openai",
            "package": "openai>=1.0",
            "env_var": "OPENAI_API_KEY",
            "prefix": "gpt-*, o1, o3, o4",
            "examples": ["gpt-4o", "gpt-4o-mini", "o3", "o4-mini"],
        },
        {
            "backend": "anthropic",
            "extra": "anthropic",
            "package": "anthropic>=0.20",
            "env_var": "ANTHROPIC_API_KEY",
            "prefix": "claude-*",
            "examples": ["claude-opus-4-5", "claude-sonnet-4-5", "claude-3-5-haiku"],
        },
        {
            "backend": "mock",
            "extra": None,
            "package": "(built-in)",
            "env_var": "(none required)",
            "prefix": "mock*",
            "examples": ["mock", "mock-fast"],
        },
    ]

    click.echo("Supported model backends:\n")
    for b in backends:
        click.echo(f"  Backend:  {b['backend']}")
        if b["extra"]:
            click.echo(f"  Install:  pip install teambench[{b['extra']}]")
        else:
            click.echo(f"  Install:  (no extra package needed)")
        click.echo(f"  Env var:  {b['env_var']}")
        click.echo(f"  Prefix:   {b['prefix']}")
        click.echo(f"  Models:   {', '.join(b['examples'])}")
        click.echo()

    click.echo("Model name prefix routing (harness/adapters/__init__.py):")
    click.echo("  gemini-*           -> GeminiAdapter")
    click.echo("  gpt-*, o1, o3, o4  -> OpenAIAdapter")
    click.echo("  claude-*           -> AnthropicAdapter")
    click.echo("  mock*              -> MockAdapter (for local testing)")


# ---------------------------------------------------------------------------
# teambench generate
# ---------------------------------------------------------------------------

@main.command("generate")
@click.option("--task", required=True, help="Task ID (e.g. S1_hidden_spec).")
@click.option("--seed", type=int, default=0, show_default=True, help="Random seed.")
@click.option(
    "--output-dir", required=True,
    help="Directory to write the generated instance. Creates workspace/ and reports/ subdirectories.",
)
def cmd_generate(task: str, seed: int, output_dir: str) -> None:
    """Generate a task instance using its parameterized generator.

    Writes workspace files, spec.md, brief.md, and expected.json into
    OUTPUT_DIR/workspace/ and OUTPUT_DIR/reports/.

    \b
    Examples:
      teambench generate --task S1_hidden_spec --seed 0 --output-dir /tmp/s1_seed0
      teambench generate --task D1_schema_drift --seed 2 --output-dir /tmp/d1_seed2
    """
    root = _repo_root()
    sys.path.insert(0, root)

    from generators.registry import has_generator, get_generator

    if not has_generator(task):
        _echo_err(f"No generator found for task '{task}'.")
        _echo_info("Use 'teambench list-tasks' to see available tasks.")
        sys.exit(1)

    output_dir_abs = os.path.abspath(output_dir)
    workspace_dir = os.path.join(output_dir_abs, "workspace")
    reports_dir = os.path.join(output_dir_abs, "reports")
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    try:
        gen = get_generator(task)
        result = gen.generate(seed=seed)
        gen.write_to_disk(result, workspace_dir=workspace_dir, reports_dir=reports_dir)
    except Exception as exc:
        _echo_err(f"Generator failed: {exc}")
        sys.exit(1)

    _echo_ok(f"Generated '{task}' (seed={seed})")
    _echo_info(f"Workspace: {workspace_dir}")
    _echo_info(f"Reports:   {reports_dir}")

    click.echo("\nGenerated files:")
    for dirpath, _, filenames in os.walk(output_dir_abs):
        for fname in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, fname), output_dir_abs)
            click.echo(f"  {rel}")


# ---------------------------------------------------------------------------
# teambench grade
# ---------------------------------------------------------------------------

@main.command("grade")
@click.option("--task", required=True, help="Task ID.")
@click.option(
    "--run-dir", required=True,
    help="Run directory containing workspace/ and reports/ subdirectories.",
)
@click.option(
    "--tasks-dir", default="tasks", show_default=True,
    help="Directory containing task folders.",
)
def cmd_grade(task: str, run_dir: str, tasks_dir: str) -> None:
    """Grade a completed run directory.

    Runs the task's grade.sh and prints the resulting score JSON.

    \b
    Examples:
      teambench grade --task S1_hidden_spec --run-dir shared/runs/S1_hidden_spec/20240101_abc123
    """
    root = _repo_root()
    sys.path.insert(0, root)

    from harness.run_all import grade_run

    tasks_dir_abs = os.path.abspath(tasks_dir)
    task_dir = os.path.join(tasks_dir_abs, task)
    run_dir_abs = os.path.abspath(run_dir)

    if not os.path.isdir(task_dir):
        _echo_err(f"Task directory not found: {task_dir}")
        sys.exit(1)
    if not os.path.isdir(run_dir_abs):
        _echo_err(f"Run directory not found: {run_dir_abs}")
        sys.exit(1)

    try:
        score = grade_run(task, task_dir, run_dir_abs)
    except Exception as exc:
        _echo_err(f"Grading failed: {exc}")
        sys.exit(1)

    passed = score.get("pass", False)
    partial = float(
        score.get("secondary", {}).get("partial_score", 1.0 if passed else 0.0)
    )
    status_label = "PASS" if passed else "FAIL"

    click.echo(f"\nGrade result — {task}")
    click.echo(f"  Status:        {status_label}")
    click.echo(f"  Partial score: {partial:.3f}")

    failure_modes = score.get("failure_modes", [])
    if failure_modes:
        click.echo(f"  Failure modes: {', '.join(failure_modes)}")

    secondary = {k: v for k, v in score.get("secondary", {}).items() if k != "partial_score"}
    if secondary:
        click.echo("  Other metrics:")
        for k, v in secondary.items():
            click.echo(f"    {k}: {v}")

    click.echo("\nFull score JSON:")
    click.echo(json.dumps(score, indent=2))


# ---------------------------------------------------------------------------
# teambench validate
# ---------------------------------------------------------------------------

@main.command("validate")
@click.option("--task", required=True, help="Task ID.")
@click.option(
    "--seeds", multiple=True, type=int, default=(0, 1, 2), show_default=True,
    help="Seeds to validate. Repeat for multiple.",
)
def cmd_validate(task: str, seeds: tuple[int, ...]) -> None:
    """Validate cross-seed uniqueness for a task generator.

    Checks that:
    - The same seed always produces identical output (determinism / reproducibility).
    - Different seeds produce genuinely different instances (contamination resistance).

    \b
    Examples:
      teambench validate --task S1_hidden_spec
      teambench validate --task D1_schema_drift --seeds 0 --seeds 1 --seeds 2
    """
    root = _repo_root()
    sys.path.insert(0, root)

    from generators.registry import has_generator, get_generator

    if not has_generator(task):
        _echo_err(f"No generator found for task '{task}'.")
        sys.exit(1)

    _echo_info(f"Validating generator for '{task}' across seeds {list(seeds)} ...")

    gen = get_generator(task)
    results: list[tuple[int, object]] = []
    errors: list[str] = []

    for seed in seeds:
        try:
            r1 = gen.generate(seed=seed)
            r2 = gen.generate(seed=seed)
        except Exception as exc:
            errors.append(f"seed={seed}: generation failed — {exc}")
            continue

        if r1.workspace_files != r2.workspace_files:
            errors.append(
                f"seed={seed}: non-deterministic — workspace_files differ between two calls"
            )
        elif r1.expected != r2.expected:
            errors.append(
                f"seed={seed}: non-deterministic — expected.json differs between two calls"
            )
        else:
            _echo_ok(f"seed={seed}: deterministic")

        results.append((seed, r1))

    # Cross-seed uniqueness
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            s_i, r_i = results[i]
            s_j, r_j = results[j]
            if r_i.workspace_files == r_j.workspace_files:  # type: ignore[union-attr]
                errors.append(
                    f"seeds {s_i} and {s_j} produce identical workspace files — "
                    "seed is not influencing output"
                )
            elif r_i.expected == r_j.expected:  # type: ignore[union-attr]
                errors.append(
                    f"seeds {s_i} and {s_j} produce identical expected.json — "
                    "grading targets are not seed-varied"
                )
            else:
                _echo_ok(f"seeds {s_i} vs {s_j}: unique")

    if errors:
        click.echo(f"\n{len(errors)} validation error(s):")
        for e in errors:
            _echo_err(e)
        sys.exit(1)
    else:
        _echo_ok(f"All {len(seeds)} seed(s) passed validation.")


# ---------------------------------------------------------------------------
# teambench info
# ---------------------------------------------------------------------------

@main.command("info")
@click.option("--task", required=True, help="Task ID.")
@click.option(
    "--tasks-dir", default="tasks", show_default=True,
    help="Directory containing task folders.",
)
def cmd_info(task: str, tasks_dir: str) -> None:
    """Show detailed metadata for a task.

    Reads task.yaml and reports difficulty, domain, languages, file list, and
    whether a parameterized generator exists.

    \b
    Examples:
      teambench info --task S1_hidden_spec
      teambench info --task CRYPTO1_nonce_reuse
    """
    root = _repo_root()
    sys.path.insert(0, root)

    from generators.registry import has_generator

    tasks_dir_abs = os.path.abspath(tasks_dir)
    task_dir = os.path.join(tasks_dir_abs, task)

    if not os.path.isdir(task_dir):
        _echo_err(f"Task not found: {task}")
        _echo_info(f"Searched in: {tasks_dir_abs}")
        sys.exit(1)

    meta = _load_task_yaml(task_dir)

    click.echo(f"\nTask: {task}")
    click.echo("=" * 52)

    display_fields = [
        ("task_id", "Task ID"),
        ("category", "Category"),
        ("domain", "Domain"),
        ("difficulty", "Difficulty"),
        ("languages", "Languages"),
        ("parameterized", "Parameterized"),
        ("seeds", "Seeds"),
        ("time_limit_sec", "Time limit (s)"),
        ("network", "Network access"),
        ("tni_pattern", "TNI pattern"),
        ("description", "Description"),
        ("tags", "Tags"),
    ]

    for key, label in display_fields:
        val = meta.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        click.echo(f"  {label:<22} {val}")

    click.echo(f"  {'Has generator':<22} {'yes' if has_generator(task) else 'no'}")

    click.echo(f"\n  Files in task dir:")
    for fname in sorted(os.listdir(task_dir)):
        fpath = os.path.join(task_dir, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            click.echo(f"    {fname}  ({size:,} bytes)")
        else:
            click.echo(f"    {fname}/  (directory)")


# ---------------------------------------------------------------------------
# teambench submit
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = frozenset({"schema_version", "model", "completed", "aggregate", "per_task"})


@main.command("submit")
@click.argument("result_file", metavar="RESULT_JSON", type=click.Path(exists=True))
def cmd_submit(result_file: str) -> None:
    """Validate a result JSON file and print submission instructions.

    RESULT_JSON must be a leaderboard JSON produced by 'teambench run'.
    Checks schema version, required fields, and aggregate integrity before
    printing submission steps.

    \b
    Examples:
      teambench submit shared/leaderboard/leaderboard_gpt-4o.json
    """
    with open(result_file, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            _echo_err(f"Invalid JSON: {exc}")
            sys.exit(1)

    errors: list[str] = []

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"Missing required top-level keys: {sorted(missing)}")

    schema_ver = data.get("schema_version")
    if schema_ver != "1.0":
        errors.append(f"Unexpected schema_version '{schema_ver}' (expected '1.0')")

    model = data.get("model", "")
    if not model:
        errors.append("'model' field is empty or missing")

    agg = data.get("aggregate", {})
    if not isinstance(agg, dict):
        errors.append("'aggregate' must be a dict")
    else:
        for k in ("task_count", "run_count", "avg_oracle", "avg_team"):
            if k not in agg:
                errors.append(f"aggregate.{k} is missing")

    per_task = data.get("per_task", [])
    if not isinstance(per_task, list) or len(per_task) == 0:
        errors.append("'per_task' must be a non-empty list")

    if errors:
        click.echo(f"\n{len(errors)} validation error(s):")
        for e in errors:
            _echo_err(e)
        sys.exit(1)

    _echo_ok(f"Result file passes schema validation (schema_version={schema_ver})")
    click.echo(f"\n  Model:         {model}")
    click.echo(f"  Completed:     {data.get('completed', 'N/A')}")
    click.echo(f"  Tasks:         {agg.get('task_count', 'N/A')}")
    click.echo(f"  Total runs:    {agg.get('run_count', 'N/A')}")
    click.echo(f"  Avg Oracle:    {agg.get('avg_oracle', 'N/A')}")
    click.echo(f"  Avg Team:      {agg.get('avg_team', 'N/A')}")
    click.echo(f"  Avg TNI:       {agg.get('avg_tni', 'N/A')}")
    team_wins = agg.get('team_helps_count', 'N/A')
    task_count = agg.get('task_count', 'N/A')
    click.echo(f"  Team > Oracle: {team_wins}/{task_count}")

    safe_model = model.replace("/", "_").replace(":", "_")
    click.echo("\nSubmission instructions:")
    click.echo("  1. Commit your result file to your fork.")
    click.echo("  2. Place the result file at:  shared/ablation_results/lb90_<your_model>_seed0.json")
    click.echo("  3. Open a pull request to the main TeamBench repository.")
    click.echo("  4. Maintainers manually re-run the deterministic graders to verify your submission")
    click.echo("     before adding the model to the leaderboard.")
    click.echo(f"\n  Suggested path: shared/ablation_results/lb90_{safe_model}_seed0.json")


if __name__ == "__main__":
    main()
