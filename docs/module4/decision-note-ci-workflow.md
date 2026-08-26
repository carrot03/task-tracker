# Technical Decision Note: CI Workflow Design

**Project:** Task Tracker API (Module 4)
**Status:** DRAFT
**Author:** htantawi

## 1. Context

The Task Tracker API is an in-memory, no-auth, no-database Python/FastAPI service (confirmed by `README.md` line 3 and the `FastAPI(... description=...)` block in `app/main.py`). Module 4 added DevOps-facing infrastructure on top of the existing app: a `Dockerfile`, a `.dockerignore`, and a GitHub Actions workflow at `.github/workflows/ci.yml`. Before this module there was no automated CI and no container packaging for the project [VERIFY — inferred from the absence of these files prior to this branch, not from a full history review].

The app has a single test suite runnable via `pytest` (per `README.md` "Run tests" section and `CLAUDE.md`), and the new workflow's job is scoped to running that suite on every push and pull request.

## 2. Decision

CI is implemented as a single GitHub Actions workflow (`.github/workflows/ci.yml`) with one job (`test`) that: checks out the repo, sets up Python 3.11, installs `requirements.txt`, and runs `pytest -v`. It triggers on every push to any branch and on pull requests targeting `main`. The workflow does not build or verify the `Dockerfile`, does not lint, and does not deploy anything. Docker packaging (`Dockerfile`, `.dockerignore`) is maintained as a separate, CI-unverified artifact in this module.

## 3. Alternatives Considered

- **No CI at all, rely on manual `pytest` runs before merge.** Rejected because it depends on every contributor remembering to run tests locally, with no enforcement.
- **Single workflow that also builds and smoke-tests the Docker image.** Not adopted in this pass; the workflow was scoped to test execution only, deferring Docker verification to a later change.
- **Run tests only on `pull_request`, not on every `push`.** Not adopted; the current workflow keeps both triggers, which gives faster feedback on feature branches at the cost of duplicate runs on PR branches [VERIFY — duplicate-run behavior inferred from the trigger config, not observed in an actual Actions run history].
- **Split `requirements.txt` into runtime vs. test/dev dependency files.** Not adopted; a single `requirements.txt` is installed both by CI and by the Docker build.

## 4. Trade-offs

DRAFT - REWRITE IN MY OWN WORDS

- Running on every branch push gives fast feedback per commit, but combined with the `pull_request → main` trigger it means the same commit can trigger two CI runs once a PR is open — this costs Actions minutes without adding coverage.
- Keeping the workflow to "install + test" only is simple and fast, but it means a broken `Dockerfile` (added in this same module) can merge to `main` without CI ever noticing, since nothing in `ci.yml` builds it.
- Installing the full `requirements.txt` (which includes `pytest` and `httpx`) is convenient for CI, but that same file is what the `Dockerfile`'s builder stage installs from, so runtime and test dependencies aren't separated at the source-of-truth level.
- No linting or formatting step keeps the pipeline short and reduces false-positive failures, at the cost of no automated style/consistency enforcement.

I would do this differently by...

## 5. Consequences

- Every push and PR against `main` gets automatic test feedback, which did not exist before this module.
- The `README.md` "Architecture" section still states "No auth, no Docker" (line 10), which is now inaccurate now that a `Dockerfile` exists — this is a documentation gap this decision introduces, not a functional one.
- Because the workflow never exercises the `Dockerfile`, the correctness of the container build is currently verified only by local/manual `docker build` runs, not by CI [VERIFY — no evidence in `ci.yml` of any Docker-related step].
- The app remains in-memory-only with no database, no auth, and no deployment step; this CI workflow does not change or imply otherwise — it only runs the existing test suite in an automated environment.

## 6. Open Questions

DRAFT - REWRITE IN MY OWN WORDS

- Should the `Dockerfile` be built and smoke-tested (e.g. `docker build` + a `/health` curl check) as part of `ci.yml`, given it was added in the same module?
- Should `push` be restricted (e.g. to `main` only, or removed in favor of `pull_request`) to avoid duplicate runs on branches with open PRs?
- Should `requirements.txt` be split into runtime and dev/test dependency files so the Docker runtime image doesn't inherit `pytest`/`httpx`?
- Should the workflow declare an explicit `permissions:` block, since none is currently set?
- Should `README.md`'s "No auth, no Docker" line be updated now that a `Dockerfile` exists in the repo?
