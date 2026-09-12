"""
Parameterized generator for DEVOPS1: Dockerfile Multi-Stage Build Fix.

Information asymmetry (TNI pattern B):
  - spec.md describes the intended build architecture: which stages exist, what
    each stage does, the correct base images, correct port, correct WORKDIR, and
    lists exactly which lines contain bugs.
  - brief.md only says "the Docker build or container startup is broken — fix it."

Each seed produces:
  - Different app framework (flask / fastapi / aiohttp)
  - Different stage names (e.g. "builder"/"runtime" vs "build"/"prod")
  - Different port number
  - Different WORKDIR path
  - All 5 bugs from the pool are always injected:
      1. wrong_base_image       – builder uses python:3.11-alpine instead of slim
      2. wrong_copy_stage       – COPY --from= references a non-existent stage name
      3. missing_expose         – EXPOSE uses the wrong port number
      4. requirements_wrong_stage – pip install is only in the runtime stage, not builder
      5. workdir_mismatch       – runtime WORKDIR differs from builder WORKDIR so
                                   copied paths resolve incorrectly

Grade checks (static, no Docker daemon required):
  C1  Dockerfile exists
  C2  Builder stage uses correct base image (python:3.11-slim)
  C3  Runtime stage uses correct base image (python:3.11-slim)
  C4  requirements.txt installed in builder stage (RUN pip install)
  C5  COPY --from references the correct builder stage name
  C6  EXPOSE uses the correct port
  C7  WORKDIR is consistent between builder and runtime stages
  C8  app.py is present in workspace
  C9  requirements.txt is present in workspace
  C10 docker-compose.yml maps the correct host port
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Parameterisation pools ─────────────────────────────────────────────────────

APP_FRAMEWORKS = ["flask", "fastapi", "aiohttp"]

# (builder_stage_name, runtime_stage_name)
STAGE_NAME_PAIRS = [
    ("builder", "runtime"),
    ("build", "prod"),
    ("deps", "app"),
    ("compile", "final"),
    ("installer", "server"),
]

PORT_CHOICES = [8000, 8080, 8081, 8088, 8090, 5000, 5001, 9000]

WORKDIR_CHOICES = ["/app", "/srv/app", "/opt/app", "/code", "/service"]

PYTHON_VERSION = "3.11"

BUG_POOL = [
    "wrong_base_image",
    "wrong_copy_stage",
    "missing_expose",
    "requirements_wrong_stage",
    "workdir_mismatch",
]


class Generator(TaskGenerator):
    task_id = "DEVOPS1_dockerfile_fix"
    domain = "ops"
    difficulty = "medium"
    languages = ["dockerfile", "python", "bash"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        framework = rng.choice(APP_FRAMEWORKS)
        builder_stage, runtime_stage = rng.choice(STAGE_NAME_PAIRS)
        port = rng.choice(PORT_CHOICES)
        workdir = rng.choice(WORKDIR_CHOICES)

        # Wrong WORKDIR for the runtime stage (workdir_mismatch bug)
        wrong_workdir_opts = [w for w in WORKDIR_CHOICES if w != workdir]
        wrong_workdir = rng.choice(wrong_workdir_opts)

        # Wrong stage name for COPY --from bug (must differ from real builder stage)
        wrong_stage_opts = [s for s, _ in STAGE_NAME_PAIRS if s != builder_stage]
        wrong_copy_stage = rng.choice(wrong_stage_opts)

        # Wrong port for EXPOSE bug (must differ from real port)
        wrong_port_opts = [p for p in PORT_CHOICES if p != port]
        wrong_expose_port = rng.choice(wrong_port_opts)

        expected = {
            "framework": framework,
            "builder_stage": builder_stage,
            "runtime_stage": runtime_stage,
            "port": port,
            "workdir": workdir,
            "python_version": PYTHON_VERSION,
            "correct_base_image": f"python:{PYTHON_VERSION}-slim",
            "bugs": BUG_POOL,
            "checks_total": 10,
        }

        dockerfile = self._make_buggy_dockerfile(
            framework=framework,
            builder_stage=builder_stage,
            runtime_stage=runtime_stage,
            port=port,
            workdir=workdir,
            wrong_workdir=wrong_workdir,
            wrong_copy_stage=wrong_copy_stage,
            wrong_expose_port=wrong_expose_port,
        )

        app_py = self._make_app_py(framework, port)
        requirements_txt = self._make_requirements(framework)
        docker_compose = self._make_docker_compose(port)
        test_build_sh = self._make_test_build_sh(port)

        workspace_files = {
            "Dockerfile": dockerfile,
            "app.py": app_py,
            "requirements.txt": requirements_txt,
            "docker-compose.yml": docker_compose,
            "test_build.sh": test_build_sh,
        }

        spec_md = self._make_spec(
            framework=framework,
            builder_stage=builder_stage,
            runtime_stage=runtime_stage,
            port=port,
            workdir=workdir,
            wrong_workdir=wrong_workdir,
            wrong_copy_stage=wrong_copy_stage,
            wrong_expose_port=wrong_expose_port,
        )
        brief_md = self._make_brief(framework, port)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
            metadata={"difficulty": "medium", "category": "Operations"},
        )

    # ── Dockerfile ─────────────────────────────────────────────────────────────

    def _make_buggy_dockerfile(
        self,
        framework: str,
        builder_stage: str,
        runtime_stage: str,
        port: int,
        workdir: str,
        wrong_workdir: str,
        wrong_copy_stage: str,
        wrong_expose_port: int,
    ) -> str:
        correct_image = f"python:{PYTHON_VERSION}-slim"
        # BUG 1: builder uses alpine instead of slim
        wrong_builder_image = f"python:{PYTHON_VERSION}-alpine"

        lines = [
            "# syntax=docker/dockerfile:1",
            "",
            f"# ── Stage 1: {builder_stage} ──────────────────────────────",
            # BUG 1: wrong base image
            f"FROM {wrong_builder_image} AS {builder_stage}",
            "",
            f"WORKDIR {workdir}",
            "",
            "COPY requirements.txt .",
            "",
            # BUG 4: pip install intentionally absent from builder stage
            "# NOTE: dependencies will be installed in the runtime stage",
            "",
            "COPY app.py .",
            "",
            f"# ── Stage 2: {runtime_stage} ─────────────────────────────",
            f"FROM {correct_image} AS {runtime_stage}",
            "",
            # BUG 5: runtime uses a different WORKDIR
            f"WORKDIR {wrong_workdir}",
            "",
            # BUG 4: pip install lives here instead of the builder stage
            "COPY requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "",
            # BUG 2: --from references wrong stage name
            f"COPY --from={wrong_copy_stage} {workdir}/app.py .",
            "",
            # BUG 3: wrong port in EXPOSE
            f"EXPOSE {wrong_expose_port}",
            "",
            "ENV PYTHONUNBUFFERED=1",
            "",
            'CMD ["python", "app.py"]',
        ]
        return "\n".join(lines) + "\n"

    # ── app.py ─────────────────────────────────────────────────────────────────

    def _make_app_py(self, framework: str, port: int) -> str:
        if framework == "flask":
            return textwrap.dedent(f"""\
                import os
                from flask import Flask, jsonify

                app = Flask(__name__)


                @app.route("/health")
                def health():
                    return jsonify({{"status": "ok"}})


                @app.route("/")
                def index():
                    return jsonify({{"service": "devops1", "framework": "flask"}})


                if __name__ == "__main__":
                    port = int(os.environ.get("PORT", {port}))
                    app.run(host="0.0.0.0", port=port)
                """)
        elif framework == "fastapi":
            return textwrap.dedent(f"""\
                import os
                import uvicorn
                from fastapi import FastAPI

                app = FastAPI()


                @app.get("/health")
                def health():
                    return {{"status": "ok"}}


                @app.get("/")
                def index():
                    return {{"service": "devops1", "framework": "fastapi"}}


                if __name__ == "__main__":
                    port = int(os.environ.get("PORT", {port}))
                    uvicorn.run(app, host="0.0.0.0", port=port)
                """)
        else:  # aiohttp
            return textwrap.dedent(f"""\
                import os
                from aiohttp import web


                async def health(request):
                    return web.json_response({{"status": "ok"}})


                async def index(request):
                    return web.json_response({{"service": "devops1", "framework": "aiohttp"}})


                def make_app():
                    application = web.Application()
                    application.router.add_get("/health", health)
                    application.router.add_get("/", index)
                    return application


                if __name__ == "__main__":
                    port = int(os.environ.get("PORT", {port}))
                    web.run_app(make_app(), host="0.0.0.0", port=port)
                """)

    # ── requirements.txt ───────────────────────────────────────────────────────

    def _make_requirements(self, framework: str) -> str:
        if framework == "flask":
            return "flask>=3.0.0\n"
        elif framework == "fastapi":
            return "fastapi>=0.110.0\nuvicorn>=0.29.0\n"
        else:  # aiohttp
            return "aiohttp>=3.9.0\n"

    # ── docker-compose.yml ─────────────────────────────────────────────────────

    def _make_docker_compose(self, port: int) -> str:
        return textwrap.dedent(f"""\
            version: "3.9"
            services:
              app:
                build: .
                ports:
                  - "{port}:{port}"
                environment:
                  - PORT={port}
                healthcheck:
                  test: ["CMD", "python", "-c",
                    "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')"]
                  interval: 10s
                  timeout: 5s
                  retries: 3
                  start_period: 5s
            """)

    # ── test_build.sh ──────────────────────────────────────────────────────────

    def _make_test_build_sh(self, port: int) -> str:
        return textwrap.dedent(f"""\
            #!/usr/bin/env bash
            # test_build.sh — verify the Docker image builds and the container starts
            set -euo pipefail

            IMAGE_NAME="devops1-test-$$"

            cleanup() {{
                docker rm -f "$IMAGE_NAME" 2>/dev/null || true
                docker rmi "$IMAGE_NAME" 2>/dev/null || true
            }}
            trap cleanup EXIT

            echo "[1/4] Building Docker image..."
            docker build -t "$IMAGE_NAME" .

            echo "[2/4] Starting container..."
            docker run -d --name "$IMAGE_NAME" -p {port}:{port} "$IMAGE_NAME"

            echo "[3/4] Waiting for health endpoint..."
            for i in $(seq 1 20); do
                BODY=$(curl -sf "http://localhost:{port}/health" 2>/dev/null || true)
                if echo "$BODY" | python3 -c \\
                    "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" \\
                    2>/dev/null; then
                    echo "  Health check passed."
                    break
                fi
                sleep 1
                if [ "$i" -eq 20 ]; then
                    echo "  ERROR: health check timed out."
                    docker logs "$IMAGE_NAME"
                    exit 1
                fi
            done

            echo "[4/4] Verifying /health returns {{\"status\": \"ok\"}}..."
            BODY=$(curl -sf "http://localhost:{port}/health")
            echo "$BODY" | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('status') == 'ok', 'unexpected body: ' + repr(body)
print('PASS: /health returned {{\"status\": \"ok\"}}')
"

            echo ""
            echo "All checks passed."
            """)

    # ── spec.md ────────────────────────────────────────────────────────────────

    def _make_spec(
        self,
        framework: str,
        builder_stage: str,
        runtime_stage: str,
        port: int,
        workdir: str,
        wrong_workdir: str,
        wrong_copy_stage: str,
        wrong_expose_port: int,
    ) -> str:
        correct_image = f"python:{PYTHON_VERSION}-slim"
        wrong_builder_image = f"python:{PYTHON_VERSION}-alpine"

        return textwrap.dedent(f"""\
            # DEVOPS1_dockerfile_fix: Multi-Stage Dockerfile Repair

            ## Goal

            Fix the `Dockerfile` in the workspace so that `docker build .` succeeds
            and a running container responds on port {port} with a healthy `{framework}`
            web application.

            ## Intended Build Architecture

            The Dockerfile must use a **two-stage build**:

            | Stage name | Purpose | Correct base image |
            |------------|---------|-------------------|
            | `{builder_stage}` | Install Python dependencies | `{correct_image}` |
            | `{runtime_stage}` | Run the application | `{correct_image}` |

            ### Stage 1 — `{builder_stage}` (dependency installer)

            ```dockerfile
            FROM {correct_image} AS {builder_stage}
            WORKDIR {workdir}
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt
            COPY app.py .
            ```

            ### Stage 2 — `{runtime_stage}` (application runner)

            ```dockerfile
            FROM {correct_image} AS {runtime_stage}
            WORKDIR {workdir}
            COPY --from={builder_stage} {workdir}/app.py .
            EXPOSE {port}
            ENV PYTHONUNBUFFERED=1
            CMD ["python", "app.py"]
            ```

            ## Known Bugs in Current Dockerfile

            The Dockerfile has **5 intentional bugs**. Fix all of them:

            | # | Bug type | Current (wrong) | Correct |
            |---|----------|-----------------|---------|
            | 1 | Wrong builder base image | `FROM {wrong_builder_image} AS {builder_stage}` | `FROM {correct_image} AS {builder_stage}` |
            | 2 | `pip install` in wrong stage | `RUN pip install` only in `{runtime_stage}` | Must be in `{builder_stage}` |
            | 3 | `COPY --from` wrong stage name | `COPY --from={wrong_copy_stage}` | `COPY --from={builder_stage}` |
            | 4 | Wrong port in EXPOSE | `EXPOSE {wrong_expose_port}` | `EXPOSE {port}` |
            | 5 | WORKDIR mismatch in runtime | `WORKDIR {wrong_workdir}` in `{runtime_stage}` | `WORKDIR {workdir}` (must match builder) |

            ## Requirements

            1. `docker build .` must complete without errors.
            2. The container must respond to `GET /health` with HTTP 200 and body
               `{{"status": "ok"}}`.
            3. The container must listen on port `{port}`.
            4. All dependency installation must happen in the `{builder_stage}` stage
               only (not duplicated in `{runtime_stage}`).
            5. Do **not** modify `app.py` or `requirements.txt`.
            6. Run `bash test_build.sh` to verify before submitting.

            ## Authoritative Sources

            - This spec is the authoritative reference for the correct architecture.
            - `app.py` and `requirements.txt` are correct — do not modify them.
            - `docker-compose.yml` shows the correct port mapping and can be used for
              local testing with `docker compose up`.

            ## Deliverables

            - Fixed `Dockerfile` committed to the workspace.
            - Verifier must create `/shared/submission/attestation.json` with
              `verdict="pass"`.
            """)

    # ── brief.md ───────────────────────────────────────────────────────────────

    def _make_brief(self, framework: str, port: int) -> str:
        return textwrap.dedent(f"""\
            # DEVOPS1_dockerfile_fix (Brief)

            The Docker build for this {framework} application is broken. Fix the
            `Dockerfile` so that `docker build .` succeeds and the running container
            starts correctly on port {port}.

            Run `bash test_build.sh` to verify the fix.

            Follow the Planner's guidance precisely.
            """)
