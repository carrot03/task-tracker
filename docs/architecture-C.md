# Task Tracker — Architecture (Strategy C: Targeted Context)

## What the app does
Task Tracker is a FastAPI REST API for managing tasks, each of which can carry
tags, a priority/status, an optional due date, and comments. Storage is
in-memory only — the app has no authentication and no persistence across
restarts. A static frontend is served from the same FastAPI app.

## Data model
- **TaskStatus** (enum): `ToDo`, `InProgress`, `Done` — parsed case-insensitively.
- **TaskPriority** (enum): `Low`, `Medium`, `High` — parsed case-insensitively.
- **TagCreate / TagResponse**: `name` (non-blank, ≤50 chars); response adds `id`.
- **CommentCreate / CommentResponse**: `author` (≤100 chars), `body` (≤2000 chars); response adds `id`, `task_id`, `created_at`.
- **TaskCreate / TaskUpdate**: `title` (non-blank, ≤200 chars), `description` (≤2000 chars), `status`, `priority`, `assignee` (≤100 chars, optional), `tag_ids` (list), `due_date` (optional date). `TaskUpdate` makes every field optional for partial updates.
- **TaskResponse**: id, title, description, status, priority, assignee, `tags` (full `TagResponse` objects, not just ids), `due_date`, `created_at`, `updated_at`, plus a computed `is_overdue` (true when `due_date` is past and `status != Done`, computed at read time, not stored).
- All models use `extra="forbid"` — unknown request fields are rejected.

## Request flow: creating a task (`POST /tasks`)
1. FastAPI parses the body into a `TaskCreate`; Pydantic validators run (trim/validate `title`, normalize `assignee`, reject unknown fields).
2. The route handler calls `store.get_tags_by_ids(payload.tag_ids)`; if any id is missing or duplicated, it raises `HTTPException(422)` before touching storage.
3. Otherwise it calls `store.add_task(payload)`, which generates a `uuid4` id, sets `created_at`/`updated_at` to the current UTC time, re-resolves `tag_ids` into full `TagResponse` objects, and stores the resulting `TaskResponse` in the `_tasks` dict keyed by id.
4. The new `TaskResponse` is returned with HTTP 201.

## Key files
- `app/main.py` — FastAPI app instance, all route handlers (`/health`, `/tasks`, `/tags`, `/tasks/{id}/comments`), CORS config, static frontend mount.
- `app/models/__init__.py` — all Pydantic request/response schemas and enums, including the computed `is_overdue` field.
- `app/store/__init__.py` — in-memory persistence: three module-level dicts (`_tasks`, `_tags`, `_comments`) plus CRUD functions and a `_reset()`.
- `app/business_rules.py` — imported by `main.py` for `validate_status_transition`; contents not read.
- `frontend/` — static directory mounted at `/`; contents not read.

## Conventions
- **Validation**: Pydantic `field_validator`s strip/normalize strings and enforce blank/length rules; `extra="forbid"` on every model rejects unknown fields; enums accept case-insensitive input via `_missing_`.
- **Storage**: plain in-memory dicts keyed by string UUIDs (`uuid4()`); no database. `store.update_task` applies only explicitly-set fields (`model_dump(exclude_unset=True)`) and re-stamps `updated_at`. `store._reset()` clears all three dicts.
- **Error handling**: route handlers in `main.py` raise `HTTPException` directly and inline (404 for missing task/comment, 409 for duplicate tag name, 422 for invalid `tag_ids` or, per docstring, invalid status transitions) — no centralized exception-handling layer visible.
- **Frontend/backend interaction**: the static frontend is mounted at `/` via `StaticFiles` *after* all API routes are registered, so API routes take precedence over the catch-all static mount. CORS is enabled for `localhost:5500`, `127.0.0.1:5500`, `localhost:5173`, and `null` origins, `allow_credentials=False`.

## Not visible or assumptions
- The actual status-transition rules enforced by `validate_status_transition` (`app/business_rules.py` was not read).
- The frontend's structure, behavior, or how it calls the API (`frontend/` was not read).
- Any test, config, or dependency files (`tests/`, `requirements.txt`, `.env.example`, etc.) — not read.
- Whether any other storage/config module exists beyond `app/store/__init__.py`.
