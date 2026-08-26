# Mini ADR: Tags and Due Dates

## Decision

Implement tags as in-memory records with stable IDs. Tasks store a list of tag IDs internally and return expanded tag objects. Add optional `due_date` validation to task create/update models, compute `is_overdue` in the response model, and support `GET /tasks?overdue=true` and `GET /tasks?tag_id=...`.

## Why

This matches the existing in-memory architecture, keeps the API contract explicit, and lets the frontend use the same state for card indicators and filters. Overdue status is derived rather than stored, so it cannot become stale as the calendar changes or a task is completed.

## Alternatives considered

AI suggested a separate tag-management screen, tag rename/delete endpoints, and a database-backed many-to-many relationship. Those options were rejected as too large for the sprint and inconsistent with the current project architecture. A frontend-only overdue calculation was also considered, but backend filtering and a response-level `is_overdue` field provide one API contract for clients.

## Scope

No persistence, authentication, bulk operations, tag rename/delete, or search feature was added.