# Comments on Tasks — Design Document

Status: **Implemented** (2026-08-26). All sections below describe what was
actually built, updated from the original pre-implementation draft. The
`app/` changes were made under explicit approval per `AGENTS.md` §4; the
`tests/`/`frontend/` changes were made under a separate, later approval in
the same thread. See §7 for a summary of what changed since the draft and
the one implementation-time bug found and fixed.

## 1. Data Model

**Where it belongs:** `app/models/__init__.py`, alongside `TagCreate`/`TagResponse`
(models/__init__.py:65–81). Two new models, following that exact split:

- `CommentCreate` — request body for `POST`. Fields: `author: str`, `body: str`.
  Does **not** include `task_id` (see API Routes — the task is identified by the
  URL path, matching how `get_task`/`patch_task` take `task_id` as a path param
  rather than a body field) or `id`/`created_at` (server-generated, same as
  `TaskResponse.id`/`created_at` in `store.add_task`, store/__init__.py:85–100).
- `CommentResponse` — the stored/returned shape: `id: str`, `task_id: str`,
  `author: str`, `body: str`, `created_at: datetime`. No `updated_at` — nothing
  in the requested field list implies comments are editable, so this plan treats
  them as immutable/append-only (see Open Questions).

**Validation pattern to reuse:** `models/__init__.py` has an existing convention
of a private `_validate_x` helper called from a `@field_validator`
(`_validate_title` at models/__init__.py:40–46, `_validate_tag_name` at
models/__init__.py:56–62) — strip, reject blank, enforce max length. The
`author`/`body` 1–100 / 1–2000 constraints fit this pattern directly: a
`_validate_comment_author` and `_validate_comment_body` helper (or reuse of a
generalized helper) that strips, rejects empty-after-strip, and enforces the
max length. `Field(max_length=...)` alone (as used for `TaskCreate.description`,
models/__init__.py:87) would not enforce "non-blank," so the validator approach
matches what the repo already does for required, non-blank text fields like
`title`.

`model_config = ConfigDict(extra="forbid")` on both models, matching every
existing model (models/__init__.py:66, 77, 84, 106, 130) — this is what makes
`test_create_task_unknown_field_returns_422` (test_tasks.py:42–45) pass today,
and the same behavior should apply to comments.

**Storage:** `app/store/__init__.py` holds two module-level dicts, `_tasks` and
`_tags` (store/__init__.py:17–18). A third, `_comments: dict[str, CommentResponse]`,
keyed by comment id, would follow the same shape. Needed functions, mirroring
the existing `add_tag`/`get_all_tags` naming (store/__init__.py:21–46):
`add_comment(task_id, payload) -> CommentResponse`, `get_comments_by_task_id(task_id) -> list[CommentResponse]`,
possibly `get_comment_by_id`/`delete_comment` depending on which routes are
approved (see §2). **`_reset()` (store/__init__.py:198–200) must clear `_comments`
too**, or the autouse `_reset_storage` fixture in `tests/conftest.py` (conftest.py:8–12)
will leak comment state across tests silently.

**Embedding question:** `TaskResponse` already embeds full `TagResponse` objects
in a `tags: list[TagResponse]` field rather than raw IDs (models/__init__.py:138,
populated via `get_tags_by_ids` in `store.add_task`, store/__init__.py:94).
**Decision: not embedded.** `TaskResponse` is unchanged — comments are only
reachable via the dedicated `/tasks/{task_id}/comments` endpoints (§2). This
was the lower-risk path flagged in §5 and avoided touching any existing
task-response test.

## 2. API Routes

All current routes live directly on `app` in `app/main.py` — `app/routers/`
exists but is an empty, unused package (`"""API route modules."""` is its only
content). New routes were added to `main.py`, next to the existing `/tasks`
and `/tags` handlers, matching the confirmed convention.

Implemented routes, nested under the task (a new pattern for this repo — no
prior nested-resource precedent existed):

| Method | Path | Request body | Response body | Notes |
|---|---|---|---|---|
| `POST` | `/tasks/{task_id}/comments` | `CommentCreate` | `CommentResponse`, `201` | Mirrors `create_task` (main.py:120–139): validate parent exists, then delegate the write to `store`. |
| `GET` | `/tasks/{task_id}/comments` | — | `list[CommentResponse]`, `200` | Mirrors `list_tasks`/`list_tags` (main.py:58–95). |
| `GET` | `/tasks/{task_id}/comments/{comment_id}` | — | `CommentResponse`, `200` | Mirrors `get_task` (main.py:142–158). |
| `DELETE` | `/tasks/{task_id}/comments/{comment_id}` | — | `204 No Content` | Mirrors `delete_task` (main.py:161–176). Unrestricted — no auth exists in this repo, confirmed acceptable (§6.3). |

All four routes were built — the single-`GET` and `DELETE` routes were listed
as "optional" in the original draft but were confirmed in scope (§6.3).

No `PATCH`/`PUT` route was added — there's no `updated_at` in the requested
field list, and no analogous "editable" behavior to copy from tags (tags have
no update endpoint either — only `create` and `list`, per `mini-adr.md`'s
explicit scope note: "No... tag rename/delete... was added"). Comments remain
immutable after creation; deletion is the only mutation.

**Error cases**, matching the existing style of raising `HTTPException` inline
in the route handler (e.g., main.py:155–158, main.py:174–176) rather than
returning `None`/`False` from `store` and letting the caller decide:

- `404` if `task_id` doesn't exist — for `POST`, `GET` (list), `GET`
  (single), and `DELETE`. This matches `get_task`'s `404` behavior (main.py:156–158)
  rather than, say, silently returning an empty list for a list on a missing
  task.
- `404` if `comment_id` doesn't exist, for the single-`GET`/`DELETE` routes,
  with a detail message following the existing convention
  (`f"Task with id {task_id} not found"`, main.py:157) — e.g. `f"Comment with id {comment_id} not found"`.
- `422` for validation failures on `CommentCreate`: blank/missing `author`,
  `author` over 100 chars, blank/missing `body`, `body` over 2000 chars, or any
  extra field (via `extra="forbid"`) — these are all handled by Pydantic/FastAPI
  automatically once the model is defined correctly, same as `test_create_task_missing_title_returns_422`
  etc.
- No `409` case is evident for comments (no uniqueness constraint like the tag
  name's case-insensitive dedup in `store.add_tag`, store/__init__.py:31–32).

## 3. Tests

`tests/test_comments.py` (20 tests), following the two observed styles in
`tests/test_tags.py` (module-level `create_comment` helper + flat `test_`
functions) and `tests/test_tasks.py`. Reuses the `client` and `created_task`
fixtures from `tests/conftest.py` (conftest.py:15–24) rather than
instantiating `TestClient` or seeding a task manually.

Full suite after adding this file: **53 passed** (33 pre-existing + 20 new).

**Happy path:**
- `test_create_comment_returns_201_with_expected_fields` — asserts `id`,
  `task_id`, `author`, `body`, `created_at` are all present and match input
  (mirrors `test_create_task_valid_returns_201_with_full_body`, test_tasks.py:1–21).
- `test_list_comments_returns_comments_for_task_in_creation_order`
- `test_list_comments_empty_task_returns_200_and_empty_list` (mirrors
  `test_list_tasks_empty_returns_200_and_empty_list`, test_tasks.py:48–52).
- `test_get_comment_by_id_returns_comment` (mirrors
  `test_get_task_by_id_returns_task`, test_tasks.py:75–79).
- `test_delete_comment_returns_204_no_body` (mirrors
  `test_delete_existing_returns_204_no_body`, test_tasks.py:127–131).

**Validation:**
- `test_create_comment_missing_author_returns_422`
- `test_create_comment_blank_author_returns_422`
- `test_create_comment_author_over_100_chars_returns_422`
- `test_create_comment_missing_body_returns_422`
- `test_create_comment_blank_body_returns_422`
- `test_create_comment_body_over_2000_chars_returns_422`
- `test_create_comment_unknown_field_returns_422` (mirrors
  `test_create_task_unknown_field_returns_422`, test_tasks.py:42–45 — confirms
  `extra="forbid"` is wired up on `CommentCreate`)
- `test_create_comment_id_and_created_at_are_not_client_settable` — POST with
  `id`/`created_at` in the body either 422s (if `extra="forbid"` rejects them,
  since they're not fields on `CommentCreate`) or is silently ignored; this
  test should pin down which.

**Edge cases:**
- `test_create_comment_on_missing_task_returns_404`
- `test_list_comments_on_missing_task_returns_404`
- `test_get_comment_not_found_returns_404` (comment id doesn't exist at all)
- `test_get_comment_wrong_task_returns_404` — a comment that exists but
  belongs to a *different* task id than the one in the URL.
- `test_delete_comment_not_found_returns_404`
- `test_comments_isolated_between_tasks` — a comment created on task A never
  appears in task B's list (mirrors the tag-isolation intent of
  `test_tag_filter_excludes_task_after_its_tag_is_changed`, test_tags.py:54–64).
- `test_deleting_task_removes_its_comments` — confirms cascade delete (§6.4).
  Cascade isn't observable through the API alone once the parent task is gone
  (list/get on that `task_id` 404 either way, cascaded or orphaned), so this
  test imports `app.store` directly and asserts the comment's id is no longer
  a key in `store._comments`.

## 4. Frontend Changes

**File:** `frontend/index.html` only — it's the single static file serving the
whole UI (mounted last in `main.py`, main.py:223–225). There was previously
**no comments UI of any kind**; this was net-new.

**What was added**, inside the existing edit modal's `.modal-body`, after the
tag `<fieldset>`: a new `#task-comments-section` fieldset containing —
- `#task-comments-hint` — a `<p>` shown only in "create" mode ("Save the task
  first to add comments.").
- `#task-comments-list` — the rendered list of existing comments (author,
  body, a `Date.toLocaleString()`-formatted timestamp, a per-comment "Delete"
  button), or a "No comments yet." placeholder when empty (styled like the
  existing `.tag-checkboxes-empty` placeholder).
- `#task-comments-form` — an `author` text input + a `body` textarea +
  an "Add Comment" button (`type="button"`, not `type="submit"`, so it can't
  accidentally trigger the outer task form's submit).

`openModal` toggles which of `#task-comments-hint` / `#task-comments-form` is
visible based on `mode`, and calls `fetchComments(task.id)` in edit mode;
`closeModal` clears `state.comments`. New CSS added: `.comment-list`,
`.comment-item`, `.comment-item-header`, `.comment-author`,
`.comment-timestamp`, `.comment-body`, `.comment-delete-button`,
`.comment-form`, `.comment-hint`.

**JS changes**, following the existing conventions:
- `fetchComments`, `handleAddComment`, `handleDeleteComment` — all go through
  the existing `fetchJson` helper against `${API_BASE}/tasks/{id}/comments[/{id}]`.
- `renderComments` uses the existing `createElement` helper, matching how
  `buildCard`/`buildColumn` construct DOM nodes.
- Errors surface through the existing `setModalError`/`clearModalError` pair.

**Verified live** (headless Chromium, `tests/test_comments.py`-adjacent manual
run, not committed to the repo): create-mode shows the hint and hides the
form; edit-mode shows the form; adding a comment updates the list
immediately; deleting a comment removes it and restores the empty-state
message; zero console errors. See §7 for a bug this surfaced and fixed.

Not addressed (still an open follow-up, not decided in this thread): whether
the task card itself (`buildCard`) should show a comment count without
opening the modal — that's an additional fetch-per-card cost the current
board doesn't pay for anything else today.

## 5. Migration Notes

There is no database and no persistence across restarts (`README.md`,
`CLAUDE.md`, `mini-adr.md`, confirmed in `AGENTS.md` §3) — "migration" here
means in-memory data-shape changes only, not a schema migration tool.

- A new `_comments` dict was added to `app/store/__init__.py` alongside
  `_tasks`/`_tags` (store/__init__.py:17–18), and is cleared inside `_reset()`
  along with them — confirmed by `test_list_comments_empty_task_returns_200_and_empty_list`
  and the rest of the suite passing with no cross-test leakage.
- Existing tasks have no comments by default; this was purely additive, no
  backfill needed — same shape of change as the mid-course ADR's addition of
  `tags`/`due_date` (`mini-adr.md`).
- Comments were **not** embedded into `TaskResponse` (§1) — no existing model
  or test needed to change; `TaskResponse` and every existing test asserting
  its exact JSON shape are untouched.
- `delete_task` (store/__init__.py) now also calls `delete_comments_by_task_id`
  before returning, so a deleted task never leaves orphaned rows in
  `_comments` (§6.4).

## 6. Open Questions — resolved

All five were decided before/during implementation:

1. **Nested route vs. flat resource.** Resolved: nested,
   `/tasks/{task_id}/comments` — confirmed as an assumption (2026-08-26,
   see bottom of doc).
2. **Embed in `TaskResponse` or keep separate?** Resolved: kept separate.
   `TaskResponse` is unchanged; comments are reachable only through
   `/tasks/{task_id}/comments` (§1, §5).
3. **Are comments ever editable or deletable, and by whom?** Resolved:
   not editable (no `PATCH`, no `updated_at`); deletable via unrestricted
   `DELETE /tasks/{task_id}/comments/{comment_id}` (confirmed 2026-08-26 —
   acceptable given no auth system exists anywhere in this repo).
4. **Cascade behavior when a task is deleted.** Resolved: cascade delete.
   `store.delete_task` now also removes every comment belonging to that task
   (confirmed 2026-08-26), rather than orphaning them or blocking the delete.
   Verified by `test_deleting_task_removes_its_comments` inspecting
   `store._comments` directly (§3).
5. **Should `GET /tasks/{task_id}/comments` on a missing task 404 or return
   an empty list?** Resolved: `404`, matching `get_task`'s existing behavior
   — confirmed as an assumption (2026-08-26).

## 7. Implementation Notes

**Files changed:**
- `app/models/__init__.py` — `CommentCreate`, `CommentResponse`,
  `_validate_comment_author`, `_validate_comment_body`.
- `app/store/__init__.py` — `_comments` dict; `add_comment`,
  `get_comments_by_task_id`, `get_comment_by_id`, `delete_comment`,
  `delete_comments_by_task_id`; `_reset()` and `delete_task` updated.
- `app/main.py` — `create_comment`, `list_comments`, `get_comment`,
  `delete_comment` route handlers, all 404-checking the parent task first.
- `tests/test_comments.py` — new, 20 tests (§3).
- `frontend/index.html` — comments section in the edit modal, new CSS,
  new JS functions (§4).

**Bug found and fixed during manual browser verification:** the comment
form's `hidden` attribute (used to hide `#task-comments-form` in "create"
mode) was silently overridden by the `.comment-form { display: grid }` CSS
rule — an author-stylesheet `display` declaration beats the browser's
built-in `[hidden] { display: none }` rule regardless of selector order or
specificity. Fixed by adding an explicit `.comment-form[hidden] { display:
none; }` rule. Caught by a headless-Chromium script that checked
`page.isVisible('#task-comments-form')` in create mode before and after the
fix (`true` → `false`); not something the Python test suite could have
caught, since it's pure frontend rendering behavior.

**Verification performed:**
- `venv/bin/python3 -m pytest -q` → 53 passed (33 pre-existing + 20 new).
- `node --check` on the extracted `<script>` contents → syntax valid.
- Live server (`venv/bin/uvicorn app.main:app --port 8000`) driven with a
  headless-Chromium Playwright script: create-task flow, edit-modal comment
  add/list/delete flow, create-mode hint/form toggle, zero console errors.
  No project `run` skill existed for this repo prior to this session.

## Files read

- `AGENTS.md`
- `README.md`
- `app/main.py`
- `app/models/__init__.py`
- `app/store/__init__.py`
- `app/business_rules.py`
- `app/routers/__init__.py`
- `tests/conftest.py`
- `tests/test_tags.py`
- `tests/test_tasks.py`
- `frontend/index.html`
- `docs/midcourse/mini-adr.md`

Not read (not required by the field/behavior questions this plan needed to
answer, but worth noting): `tests/test_overdue.py`, `tests/test_health.py`,
`tests/verify_a.py`, `docs/midcourse/user-stories.md`,
`docs/midcourse/prompt-log.md`, `docs/midcourse/verification.md`,
`docs/module4/*`, `docs/module5/*`, `CLAUDE.md` (already in context via
system reminder, not re-read as a file).

## Assumptions to verify

Confirmed true by the project owner (2026-08-26):

- Routes belong in `main.py` rather than `app/routers/`.
- `CommentCreate` validation follows the strip-then-reject-blank pattern used
  for `title`/tag `name`.
- Comments are nested under `/tasks/{task_id}/comments`.
- Comments are immutable/append-only (no edit endpoint).
- A missing parent task 404s (matching `get_task`'s existing behavior).
- This feature is out of scope for the existing `docs/midcourse/` decision
  record and would warrant its own doc (this file) rather than an addendum to
  `mini-adr.md`.

Confirmed true by the project owner, resolving the remaining open questions
(2026-08-26):

- Comment deletion is in scope, unrestricted (no auth exists in this repo).
- Deleting a task cascade-deletes its comments.
