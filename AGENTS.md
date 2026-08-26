# AGENTS.md

Guidance for Codex/AI agents working in this repository. This file governs how an
agent should operate here; it does not replace `CLAUDE.md` (Claude Code guidance) or
`docs/midcourse/` (project decision record) — read those too when relevant.

## 1. Project summary

Task Tracker API — a minimal Python/FastAPI REST API for managing tasks, with a
static frontend (`frontend/index.html`) served from the same origin via
`StaticFiles`. Storage is two module-level in-memory dicts (`app/store/__init__.py`):
no database, no authentication, and no persistence across restarts. Mid-course
features add tags/labels and due-date/overdue filtering (see
`docs/midcourse/mini-adr.md`).

## 2. Tech stack and commands

**Stack** (from `requirements.txt`): FastAPI 0.115.12, Pydantic 2.11.3,
uvicorn 0.34.0 (`[standard]`), python-dotenv 1.1.0, pytest 9.1.1, httpx 0.28.1
(used by `TestClient`). CI (`.github/workflows/ci.yml`) runs on Python 3.11.
No `pyproject.toml`. No lint/format tool is configured in this repo — not confirmed
if one is desired.

**Setup:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Note: this environment has no `python` executable — use `python3` for all commands
(per `CLAUDE.md`), even though `README.md` shows plain `python`.

**Run:**
```bash
uvicorn app.main:app --reload --port 8000
```
Frontend: `http://127.0.0.1:8000/`. Swagger/OpenAPI docs: `http://127.0.0.1:8000/docs`.

**Test:**
```bash
python3 -m pytest              # all tests
python3 -m pytest tests/test_tags.py
python3 -m pytest tests/test_tags.py::test_name
python3 tests/verify_a.py      # standalone script (not pytest); prints PASS/FAIL lines
```
CI runs `pytest -v` on every push branch and on PRs into `main`.

**Docker** (from `Dockerfile`, not documented elsewhere as a supported workflow —
treat build/run details beyond the Dockerfile itself as not confirmed):
```bash
docker build -t task-tracker .
docker run -p 8000:8000 task-tracker
```

## 3. Business rules visible in code

- **Task status** (`app/models/__init__.py::TaskStatus`): `ToDo`, `InProgress`,
  `Done`. Input matching is case-insensitive (`_missing_` normalizes).
- **Status transitions** (`app/business_rules.py`): only
  `ToDo → InProgress`, `InProgress → Done`, `Done → InProgress` (reopen) are valid.
  Setting a task to its current status is a no-op (always allowed). Any other
  transition raises `HTTPException(422)`.
- **Task priority**: `Low`, `Medium`, `High` (case-insensitive input, same pattern
  as status).
- **Title**: required, stripped, must be non-blank, max 200 characters
  (`_validate_title`).
- **Description**: optional, defaults to `""`, max 2000 characters.
- **Assignee**: optional, stripped; empty string normalizes to `None`; max 100
  characters.
- **Tags**: `TagCreate.name` must be non-blank after stripping, max 50 characters.
  Creating a tag with a name that already exists (case-insensitive) returns
  `409 Conflict` (`app/store/__init__.py::add_tag`).
- **Task `tag_ids`**: on create/update, must reference existing tag IDs with no
  duplicates, or the request is rejected with `422` (`store.get_tags_by_ids`,
  enforced in `app/main.py` before the write).
- **`due_date`**: optional date field on `TaskCreate`/`TaskUpdate`.
- **`is_overdue`**: a `@computed_field` on `TaskResponse` (not stored) — `True`
  only if `due_date` is set, is strictly before today, and `status != Done`. This
  keeps overdue state from going stale.
- **Filtering** (`GET /tasks`): `status`, `priority`, `tag_id`, `overdue` filters
  combine with AND. `overdue=False` behaves identically to omitting the filter
  (only `overdue=True` actually filters).
- **Strict schemas**: all Pydantic models use `extra="forbid"` — unknown fields in
  a request body raise `422`.
- **No auth, no persistence**: confirmed in `README.md`, `CLAUDE.md`, and
  `docs/midcourse/mini-adr.md` (in-memory dicts, wiped by `store._reset()` and on
  process restart).
- **CORS**: only specific localhost origins are allowed
  (`app/main.py`), `allow_credentials=False`.

## 4. Module 5 guardrails

- **Docs-first**: before proposing or making a change, check `docs/midcourse/`
  (user stories, mini-ADR, verification record) and `docs/module4/` for decisions
  already made on this topic. Don't re-litigate a settled decision without saying
  so explicitly.
- **Read-only by default**: unless the user has explicitly approved a specific
  edit in this thread, treat requests as read/explain/analyze only. Propose diffs
  for review rather than applying them unprompted.
- **One task per thread**: scope each conversation/thread to a single, clearly
  stated task. If the user asks for something unrelated mid-thread, flag that it's
  a new task rather than silently expanding scope.
- **No `app/` or `frontend/` changes without explicit approval**: do not modify
  anything under `app/` (routes, models, store, business rules) or `frontend/`
  (the static frontend served via `StaticFiles`) unless the user has explicitly
  approved that specific change in this thread. This file, `AGENTS.md`, is the one
  exception the agent may write to when asked to draft/update it.

## 5. Security and governance reminders

- Never paste, log, or otherwise expose secrets or `.env` contents (`.env` is
  git-ignored; `.env.example` only documents `PORT` and `APP_ENV` — treat any
  future secret-bearing variable the same way).
- Never run destructive commands (e.g. `rm -rf`, force-push, dropping data) without
  explicit user confirmation — this project has no database, but the same
  discipline applies to the working tree and git history.
- Always cite the file(s) and, where useful, line numbers backing a claim about
  behavior — don't assert business logic without pointing to the code.
- Do not invent commands, endpoints, dependencies, or business rules that aren't
  visible in this repo. If something can't be confirmed by reading the code or
  docs, say "not confirmed" rather than guessing.
