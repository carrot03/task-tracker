# Task Tracker — Architecture (Draft A)

## 1. What the app does
Task Tracker is a minimal Python/FastAPI REST API for managing tasks, with support for tags, comments, and overdue detection. A static single-page frontend is served from the same FastAPI app. There is no database and no authentication — all data lives in memory and is lost on restart.

## 2. Data model
- **Task**: `id`, `title`, `description`, `status` (`ToDo`/`InProgress`/`Done`), `priority` (`Low`/`Medium`/`High`), `assignee`, `tags` (list of embedded `TagResponse`, not just IDs), `due_date`, `created_at`, `updated_at`, and a computed `is_overdue` (derived from `due_date`/`status` at read time, never stored).
- **Tag**: `id`, `name` (unique, case-insensitive).
- **Comment**: `id`, `task_id`, `author`, `body`, `created_at` — scoped to a task; deleted automatically when the task is deleted.
- All request models use `extra="forbid"`, so unknown fields cause a 422.

## 3. Request flow — creating a task (`POST /tasks`)
1. FastAPI parses/validates the body against `TaskCreate` (title non-blank/≤200 chars, description ≤2000 chars, valid enum values, etc.); a validation failure returns 422 automatically.
2. `main.create_task` calls `store.get_tags_by_ids(payload.tag_ids)`; if any tag ID is missing or duplicated, it raises `HTTPException(422)` before any write occurs.
3. `store.add_task` generates a UUID `id`, sets `created_at`/`updated_at` to now (UTC), expands `tag_ids` into full `TagResponse` objects, and stores the resulting `TaskResponse` in the module-level `_tasks` dict.
4. The `TaskResponse` (with `is_overdue` computed on serialization) is returned with `201 Created`.

## 4. Key files
- `app/main.py` — all API routes (`/health`, `/tasks`, `/tags`, `/tasks/{id}/comments`); mounts the static frontend last so API routes take precedence.
- `app/models/__init__.py` — all Pydantic request/response schemas and enums.
- `app/store/__init__.py` — entire persistence layer (three in-memory dicts: `_tasks`, `_tags`, `_comments`); also owns timestamping and cascading comment deletion.
- `app/business_rules.py` — status-transition validation graph (raises `HTTPException(422)` directly).
- `frontend/index.html` — single-file static frontend; calls the API via relative `fetch` with `API_BASE = ""` (same-origin).
- `tests/conftest.py` — autouse fixture that resets storage between tests, plus shared `client`/`created_task` fixtures.
- `docs/midcourse/mini-adr.md` — architectural decisions and rejected alternatives (e.g. no persistence).
- `app/routers/__init__.py` — empty/unused; routes are not split out despite this package existing.

## 5. Conventions
- **Validation**: Pydantic field validators handle field-level rules (blank/length checks, enum normalization); cross-resource rules (tag existence, status transitions) are checked in `main.py` before delegating to `store`, and violations raise `HTTPException` directly rather than returning booleans.
- **Storage**: plain module-level dicts keyed by UUID string; no locking, no persistence; `_reset()` clears all three dicts and is used by tests for isolation.
- **Error handling**: 404 for missing tasks/comments, 409 for duplicate tag names, 422 for invalid tag references or invalid status transitions or schema violations — all raised inline in route handlers, not via exception middleware.
- **Frontend/backend interaction**: the frontend is static HTML/JS served by the same FastAPI instance via `StaticFiles` (mounted last, at `/`), and talks to the API with relative-path `fetch` calls — no separate frontend server or build step in normal operation (though CORS is configured for `localhost:5500/5173` dev-server scenarios).

## 6. Not visible / assumptions
- Could not confirm why `app/routers/` exists but is unused — likely a scaffold left for a future split that never happened.
- Comment ordering (`get_comments_by_task_id`) relies on dict insertion order; not explicitly documented as a guarantee, inferred from code.
- CORS origins (`5500`, `5173`, `null`) suggest a Live Server / Vite dev workflow, but no doc confirms this.
- Did not inspect `docs/decisions/comments-feature-plan.md` or CI/Docker setup in detail — out of scope for a code-only architecture read.
