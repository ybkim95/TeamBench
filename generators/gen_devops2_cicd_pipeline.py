"""
Parameterized generator for DEVOPS2: CI/CD Pipeline Bug Fix.

Each seed produces a different GitHub Actions pipeline domain
(python-api / node-service / go-binary / rust-cli / java-app) with:

  4-5 real bugs (must be fixed):
    B1. wrong_runner_image:   uses ubuntu-18.04 (EOL) instead of ubuntu-latest
    B2. missing_env_var:      step references $SECRET_KEY but env: block is absent
    B3. wrong_artifact_path:  upload-artifact path doesn't match where build writes output
    B4. bad_conditional:      step runs on wrong condition (e.g. always() when should be
                               on success only, or inverted branch check)
    B5. wrong_checkout_depth: shallow clone (fetch-depth: 1) breaks git-describe versioning

  2 flaky-test false alarms (must NOT be changed):
    F1. retry_on_flaky:       a `continue-on-error: true` on an integration test step is
                               intentional — the test is known-flaky and team accepts it
    F2. test_timeout:         a long timeout on a specific test step is intentional —
                               the test legitimately requires extra time

Information asymmetry (TNI pattern B):
  spec.md   — postmortem distinguishing real bugs vs flaky-test false alarms,
               plus exact fixes for each real bug
  brief.md  — "fix the CI pipeline" (no specifics)
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "python-api",
        "language": "Python",
        "runner": "ubuntu-latest",
        "build_tool": "pip",
        "build_cmd": "pip install -e .",
        "test_cmd": "pytest tests/ -v",
        "lint_cmd": "ruff check src/",
        "artifact_dir": "dist/",
        "artifact_wrong": "build/",
        "binary_name": "api-server",
        "secret_var": "DATABASE_URL",
        "secret_step": "Run database migrations",
        "secret_cmd": "python manage.py migrate",
        "version_cmd": "python setup.py --version",
        "integration_test": "pytest tests/integration/ -v --timeout=60",
        "integration_step": "Run integration tests",
        "slow_test": "pytest tests/e2e/ -v",
        "slow_step": "Run e2e tests",
        "slow_timeout": 30,
        "workflow_name": "Python API CI",
        "cache_key": "pip-${{ hashFiles('requirements.txt') }}",
        "cache_path": "~/.cache/pip",
    },
    {
        "name": "node-service",
        "language": "Node.js",
        "runner": "ubuntu-latest",
        "build_tool": "npm",
        "build_cmd": "npm ci && npm run build",
        "test_cmd": "npm test",
        "lint_cmd": "npm run lint",
        "artifact_dir": "dist/",
        "artifact_wrong": ".next/",
        "binary_name": "service-bundle",
        "secret_var": "STRIPE_SECRET_KEY",
        "secret_step": "Run payment service",
        "secret_cmd": "node scripts/verify-payments.js",
        "version_cmd": "node -e \"console.log(require('./package.json').version)\"",
        "integration_test": "npm run test:integration",
        "integration_step": "Run integration tests",
        "slow_test": "npm run test:e2e",
        "slow_step": "Run browser tests",
        "slow_timeout": 45,
        "workflow_name": "Node Service CI",
        "cache_key": "node-${{ hashFiles('package-lock.json') }}",
        "cache_path": "~/.npm",
    },
    {
        "name": "go-binary",
        "language": "Go",
        "runner": "ubuntu-latest",
        "build_tool": "go",
        "build_cmd": "go build -o bin/app ./cmd/app",
        "test_cmd": "go test ./... -v",
        "lint_cmd": "golangci-lint run",
        "artifact_dir": "bin/",
        "artifact_wrong": "build/bin/",
        "binary_name": "app",
        "secret_var": "SIGNING_KEY",
        "secret_step": "Sign binary",
        "secret_cmd": "bash scripts/sign.sh bin/app",
        "version_cmd": "git describe --tags --always",
        "integration_test": "go test ./integration/... -v -timeout 2m",
        "integration_step": "Run integration tests",
        "slow_test": "go test ./bench/... -bench=. -benchtime=30s",
        "slow_step": "Run benchmarks",
        "slow_timeout": 60,
        "workflow_name": "Go Binary CI",
        "cache_key": "go-${{ hashFiles('go.sum') }}",
        "cache_path": "~/go/pkg/mod",
    },
    {
        "name": "rust-cli",
        "language": "Rust",
        "runner": "ubuntu-latest",
        "build_tool": "cargo",
        "build_cmd": "cargo build --release",
        "test_cmd": "cargo test --all",
        "lint_cmd": "cargo clippy -- -D warnings",
        "artifact_dir": "target/release/",
        "artifact_wrong": "target/debug/",
        "binary_name": "cli-tool",
        "secret_var": "CRATES_IO_TOKEN",
        "secret_step": "Publish to crates.io",
        "secret_cmd": "cargo publish --token $CRATES_IO_TOKEN",
        "version_cmd": "cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version'",
        "integration_test": "cargo test --test integration -- --nocapture",
        "integration_step": "Run integration tests",
        "slow_test": "cargo test --test stress -- --nocapture",
        "slow_step": "Run stress tests",
        "slow_timeout": 45,
        "workflow_name": "Rust CLI CI",
        "cache_key": "cargo-${{ hashFiles('Cargo.lock') }}",
        "cache_path": "~/.cargo/registry",
    },
    {
        "name": "java-app",
        "language": "Java",
        "runner": "ubuntu-latest",
        "build_tool": "gradle",
        "build_cmd": "./gradlew build -x test",
        "test_cmd": "./gradlew test",
        "lint_cmd": "./gradlew checkstyle",
        "artifact_dir": "build/libs/",
        "artifact_wrong": "build/classes/",
        "binary_name": "app.jar",
        "secret_var": "NEXUS_PASSWORD",
        "secret_step": "Publish to Nexus",
        "secret_cmd": "./gradlew publish",
        "version_cmd": "./gradlew properties -q | grep 'version:' | awk '{print $2}'",
        "integration_test": "./gradlew integrationTest",
        "integration_step": "Run integration tests",
        "slow_test": "./gradlew performanceTest",
        "slow_step": "Run performance tests",
        "slow_timeout": 60,
        "workflow_name": "Java App CI",
        "cache_key": "gradle-${{ hashFiles('build.gradle') }}",
        "cache_path": "~/.gradle/caches",
    },
]

BUG_SETS = [
    # seed 0: all 5 bugs
    ["wrong_runner_image", "missing_env_var", "wrong_artifact_path", "bad_conditional", "wrong_checkout_depth"],
    # seed 1: 4 bugs (skip wrong_checkout_depth)
    ["wrong_runner_image", "missing_env_var", "wrong_artifact_path", "bad_conditional"],
    # seed 2: 4 bugs (skip bad_conditional)
    ["wrong_runner_image", "missing_env_var", "wrong_artifact_path", "wrong_checkout_depth"],
    # seed 3: 4 bugs (skip wrong_artifact_path)
    ["wrong_runner_image", "missing_env_var", "bad_conditional", "wrong_checkout_depth"],
    # seed 4: 4 bugs (skip missing_env_var)
    ["wrong_runner_image", "wrong_artifact_path", "bad_conditional", "wrong_checkout_depth"],
]


class Generator(TaskGenerator):
    task_id = "DEVOPS2_cicd_pipeline"
    domain = "Pipeline/Integration"
    difficulty = "hard"
    languages = ["yaml", "python"]

    @staticmethod
    def _clean(s: str) -> str:
        """Strip common leading whitespace from every line (handles f-string indent issues)."""
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        bug_set_idx = seed % len(BUG_SETS)
        cfg = DOMAINS[domain_idx]
        bugs = BUG_SETS[bug_set_idx]

        # Seed-parameterized variant values
        wrong_image = rng.choice(["ubuntu-18.04", "ubuntu-20.04"])
        branch_name = rng.choice(["main", "master", "release", "production"])
        node_version = rng.choice(["18", "20", "21"])

        workspace_files = self._make_workspace(cfg, bugs, wrong_image, branch_name)
        spec_md = self._clean(self._make_spec(cfg, bugs, wrong_image, branch_name))
        brief_md = self._clean(self._make_brief(cfg))

        return GeneratedTask(
            task_id="DEVOPS2_cicd_pipeline",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "language": cfg["language"],
                "bugs": bugs,
                "false_alarms": ["retry_on_flaky", "test_timeout"],
                "correct_runner": cfg["runner"],
                "wrong_runner": wrong_image,
                "correct_artifact_dir": cfg["artifact_dir"],
                "wrong_artifact_dir": cfg["artifact_wrong"],
                "branch_name": branch_name,
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "Pipeline/Integration"},
        )

    # ── Workspace file generators ──────────────────────────────────────────────

    def _make_workspace(
        self, cfg: dict, bugs: list, wrong_image: str, branch_name: str
    ) -> dict:
        files = {}
        files[".github/workflows/ci.yml"] = self._make_workflow(
            cfg, bugs, wrong_image, branch_name
        )
        files["postmortem.md"] = self._make_postmortem(cfg, bugs, wrong_image, branch_name)
        files["README.md"] = self._make_readme(cfg)
        return files

    def _make_workflow(
        self, cfg: dict, bugs: list, wrong_image: str, branch_name: str
    ) -> str:
        has_wrong_runner = "wrong_runner_image" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_wrong_depth = "wrong_checkout_depth" in bugs

        runner = wrong_image if has_wrong_runner else cfg["runner"]
        artifact_path = cfg["artifact_wrong"] if has_wrong_artifact else cfg["artifact_dir"]
        checkout_depth = "1" if has_wrong_depth else "0"

        # Build condition for deploy step
        if has_bad_cond:
            # Wrong: always() — runs even on failure
            deploy_condition = "always()"
            deploy_condition_comment = "# BUG B4: always() runs even when tests fail; should be: success() && github.ref == 'refs/heads/{branch_name}'"
        else:
            deploy_condition = f"success() && github.ref == 'refs/heads/{branch_name}'"
            deploy_condition_comment = "# Correct: only deploy on success from the target branch"

        # Build env block for secret step
        if has_missing_env:
            env_block = "      # BUG B2: env block missing — $" + cfg["secret_var"] + " will be empty at runtime"
            env_lines = ""
        else:
            env_block = f"      env:"
            env_lines = f"\n        {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}}"

        workflow = textwrap.dedent(f"""\
            name: {cfg['workflow_name']}

            on:
              push:
                branches: ["{branch_name}", "develop"]
              pull_request:
                branches: ["{branch_name}"]

            jobs:
              build-and-test:
                # BUG B1: {wrong_image} is EOL; should be ubuntu-latest
                runs-on: {runner}

                steps:
                  - name: Checkout code
                    uses: actions/checkout@v4
                    with:
                      # BUG B5: fetch-depth: 1 (shallow clone) breaks git describe versioning
                      # Fix: fetch-depth: 0 to include all tags
                      fetch-depth: {checkout_depth}

                  - name: Cache dependencies
                    uses: actions/cache@v3
                    with:
                      path: {cfg['cache_path']}
                      key: {cfg['cache_key']}

                  - name: Build
                    run: {cfg['build_cmd']}

                  - name: Lint
                    run: {cfg['lint_cmd']}

                  - name: Run unit tests
                    run: {cfg['test_cmd']}

                  - name: {cfg['integration_step']}
                    # INTENTIONAL (F1): continue-on-error is deliberate — this integration
                    # test is known-flaky due to external service dependencies. The team
                    # accepts occasional failures here. Do NOT remove continue-on-error.
                    continue-on-error: true
                    run: {cfg['integration_test']}

                  - name: {cfg['slow_step']}
                    # INTENTIONAL (F2): timeout-minutes: {cfg['slow_timeout']} is correct —
                    # this test legitimately requires extra time. Do NOT reduce the timeout.
                    timeout-minutes: {cfg['slow_timeout']}
                    run: {cfg['slow_test']}

                  - name: Upload build artifacts
                    uses: actions/upload-artifact@v3
                    with:
                      name: build-output
                      # BUG B3: wrong path — build writes to {cfg['artifact_dir']} not {cfg['artifact_wrong']}
                      path: {artifact_path}

                  - name: {cfg['secret_step']}
                    {deploy_condition_comment}
                    if: {deploy_condition}
                    {env_block}{env_lines}
                    run: {cfg['secret_cmd']}
            """)

        return workflow

    def _make_postmortem(
        self, cfg: dict, bugs: list, wrong_image: str, branch_name: str
    ) -> str:
        has_wrong_runner = "wrong_runner_image" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_wrong_depth = "wrong_checkout_depth" in bugs

        real_bugs = []
        if has_wrong_runner:
            real_bugs.append(
                f"- **B1 (wrong_runner_image)**: Pipeline uses `{wrong_image}` (EOL). "
                f"Fix: change to `runs-on: ubuntu-latest`."
            )
        if has_missing_env:
            real_bugs.append(
                f"- **B2 (missing_env_var)**: `{cfg['secret_step']}` step references "
                f"`${cfg['secret_var']}` but no `env:` block injects the secret. "
                f"Fix: add `env: {{ {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}} }}`."
            )
        if has_wrong_artifact:
            real_bugs.append(
                f"- **B3 (wrong_artifact_path)**: `upload-artifact` path is `{cfg['artifact_wrong']}` "
                f"but the build writes to `{cfg['artifact_dir']}`. "
                f"Fix: change `path:` to `{cfg['artifact_dir']}`."
            )
        if has_bad_cond:
            real_bugs.append(
                f"- **B4 (bad_conditional)**: Deploy step has `if: always()` — runs even "
                f"when tests fail, potentially deploying broken code. "
                f"Fix: `if: success() && github.ref == 'refs/heads/{branch_name}'`."
            )
        if has_wrong_depth:
            real_bugs.append(
                "- **B5 (wrong_checkout_depth)**: `fetch-depth: 1` (shallow clone) causes "
                "`git describe` to fail because tags are not fetched. "
                "Fix: `fetch-depth: 0` to include full history and all tags."
            )

        real_section = "\n".join(real_bugs) if real_bugs else "_(none)_"

        return textwrap.dedent(f"""\
            # CI/CD Pipeline Postmortem — {cfg['workflow_name']}

            ## Incident Summary

            Several failures were observed in the CI pipeline for this {cfg['language']} project.
            This postmortem distinguishes genuine configuration bugs from known-acceptable
            test behaviours.

            ## Real Bugs (Must Be Fixed)

            {real_section}

            ## Known-Flaky Tests (Do NOT Change)

            - **F1 (retry_on_flaky)**: The `{cfg['integration_step']}` step has
              `continue-on-error: true`. This is **intentional** — this test occasionally
              fails due to unreliable external service dependencies. The team has accepted
              this flakiness. Removing `continue-on-error` would cause valid CI runs to
              fail on transient network issues.

            - **F2 (test_timeout)**: The `{cfg['slow_step']}` step has
              `timeout-minutes: {cfg['slow_timeout']}`. This is **intentional** — the
              test legitimately requires up to {cfg['slow_timeout']} minutes. Reducing the
              timeout would cause spurious failures.

            ## Authoritative Sources

            - This postmortem is the authoritative reference for what is a bug vs intentional.
            - The GitHub Actions documentation at https://docs.github.com/en/actions is the
              reference for correct syntax.
            - Do NOT modify the application source code — only `.github/workflows/ci.yml`.

            ## Deliverables

            - Fixed `.github/workflows/ci.yml`
            - All real bugs fixed; flaky-test patterns preserved unchanged
            """)

    def _make_readme(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # {cfg['workflow_name']} — Project README

            This is a {cfg['language']} project with a GitHub Actions CI/CD pipeline.

            ## Building

            ```bash
            {cfg['build_cmd']}
            ```

            ## Testing

            ```bash
            {cfg['test_cmd']}
            ```

            ## CI Pipeline

            The pipeline is defined in `.github/workflows/ci.yml`. It:

            1. Checks out the code
            2. Caches dependencies
            3. Builds the project
            4. Runs linting and unit tests
            5. Runs integration tests (known-flaky, `continue-on-error: true`)
            6. Uploads build artifacts from `{cfg['artifact_dir']}`
            7. Deploys on successful push to the main branch

            ## Notes

            - Integration tests may fail transiently due to external dependencies — this is expected.
            - E2e/performance tests have a long timeout — this is intentional.
            """)

    # ── Spec / Brief generators ────────────────────────────────────────────────

    def _make_spec(
        self, cfg: dict, bugs: list, wrong_image: str, branch_name: str
    ) -> str:
        has_wrong_runner = "wrong_runner_image" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_wrong_depth = "wrong_checkout_depth" in bugs

        bug_rows = []
        if has_wrong_runner:
            bug_rows.append(
                f"| B1 | wrong_runner_image | `runs-on: {wrong_image}` | `runs-on: ubuntu-latest` |"
            )
        if has_missing_env:
            bug_rows.append(
                f"| B2 | missing_env_var | No `env:` block in `{cfg['secret_step']}` step | "
                f"Add `env: {{ {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}} }}` |"
            )
        if has_wrong_artifact:
            bug_rows.append(
                f"| B3 | wrong_artifact_path | `path: {cfg['artifact_wrong']}` | `path: {cfg['artifact_dir']}` |"
            )
        if has_bad_cond:
            bug_rows.append(
                f"| B4 | bad_conditional | `if: always()` on deploy step | "
                f"`if: success() && github.ref == 'refs/heads/{branch_name}'` |"
            )
        if has_wrong_depth:
            bug_rows.append(
                "| B5 | wrong_checkout_depth | `fetch-depth: 1` | `fetch-depth: 0` |"
            )

        bug_table = "\n".join(bug_rows)

        return textwrap.dedent(f"""\
            # DEVOPS2_cicd_pipeline: CI/CD Pipeline Bug Fix — Full Specification (Planner Only)

            ## Overview

            The workspace contains a GitHub Actions workflow for a {cfg['language']} project
            (`.github/workflows/ci.yml`) with **{len(bugs)} real configuration bugs** and
            **2 intentional flaky-test patterns** that must be preserved.

            The executor only receives the brief; this spec provides the full analysis.

            ## File Structure

            - `.github/workflows/ci.yml` — the pipeline definition (the ONLY file to modify)
            - `postmortem.md` — incident analysis distinguishing real bugs vs flaky patterns
            - `README.md` — project overview

            ## Real Bugs (Must Be Fixed)

            | # | Type | Current (wrong) | Correct |
            |---|------|-----------------|---------|
            {bug_table}

            ### Bug Details

            """) + self._spec_bug_details(cfg, bugs, wrong_image, branch_name) + textwrap.dedent(f"""\

            ## Intentional Patterns (DO NOT CHANGE)

            ### F1 — `continue-on-error: true` on `{cfg['integration_step']}`

            This is **intentional** — the integration tests are known-flaky due to
            external service dependencies. The team has explicitly accepted this risk.
            Removing `continue-on-error` would cause valid CI runs to fail on transient
            network issues.

            ### F2 — `timeout-minutes: {cfg['slow_timeout']}` on `{cfg['slow_step']}`

            This timeout is **correct and intentional** — the test legitimately requires
            up to {cfg['slow_timeout']} minutes. Reducing it would cause spurious failures.

            ## Acceptance Criteria

            1. All {len(bugs)} real bugs are fixed in `.github/workflows/ci.yml`
            2. `continue-on-error: true` on `{cfg['integration_step']}` is preserved
            3. `timeout-minutes: {cfg['slow_timeout']}` on `{cfg['slow_step']}` is preserved
            4. YAML is syntactically valid (`yamllint` reports no errors)
            5. Only `.github/workflows/ci.yml` is modified

            ## Authoritative Sources

            - This spec is the authoritative analysis of bugs vs intentional patterns
            - `postmortem.md` in the workspace provides the same analysis (readable by agents)
            - GitHub Actions documentation is the reference for correct syntax
            """)

    def _spec_bug_details(
        self, cfg: dict, bugs: list, wrong_image: str, branch_name: str
    ) -> str:
        sections = []

        if "wrong_runner_image" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug B1 — EOL Runner Image

                **Location:** `runs-on:` in `build-and-test` job

                **Root cause:** `{wrong_image}` has reached end-of-life and is no longer
                maintained. GitHub may remove it at any time, and it lacks security patches.

                **Fix:** Change to `runs-on: ubuntu-latest`
                """))

        if "missing_env_var" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug B2 — Missing Environment Variable Injection

                **Location:** `{cfg['secret_step']}` step

                **Root cause:** The step runs `{cfg['secret_cmd']}` which requires
                `${cfg['secret_var']}` to be set, but the step has no `env:` block
                to inject the secret. The variable will be empty at runtime, causing
                authentication failure.

                **Fix:** Add an `env:` block to the step:
                ```yaml
                env:
                  {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}}
                ```
                """))

        if "wrong_artifact_path" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug B3 — Wrong Artifact Upload Path

                **Location:** `upload-artifact` step, `path:` field

                **Root cause:** The `path:` is set to `{cfg['artifact_wrong']}` but the
                build step (`{cfg['build_cmd']}`) writes output to `{cfg['artifact_dir']}`.
                The upload will fail or upload nothing because the wrong directory is referenced.

                **Fix:** Change `path: {cfg['artifact_wrong']}` to `path: {cfg['artifact_dir']}`
                """))

        if "bad_conditional" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug B4 — Incorrect Step Conditional

                **Location:** `{cfg['secret_step']}` step, `if:` condition

                **Root cause:** `if: always()` causes the deploy step to run regardless
                of whether previous steps passed or failed. This means a broken build
                could be deployed to production.

                **Fix:** Change to:
                ```yaml
                if: success() && github.ref == 'refs/heads/{branch_name}'
                ```
                This ensures deployment only happens on successful runs on the main branch.
                """))

        if "wrong_checkout_depth" in bugs:
            sections.append(textwrap.dedent(f"""\
                ### Bug B5 — Shallow Clone Breaks Versioning

                **Location:** `Checkout code` step, `fetch-depth:` option

                **Root cause:** `fetch-depth: 1` creates a shallow clone without tags.
                The build uses `{cfg['version_cmd']}` which relies on git tags to
                determine the version. With a shallow clone, this command fails or
                returns a fallback like `0.0.0-unknown`.

                **Fix:** Change `fetch-depth: 1` to `fetch-depth: 0` to fetch full
                history and all tags.
                """))

        return "\n".join(sections)

    def _make_brief(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # DEVOPS2_cicd_pipeline (Brief)

            The GitHub Actions CI/CD pipeline for this {cfg['language']} project is broken.
            Fix the pipeline configuration so it runs correctly.

            **File to fix:** `.github/workflows/ci.yml`
            **Reference:** `postmortem.md` contains incident analysis that may help.

            **Do NOT modify:** `README.md` or any application source files.

            Follow the Planner's guidance precisely.
            """)
