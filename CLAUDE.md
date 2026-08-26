# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Task Tracker API — a minimal Python/FastAPI REST API for managing tasks, with a static frontend served from the same origin. In-memory storage only: no database, no auth, no persistence across restarts (see `docs/midcourse/mini-adr.md`).

## Commands

```bash
# Setup (once)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run the app (frontend served at the same URL by FastAPI)
uvicorn app.main:app --reload --port 8000

# Run all tests
python3 -m pytest

# Run a single test file / test
python3 -m pytest tests/test_tags.py
python3 -m pytest tests/test_tags.py::test_name
```

Note: this environment has no `python` executable — use `python3` (see `docs/midcourse/verification.md`).

There is no lint/format command configured in this repo.

## Architecture

- Single FastAPI app defined in `app/main.py` — all routes (`/health`, `/tasks`, `/tags`) live directly on `app`, not in `app/routers/`. The `app/routers/` package exists but is currently unused/empty; don't assume route handlers live there without checking `main.py` first.
- `app/models/__init__.py` — all Pydantic schemas (`TaskCreate`, `TaskUpdate`, `TaskResponse`, `TagCreate`, `TagResponse`, `TaskStatus`, `TaskPriority`). All models use `extra="forbid"`, so unknown fields in a request raise a 422. `TaskResponse.is_overdue` is a `@computed_field` derived from `due_date`/`status` at read time, not stored — this keeps overdue status from going stale.
- `app/store/__init__.py` — the entire persistence layer: two module-level dicts (`_tasks`, `_tags`) keyed by UUID. Tasks store expanded `TagResponse` objects (not just IDs); `get_tags_by_ids` returns `None` if any ID is missing or duplicated, which callers in `main.py` treat as a 422. `_reset()` clears both dicts and is used by the `tests/conftest.py` autouse fixture to isolate tests.
- `app/business_rules.py` — status-transition validation (`ToDo → InProgress → Done`, `Done → InProgress` to reopen; same-status is a no-op). Raises `HTTPException(422)` directly rather than returning a bool, so it's called inline from the route handler in `main.py`.
- The static frontend (`frontend/index.html`) is mounted at `/` via `StaticFiles` — this mount is registered *last* in `main.py` so API routes always take precedence over the catch-all static mount.
- Request flow for mutating endpoints: `main.py` validates cross-resource concerns (tag ID existence, status transitions) via `store`/`business_rules` before delegating the actual write to `store`, which is where model construction and timestamping (`created_at`/`updated_at`) happen.

## Testing conventions

- `tests/conftest.py` provides an autouse `_reset_storage` fixture (wipes the in-memory store before/after each test) plus `client` (a `TestClient`) and `created_task` fixtures — use these rather than instantiating `TestClient` or seeding data manually.
- Tests are organized by feature area: `test_tasks.py` (core CRUD/status transitions), `test_tags.py`, `test_overdue.py`, `test_health.py`.
- `tests/verify_a.py` is a standalone script (not a pytest file) that prints PASS/FAIL lines for model-validation edge cases; run it directly with `python3 tests/verify_a.py` rather than via pytest.

## Project documentation

`docs/midcourse/` contains the process record for this project's features (tags/labels, due-date/overdue filtering): user stories, the mini-ADR with rejected alternatives, a prompt log, and a verification record with manual browser-check steps and break-test evidence. Consult these before re-deciding something already decided there, and update the relevant doc when a covered decision changes.
