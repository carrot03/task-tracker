# Release Evidence
## Baseline
- Branch: final-project
- Date: August 26th, 2026
- Local app run command: ```uvicorn app.main:app --reload --port 8000```
- /health result: ```{"status":"ok","timestamp":"2026-08-26T18:12:44.495083+00:00"}```
- Frontend check:
![alt text](/assets/web_verification.png)
- Test command: ```python3 -m pytest```
- Test result:
![alt text](/assets/tests_verification.png)


## CI evidence
- Workflow file: `.github/workflows/ci.yml` — job `test`, triggers on push to any branch and on pull requests into `main`
- Latest run link or note: not confirmed here — `gh` CLI is unavailable in this environment (no network access to query GitHub Actions). Check the Actions tab at `github.com/carrot03/task-tracker` for the latest run on this branch. Screenshot evidence of a passing run below.
![alt text](/assets/ci_verification.png)
- Test command used by CI:
```bash
pytest -v
```
- Shortcut check: no continue-on-error / no || true / pytest is not skipped.


## Docker evidence
- Build command:
```bash
docker build -t task-tracker .
```
- Run command:
```bash
docker run --rm -p 8000:8000 task-tracker 
```
![alt text](/assets/docker-verfication.png)

- /health check: confirmed 200 — `curl http://localhost:8000/health` → `{"status":"ok","timestamp":"2026-08-26T18:17:10.328001+00:00"}`
- Non-root check, if implemented: confirmed — `Dockerfile` creates a dedicated user (`useradd --create-home --shell /usr/sbin/nologin app`) and sets `USER app` before `CMD`; verified live with `docker exec <container> whoami` → `app`
- No-baked-secrets check: confirmed clean — no `.env` file present in the image (`Dockerfile` only `COPY`s `app` and `frontend`, never `.env`); `docker exec <container> env | grep -iE 'secret|key|token|password'` found nothing project-related (only the base `python:3.11-slim` image's own `GPG_KEY` env var, used to verify the upstream Python source tarball, not a project secret)
## Documentation claim-vs-reality log
| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| README "Architecture" section stated "No auth, no Docker" (flagged as stale in `docs/module4/decision-note-ci-workflow.md` once the `Dockerfile` was added) | `grep` across the repo for that line | Resolved — the line no longer exists; the current README (Final Project version) instead states CI/Docker/health claims directly and accurately | None needed now; the open question in the module 4 decision note is moot since README was rewritten |
| README claim: "CI runs the pytest suite on push and/or pull request" | `.github/workflows/ci.yml` — `on: push` (all branches) and `on: pull_request` (into `main`), job step `pytest -v` | True, confirmed | None |
| README claim: "Docker image builds and runs with /health returning 200" | This session: `docker build -t task-tracker .`, `docker run -p 8000:8000 task-tracker`, `curl http://localhost:8000/health` → 200 | True, confirmed | Had to fix an unrelated local Docker credential-helper misconfiguration (`~/.docker/config.json` `credsStore: "desktop.exe"` unreachable from WSL) before the build would even pull its base image; no change to the app itself |