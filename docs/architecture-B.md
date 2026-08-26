# Task Tracker — Architecture

## 1. What the app does
Task Tracker is a minimal Python/FastAPI REST API for managing tasks, with
comments and tags, plus a static frontend served from the same origin. Storage
is in-memory only (two/three module-level dicts) — no database, no auth, no
persistence across restarts.

## 2. Data model
- **Task**: `id`, `title` (required, ≤200 chars), `description` (≤2000 chars),
  `status` (`ToDo`/`InProgress`/`Done`, case-insensitive input), `priority`
  (`Low`/`Medium`/`High`), `assignee` (optional, blank→`None`), `tags` (expanded
  `TagResponse` objects, not just IDs), `due_date` (optional), `created_at`,
  `updated_at`, and `is_overdue` — a `@computed_field` derived from `due_date`/
  `status` at read time (never stored, so it can't go stale).
- **Tag**: `id`, `name` (non-blank, ≤50 chars, unique case-insensitively).
- **Comment**: `id`, `task_id`, `author` (≤100 chars), `body` (≤2000 chars),
  `created_at`. Scoped to a task; deleting a task cascades to delete its
  comments.
- All request/response models use `extra="forbid"` — unknown fields → `422`.

## 3. Request flow: creating a task (`POST /tasks`)
1. FastAPI validates the JSON body against `TaskCreate` (field validators for
   title/assignee; unknown fields rejected).
2. `main.py`'s `create_task` handler calls `store.get_tags_by_ids(payload.tag_ids)`
   to confirm every tag ID exists and none are duplicated; if not, raises
   `HTTPException(422)` before any write happens.
3. On success, `store.add_task` generates a UUID `id`, stamps `created_at`/
   `updated_at` (UTC), resolves `tag_ids` into full `TagResponse` objects, and
   stores the resulting `TaskResponse` in the `_tasks` dict.
4. The `TaskResponse` (with `is_overdue` computed at serialization time) is
   returned with `201 Created`.

## 4. Key files
- `app/main.py` — all route handlers (`/health`, `/tasks`, `/tags`,
  `/tasks/{id}/comments`); mounts the static frontend last so API routes win.
- `app/models/__init__.py` — all Pydantic schemas, enums, and field validators.
- `app/store/__init__.py` — the entire persistence layer (`_tasks`, `_tags`,
  `_comments` dicts) and all CRUD/query logic.
- `app/business_rules.py` — `validate_status_transition`, the status-transition
  state machine; raises `422` directly.
- `app/routers/` — present but empty/unused; do not assume handlers live here.
- `frontend/index.html` — static single-file frontend, served via `StaticFiles`.
- `tests/conftest.py` — `_reset_storage` (autouse), `client`, `created_task`
  fixtures.
- `AGENTS.md` — agent operating rules (read-only by default, no `app/` edits
  without approval, cite file/line for behavior claims).

## 5. Conventions
- **Validation**: enforced in Pydantic models (`extra="forbid"`, length limits,
  strip/normalize validators) plus cross-resource checks (tag existence, status
  transitions) done explicitly in `main.py` before delegating to `store`.
- **Storage**: plain in-process dicts keyed by UUID string; no ORM, no schema
  migrations; `store._reset()` wipes state (used by the autouse test fixture).
- **Error handling**: route handlers raise `HTTPException` directly (404 for
  missing resources, 409 for duplicate tag names, 422 for invalid transitions
  or bad `tag_ids`) — no central exception-handling middleware observed.
- **Frontend/backend interaction**: `frontend/index.html` is mounted at `/` via
  `StaticFiles(html=True)`, registered after all API routes so `/tasks`, `/tags`,
  etc. always take precedence over the static catch-all. CORS is restricted to
  specific localhost dev origins, `allow_credentials=False`.

## 6. Not visible / assumptions
- **Comments feature undocumented in AGENTS.md/CLAUDE.md**: `app/main.py` and
  `app/store/__init__.py` implement a full comments sub-resource
  (`POST/GET /tasks/{id}/comments`, `GET/DELETE /tasks/{id}/comments/{id}`) and
  `tests/test_comments.py` exists, but neither AGENTS.md nor CLAUDE.md mentions
  comments — likely added after those docs were last updated.
- No lint/format tool is configured (confirmed "not confirmed" in AGENTS.md).
- `app/routers/` is empty — unclear whether it's planned for future use or dead
  scaffolding; not stated in either doc.
- Whether the static frontend actually calls the comments endpoints was not
  checked (frontend/index.html not inspected in this pass).
- Docker workflow exists in a `Dockerfile` but isn't documented as supported
  elsewhere — treated as unconfirmed per AGENTS.md's own caveat.
