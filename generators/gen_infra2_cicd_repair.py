"""
Parameterized generator for INFRA2_cicd_repair.

GitHub Actions workflow with 4-5 real bugs that must be fixed, plus 2
flaky-test patterns that must be PRESERVED (continue-on-error for a known
flaky test, long timeout for a slow integration test).

Information asymmetry (TNI pattern B):
  spec.md   — postmortem distinguishing real bugs vs flaky-test false alarms,
               plus exact fixes for each real bug
  brief.md  — "fix the broken CI pipeline" (no specifics)

Each seed produces a different domain (python-api / node-app / go-service /
rust-cli / java-spring) with:

  Real bugs (4-5 depending on bug_set):
    B1. wrong_docker_tag:      uses :latest instead of a pinned tag for a
                               build/push step (non-deterministic builds)
    B2. missing_env_var:       step references $SECRET but env: block absent
    B3. wrong_artifact_path:   upload-artifact path doesn't match build output
    B4. bad_conditional:       deploy step uses always() instead of success()
    B5. shallow_clone:         fetch-depth: 1 breaks git describe versioning

  Flaky-test false alarms (MUST be preserved):
    F1. continue-on-error: true on integration test (known-flaky external dep)
    F2. timeout-minutes: N    on slow test (legitimately long-running)
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
        "workflow_name": "Python API CI",
        "build_cmd": "pip install -e . && python -m build",
        "test_cmd": "pytest tests/unit/ -v",
        "lint_cmd": "ruff check src/",
        "artifact_dir": "dist/",
        "artifact_wrong": "build/",
        "docker_image": "python",
        "correct_tag": "3.11-slim",
        "wrong_tag": "latest",
        "secret_var": "DATABASE_URL",
        "secret_step": "Run database migrations",
        "secret_cmd": "python manage.py migrate --noinput",
        "version_cmd": "git describe --tags --always",
        "integration_test": "pytest tests/integration/ -v --timeout=90",
        "integration_step": "Run integration tests",
        "slow_test": "pytest tests/e2e/ -v --slow",
        "slow_step": "Run e2e tests",
        "slow_timeout": 30,
        "cache_path": "~/.cache/pip",
        "cache_key": "pip-${{ hashFiles('requirements.txt') }}",
    },
    {
        "name": "node-app",
        "language": "Node.js",
        "workflow_name": "Node App CI",
        "build_cmd": "npm ci && npm run build",
        "test_cmd": "npm run test:unit",
        "lint_cmd": "npm run lint",
        "artifact_dir": "dist/",
        "artifact_wrong": ".next/static/",
        "docker_image": "node",
        "correct_tag": "20-alpine",
        "wrong_tag": "latest",
        "secret_var": "STRIPE_SECRET_KEY",
        "secret_step": "Deploy to staging",
        "secret_cmd": "node scripts/deploy.js --env staging",
        "version_cmd": "git describe --tags --always",
        "integration_test": "npm run test:integration",
        "integration_step": "Run integration tests",
        "slow_test": "npm run test:e2e",
        "slow_step": "Run browser tests",
        "slow_timeout": 45,
        "cache_path": "~/.npm",
        "cache_key": "node-${{ hashFiles('package-lock.json') }}",
    },
    {
        "name": "go-service",
        "language": "Go",
        "workflow_name": "Go Service CI",
        "build_cmd": "go build -o bin/server ./cmd/server",
        "test_cmd": "go test ./... -v -short",
        "lint_cmd": "golangci-lint run ./...",
        "artifact_dir": "bin/",
        "artifact_wrong": "build/bin/",
        "docker_image": "golang",
        "correct_tag": "1.22-alpine",
        "wrong_tag": "latest",
        "secret_var": "GCR_TOKEN",
        "secret_step": "Push container image",
        "secret_cmd": "docker push gcr.io/myproject/server:$VERSION",
        "version_cmd": "git describe --tags --always",
        "integration_test": "go test ./integration/... -v -timeout 3m",
        "integration_step": "Run integration tests",
        "slow_test": "go test ./bench/... -bench=. -benchtime=60s",
        "slow_step": "Run benchmarks",
        "slow_timeout": 60,
        "cache_path": "~/go/pkg/mod",
        "cache_key": "go-${{ hashFiles('go.sum') }}",
    },
    {
        "name": "rust-cli",
        "language": "Rust",
        "workflow_name": "Rust CLI CI",
        "build_cmd": "cargo build --release",
        "test_cmd": "cargo test --lib",
        "lint_cmd": "cargo clippy -- -D warnings",
        "artifact_dir": "target/release/",
        "artifact_wrong": "target/debug/",
        "docker_image": "rust",
        "correct_tag": "1.77-slim",
        "wrong_tag": "latest",
        "secret_var": "CRATES_IO_TOKEN",
        "secret_step": "Publish crate",
        "secret_cmd": "cargo publish --token $CRATES_IO_TOKEN",
        "version_cmd": "git describe --tags --always",
        "integration_test": "cargo test --test integration -- --nocapture",
        "integration_step": "Run integration tests",
        "slow_test": "cargo test --test stress -- --nocapture",
        "slow_step": "Run stress tests",
        "slow_timeout": 45,
        "cache_path": "~/.cargo/registry",
        "cache_key": "cargo-${{ hashFiles('Cargo.lock') }}",
    },
    {
        "name": "java-spring",
        "language": "Java",
        "workflow_name": "Java Spring CI",
        "build_cmd": "./gradlew build -x test",
        "test_cmd": "./gradlew test",
        "lint_cmd": "./gradlew checkstyleMain",
        "artifact_dir": "build/libs/",
        "artifact_wrong": "build/classes/",
        "docker_image": "eclipse-temurin",
        "correct_tag": "21-jre-alpine",
        "wrong_tag": "latest",
        "secret_var": "NEXUS_PASSWORD",
        "secret_step": "Publish artifact",
        "secret_cmd": "./gradlew publish",
        "version_cmd": "git describe --tags --always",
        "integration_test": "./gradlew integrationTest",
        "integration_step": "Run integration tests",
        "slow_test": "./gradlew performanceTest",
        "slow_step": "Run performance tests",
        "slow_timeout": 60,
        "cache_path": "~/.gradle/caches",
        "cache_key": "gradle-${{ hashFiles('build.gradle') }}",
    },
]

# Bug sets — always includes at least 4 real bugs, seed 0 includes all 5
BUG_SETS = [
    ["wrong_docker_tag", "missing_env_var", "wrong_artifact_path", "bad_conditional", "shallow_clone"],
    ["wrong_docker_tag", "missing_env_var", "wrong_artifact_path", "bad_conditional"],
    ["wrong_docker_tag", "missing_env_var", "wrong_artifact_path", "shallow_clone"],
    ["wrong_docker_tag", "missing_env_var", "bad_conditional", "shallow_clone"],
    ["wrong_docker_tag", "wrong_artifact_path", "bad_conditional", "shallow_clone"],
]


class Generator(TaskGenerator):
    task_id = "INFRA2_cicd_repair"
    domain = "Pipeline/Integration"
    difficulty = "hard"
    languages = ["yaml"]

    @staticmethod
    def _clean(s: str) -> str:
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        bug_set_idx = seed % len(BUG_SETS)
        cfg = DOMAINS[domain_idx]
        bugs = BUG_SETS[bug_set_idx]

        branch_name = rng.choice(["main", "master", "release", "production"])

        workspace_files = self._make_workspace(cfg, bugs, branch_name)
        spec_md = self._clean(self._make_spec(cfg, bugs, branch_name))
        brief_md = self._clean(self._make_brief(cfg))

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "language": cfg["language"],
                "bugs": bugs,
                "false_alarms": ["continue_on_error_flaky", "slow_test_timeout"],
                "correct_docker_tag": cfg["correct_tag"],
                "wrong_docker_tag": cfg["wrong_tag"],
                "correct_artifact_dir": cfg["artifact_dir"],
                "wrong_artifact_dir": cfg["artifact_wrong"],
                "branch_name": branch_name,
                "secret_var": cfg["secret_var"],
                "slow_timeout": cfg["slow_timeout"],
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "Pipeline/Integration"},
        )

    # ── Workspace ──────────────────────────────────────────────────────────────

    def _make_workspace(self, cfg: dict, bugs: list, branch_name: str) -> dict:
        files = {}
        files[".github/workflows/ci.yml"] = self._make_workflow(cfg, bugs, branch_name)
        files["postmortem.md"] = self._clean(self._make_postmortem(cfg, bugs, branch_name))
        files["README.md"] = self._clean(self._make_readme(cfg))
        return files

    def _make_workflow(self, cfg: dict, bugs: list, branch_name: str) -> str:
        has_wrong_docker = "wrong_docker_tag" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_shallow = "shallow_clone" in bugs

        docker_tag = cfg["wrong_tag"] if has_wrong_docker else cfg["correct_tag"]
        artifact_path = cfg["artifact_wrong"] if has_wrong_artifact else cfg["artifact_dir"]
        fetch_depth = "1" if has_shallow else "0"

        if has_bad_cond:
            deploy_if = "always()"
            deploy_comment = (
                "# BUG B4: always() runs even when tests fail; "
                f"should be: success() && github.ref == 'refs/heads/{branch_name}'"
            )
        else:
            deploy_if = f"success() && github.ref == 'refs/heads/{branch_name}'"
            deploy_comment = "# Correct: only deploy on success from the target branch"

        if has_missing_env:
            env_block = (
                f"      # BUG B2: env block missing — ${cfg['secret_var']} "
                "will be empty at runtime"
            )
            env_lines = ""
        else:
            env_block = "      env:"
            env_lines = f"\n        {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}}"

        docker_comment = (
            f"      # BUG B1: :{cfg['wrong_tag']} is non-deterministic; "
            f"pin to :{cfg['correct_tag']}"
            if has_wrong_docker
            else f"      # Correct: pinned to :{cfg['correct_tag']}"
        )

        workflow = textwrap.dedent(f"""\
            name: {cfg['workflow_name']}

            on:
              push:
                branches: ["{branch_name}", "develop"]
              pull_request:
                branches: ["{branch_name}"]

            jobs:
              build-and-test:
                runs-on: ubuntu-latest

                steps:
                  - name: Checkout code
                    uses: actions/checkout@v4
                    with:
                      # BUG B5: fetch-depth: 1 (shallow clone) breaks git describe versioning
                      # Fix: fetch-depth: 0 to include all tags and full history
                      fetch-depth: {fetch_depth}

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

                  - name: Build Docker image
            {docker_comment}
                    run: |
                      docker build -t myapp:{docker_tag} .

                  - name: Upload build artifacts
                    uses: actions/upload-artifact@v3
                    with:
                      name: build-output
                      # BUG B3: wrong path — build writes to {cfg['artifact_dir']} not {cfg['artifact_wrong']}
                      path: {artifact_path}

                  - name: {cfg['secret_step']}
                    {deploy_comment}
                    if: {deploy_if}
            {env_block}{env_lines}
                    run: {cfg['secret_cmd']}
            """)
        return workflow

    def _make_postmortem(self, cfg: dict, bugs: list, branch_name: str) -> str:
        has_wrong_docker = "wrong_docker_tag" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_shallow = "shallow_clone" in bugs

        real_bugs = []
        if has_wrong_docker:
            real_bugs.append(
                f"- **B1 (wrong_docker_tag)**: `Build Docker image` step uses "
                f"`{cfg['docker_image']}:{cfg['wrong_tag']}` (non-deterministic). "
                f"Fix: change to `{cfg['docker_image']}:{cfg['correct_tag']}`."
            )
        if has_missing_env:
            real_bugs.append(
                f"- **B2 (missing_env_var)**: `{cfg['secret_step']}` step references "
                f"`${cfg['secret_var']}` but no `env:` block injects the secret. "
                f"Fix: add `env: {{ {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}} }}`."
            )
        if has_wrong_artifact:
            real_bugs.append(
                f"- **B3 (wrong_artifact_path)**: `upload-artifact` path is "
                f"`{cfg['artifact_wrong']}` but the build writes to `{cfg['artifact_dir']}`. "
                f"Fix: change `path:` to `{cfg['artifact_dir']}`."
            )
        if has_bad_cond:
            real_bugs.append(
                f"- **B4 (bad_conditional)**: `{cfg['secret_step']}` step has `if: always()` "
                f"— runs even when tests fail, risking broken deployments. "
                f"Fix: `if: success() && github.ref == 'refs/heads/{branch_name}'`."
            )
        if has_shallow:
            real_bugs.append(
                f"- **B5 (shallow_clone)**: `fetch-depth: 1` creates a shallow clone. "
                f"`{cfg['version_cmd']}` fails without tags. "
                f"Fix: `fetch-depth: 0` (full history + all tags)."
            )

        real_section = "\n".join(real_bugs) if real_bugs else "_(none)_"

        return textwrap.dedent(f"""\
            # CI/CD Pipeline Postmortem — {cfg['workflow_name']}

            ## Incident Summary

            Several failures were observed in the CI pipeline for this {cfg['language']} project.
            This postmortem distinguishes genuine configuration bugs from known-acceptable
            test behaviours that should NOT be changed.

            ## Real Bugs (Must Be Fixed)

            {real_section}

            ## Known-Flaky Tests (Do NOT Change)

            - **F1 (continue_on_error_flaky)**: The `{cfg['integration_step']}` step has
              `continue-on-error: true`. This is **intentional** — this test occasionally
              fails due to unreliable external service dependencies. The team has accepted
              this flakiness. Removing `continue-on-error` would cause valid CI runs to
              fail on transient network issues.

            - **F2 (slow_test_timeout)**: The `{cfg['slow_step']}` step has
              `timeout-minutes: {cfg['slow_timeout']}`. This is **intentional** — the
              test legitimately requires up to {cfg['slow_timeout']} minutes. Reducing the
              timeout would cause spurious failures on slower runners.

            ## Authoritative Sources

            - This postmortem is the authoritative reference for what is a bug vs intentional.
            - GitHub Actions documentation is the reference for correct syntax.
            - Do NOT modify application source code — only `.github/workflows/ci.yml`.

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

            1. Checks out the code (full history for versioning)
            2. Caches dependencies
            3. Builds the project
            4. Runs linting and unit tests
            5. Runs integration tests (known-flaky, `continue-on-error: true`)
            6. Runs slow tests with an extended timeout
            7. Builds the Docker image with a pinned tag
            8. Uploads build artifacts from `{cfg['artifact_dir']}`
            9. Runs deployment step on successful push to the main branch

            ## Notes

            - Integration tests may fail transiently due to external dependencies — this is expected.
            - Slow/performance tests have a long timeout — this is intentional.
            - Docker image must use a pinned tag for reproducible builds.
            """)

    # ── Spec / Brief ──────────────────────────────────────────────────────────

    def _make_spec(self, cfg: dict, bugs: list, branch_name: str) -> str:
        has_wrong_docker = "wrong_docker_tag" in bugs
        has_missing_env = "missing_env_var" in bugs
        has_wrong_artifact = "wrong_artifact_path" in bugs
        has_bad_cond = "bad_conditional" in bugs
        has_shallow = "shallow_clone" in bugs

        bug_rows = []
        if has_wrong_docker:
            bug_rows.append(
                f"| B1 | wrong_docker_tag | `{cfg['docker_image']}:{cfg['wrong_tag']}` "
                f"| `{cfg['docker_image']}:{cfg['correct_tag']}` |"
            )
        if has_missing_env:
            bug_rows.append(
                f"| B2 | missing_env_var | No `env:` in `{cfg['secret_step']}` "
                f"| Add `env: {{ {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}} }}` |"
            )
        if has_wrong_artifact:
            bug_rows.append(
                f"| B3 | wrong_artifact_path | `path: {cfg['artifact_wrong']}` "
                f"| `path: {cfg['artifact_dir']}` |"
            )
        if has_bad_cond:
            bug_rows.append(
                f"| B4 | bad_conditional | `if: always()` "
                f"| `if: success() && github.ref == 'refs/heads/{branch_name}'` |"
            )
        if has_shallow:
            bug_rows.append(
                "| B5 | shallow_clone | `fetch-depth: 1` | `fetch-depth: 0` |"
            )

        bug_table = "\n".join(bug_rows)

        details = self._spec_bug_details(cfg, bugs, branch_name)

        return textwrap.dedent(f"""\
            # INFRA2_cicd_repair: CI/CD Pipeline Repair — Full Specification (Planner Only)

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

            {details}

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
            4. YAML is syntactically valid
            5. Only `.github/workflows/ci.yml` is modified

            ## Authoritative Sources

            - This spec is the authoritative analysis of bugs vs intentional patterns
            - `postmortem.md` in the workspace provides the same analysis (readable by agents)
            - GitHub Actions documentation is the reference for correct syntax
            """)

    def _spec_bug_details(self, cfg: dict, bugs: list, branch_name: str) -> str:
        sections = []

        if "wrong_docker_tag" in bugs:
            sections.append(textwrap.dedent(f"""\
                #### Bug B1 — Non-Deterministic Docker Tag

                **Location:** `Build Docker image` step, `run:` block

                **Root cause:** `{cfg['docker_image']}:{cfg['wrong_tag']}` resolves to
                whatever the latest image is at build time. This produces non-reproducible
                builds and can silently pull breaking changes.

                **Fix:** Pin the tag to `{cfg['docker_image']}:{cfg['correct_tag']}`.
                """))

        if "missing_env_var" in bugs:
            sections.append(textwrap.dedent(f"""\
                #### Bug B2 — Missing Environment Variable Injection

                **Location:** `{cfg['secret_step']}` step

                **Root cause:** The step runs `{cfg['secret_cmd']}` which requires
                `${cfg['secret_var']}` to be set, but the step has no `env:` block.
                The variable will be empty at runtime, causing authentication failure.

                **Fix:** Add an `env:` block to the step:
                ```yaml
                env:
                  {cfg['secret_var']}: ${{{{ secrets.{cfg['secret_var']} }}}}
                ```
                """))

        if "wrong_artifact_path" in bugs:
            sections.append(textwrap.dedent(f"""\
                #### Bug B3 — Wrong Artifact Upload Path

                **Location:** `Upload build artifacts` step, `path:` field

                **Root cause:** The `path:` is set to `{cfg['artifact_wrong']}` but the
                build step (`{cfg['build_cmd']}`) writes output to `{cfg['artifact_dir']}`.
                The upload will fail or upload nothing.

                **Fix:** Change `path: {cfg['artifact_wrong']}` to `path: {cfg['artifact_dir']}`
                """))

        if "bad_conditional" in bugs:
            sections.append(textwrap.dedent(f"""\
                #### Bug B4 — Incorrect Step Conditional

                **Location:** `{cfg['secret_step']}` step, `if:` condition

                **Root cause:** `if: always()` causes the deploy step to run regardless
                of whether previous steps passed or failed. A broken build could be deployed.

                **Fix:** Change to:
                ```yaml
                if: success() && github.ref == 'refs/heads/{branch_name}'
                ```
                """))

        if "shallow_clone" in bugs:
            sections.append(textwrap.dedent(f"""\
                #### Bug B5 — Shallow Clone Breaks Versioning

                **Location:** `Checkout code` step, `fetch-depth:` option

                **Root cause:** `fetch-depth: 1` creates a shallow clone without tags.
                The build uses `{cfg['version_cmd']}` which requires git tags.
                With a shallow clone this command fails or returns `0.0.0-unknown`.

                **Fix:** Change `fetch-depth: 1` to `fetch-depth: 0`.
                """))

        return "\n".join(sections)

    def _make_brief(self, cfg: dict) -> str:
        return textwrap.dedent(f"""\
            # INFRA2_cicd_repair (Brief)

            The GitHub Actions CI/CD pipeline for this {cfg['language']} project is broken.
            Fix the pipeline configuration so it runs correctly.

            **File to fix:** `.github/workflows/ci.yml`
            **Reference:** `postmortem.md` contains incident analysis that may help.

            **Do NOT modify:** `README.md` or any application source files.

            Follow the Planner's guidance precisely.
            """)
