# Prompt Log

The prompts below summarize the AI-assisted workflow. I reviewed each response before accepting any implementation decision.

## Feature 1: Tags and labels

### Prompt 1: weak prompt and rewrite

**Weak prompt:** “I want to create further features in my app. I want to add tags and labels. Tell me how to do it.”

**What AI returned:** A broad coding plan with extra management functionality.

**Decision:** Rejected as too vague and ignored the proposed code. I rewrote it as: “Act as a senior developer. List three user stories and constraints for tags and labels. Do not mention code; focus only on this feature.”

### Prompt 2

**Prompt:** Given the three reviewed tag user stories, “List only the backend endpoints needed. Do not change code.”

**What AI returned:** Endpoints for listing/creating tags, creating/updating tasks with tag IDs, and filtering tasks by tag.

**Decision:** Accepted the endpoint outline. I kept the scope small and did not add rename/delete endpoints.

### Prompt 3

**Prompt:** “Implement the reviewed tag contract in this FastAPI in-memory task tracker. Add validation for trimmed non-blank tag names, reject unknown or duplicate task tag IDs, expose tag filtering, and add focused pytest tests. Preserve existing status behavior.”

**What AI returned:** Pydantic tag models, tag storage, task tag assignment/filtering, and tests.

**Decision:** Accepted the structure, edited the response shape to return expanded tag objects, and verified duplicate names case-insensitively.

## Feature 2: Due dates and overdue filter

### Prompt 1

**Prompt:** “Act as a senior developer. List three user stories and constraints for optional due dates and an overdue filter. Do not mention code.”

**What AI returned:** Stories for assigning dates, showing overdue tasks, and filtering them.

**Decision:** Accepted the stories, then corrected the boundary so today is not overdue and completed tasks are excluded.

### Prompt 2

**Prompt:** Given the reviewed stories and constraints, “List only the backend endpoints needed. Do not change code.”

**What AI returned:** Existing task create/update plus a task-list query parameter for overdue results.

**Decision:** Accepted the minimal API shape and chose `overdue=true` rather than a new endpoint.

### Prompt 3

**Prompt:** “Implement optional ISO due dates in task create/update, expose a derived `is_overdue` field, support `GET /tasks?overdue=true`, and add tests for invalid, today, past, future, cleared, and completed dates. Keep the in-memory design.”

**What AI returned:** Date validation, a computed response property, store filtering, frontend date/filter controls, and tests.

**Decision:** Accepted the implementation after checking the date boundary and edited the frontend to calculate the display indicator using the local calendar date.