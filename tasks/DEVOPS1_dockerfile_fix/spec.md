# DEVOPS1_dockerfile_fix: Multi-Stage Dockerfile Repair

## Goal

Fix the `Dockerfile` in the workspace so that `docker build .` succeeds and a
running container serves a healthy web application (GET /health → 200 OK).

This spec is generated per-seed. The exact stage names, port, WORKDIR, framework,
and bug values are embedded in the seed-specific version written to `spec.md` at
run time. Refer to the spec that appears in your workspace.

## Intended Build Architecture

The Dockerfile uses a **two-stage build**:

- **Stage 1 (builder/installer)**: Install Python dependencies from `requirements.txt`
  using `pip install --no-cache-dir`. Copy `app.py` into the stage.
- **Stage 2 (runtime)**: Copy only `app.py` from Stage 1 using `COPY --from=<stage1>`.
  Expose the correct application port. Set `ENV PYTHONUNBUFFERED=1`.
  Run `CMD ["python", "app.py"]`.

Both stages must use `python:3.11-slim` as the base image.

## Known Bug Categories

The Dockerfile contains **5 intentional bugs**:

1. **Wrong builder base image** — builder uses `python:3.11-alpine` instead of `python:3.11-slim`
2. **pip install in wrong stage** — `RUN pip install` appears in the runtime stage only, not the builder
3. **COPY --from wrong stage** — references a non-existent stage name
4. **Wrong EXPOSE port** — port number does not match what the app binds on
5. **WORKDIR mismatch** — runtime stage uses a different WORKDIR than the builder stage

## Requirements

1. `docker build .` must complete without errors.
2. The container must respond to `GET /health` with HTTP 200 and body `{"status": "ok"}`.
3. The container must listen on the correct port (see seed-specific spec).
4. All `pip install` must happen in the builder stage only.
5. Do **not** modify `app.py` or `requirements.txt`.
6. Run `bash test_build.sh` to verify before submitting.

## Authoritative Sources

- The seed-specific `spec.md` (this file, rewritten at generation time) is the
  authoritative reference for exact stage names, port, and WORKDIR values.
- `app.py` and `requirements.txt` are correct — do not modify them.
- `docker-compose.yml` shows the correct port mapping.

## Contradiction / Hidden Complexity

A naive agent reading only the Dockerfile may:
- Miss the WORKDIR mismatch (runtime copies from builder path but resolves to wrong dir)
- Fix the base image but leave pip install in the wrong stage (build succeeds but
  dependencies are missing at runtime)
- Use the wrong stage name in COPY --from (build fails with "failed to find stage")

The Planner, reading this spec with the full bug table, can direct the Executor
to fix all 5 bugs precisely rather than guessing.

## Deliverables

- Fixed `Dockerfile` in the workspace.
- Verifier must create `/shared/submission/attestation.json` with `verdict="pass"`.
