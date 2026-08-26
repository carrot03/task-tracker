# Verification Record

## Baseline

Before the final documentation pass, the existing test command was attempted as `python -m pytest -q`; this environment has no `python` executable. The equivalent available command is `python3 -m pytest -q`.
![alt text](../assets/image.png)

## Automated checks

Final check: `python3 -m pytest -q`

Result: all tests passed, including the original task/health tests and the new tag and overdue tests. The feature test files cover more than the required four new pytest tests:

- Tags: create/list, duplicate and blank validation, assignment, replacement, unknown IDs, and filtering.
- Due dates: valid/invalid dates, clearing, today/future/past boundaries, completed tasks, overdue filtering, and update behavior.

## Manual browser checks

With `uvicorn app.main:app --reload --port 8000` running at `http://127.0.0.1:8000/`:

1. Created a tag from **New Tag**, selected it in the task form, and confirmed its chip appeared on the card.
2. Selected the tag filter and confirmed unrelated cards disappeared; cleared it and confirmed the board restored.
3. Created a task with a past due date and confirmed the card showed **Overdue**.
4. Selected the overdue filter and confirmed only incomplete past-due tasks remained.
5. Edited the due date to today and confirmed the overdue indicator disappeared.

## Behavior contract before/after refactor

The refactor preserved the existing task contract: status transitions remain validated, partial updates preserve unspecified fields, missing tasks return 404, and empty filters return 200 with `[]`. New contract: tags are validated and expanded in responses; due dates are optional ISO dates; overdue means strictly before today and not `Done`.

## Break Test evidence

I temporarily changed the overdue comparison from `due_date < date.today()` to `due_date <= date.today()`. The due-today test failed, proving the boundary test detects the regression. I also temporarily removed the tag filter condition; the tag-filter test failed because an unrelated task was returned. Both temporary changes were restored before the final test run.