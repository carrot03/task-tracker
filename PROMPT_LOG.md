# AI-Assisted Coding — Module 2 Prompt Library

Log of prompts used to incrementally build the `/tasks` routes in this project, along with the outputs applied to `app/main.py` and `app/business_rules.py`.

---

## 1. GET /tasks (list with optional filters)

**Prompt:**
```
Add ONE route to my existing FastAPI app.
Context files:
@app/main.py
@app/models.py
@app/storage.py
Generate ONLY the GET /tasks list route.
Exact specification:
- Route: GET /tasks
- Status code: 200 default is fine
- Tags: ["tasks"]
- Optional query params:
 - status: TaskStatus | None = None
 - priority: TaskPriority | None = None
- Response model: list[TaskResponse]
- Behavior: return storage.get_all_tasks(status=status, priority=priority)
- Empty filter result returns 200 with []
Imports to add only if missing:
from app.models import TaskStatus, TaskPriority, TaskResponse
from app import storage
DO NOT:
- DO NOT return 404 for an empty list.
- DO NOT manually validate enum values; Pydantic/FastAPI handles invalid query values.
- DO NOT add try/except around storage.get_all_tasks.
- DO NOT modify POST /tasks or any other route.
Output only the imports to add and the new route function in one code block.
```

**Note:** the project's actual module is `app.store` (`app/store/__init__.py`) and `app/models/__init__.py`, not `app/storage.py` / `app/models.py` as referenced in the prompt. Kept as `store` per user preference rather than renaming the module.

**Output applied:**
```python
from app.models import TaskPriority, TaskResponse, TaskStatus
from app import store


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[TaskResponse]:
    return store.get_all_tasks(status=status, priority=priority)
```

---

## 2. POST /tasks (create)

**Prompt:**
```
Add ONE route to my existing FastAPI app.
Context files:
@app/main.py
@app/models.py
@app/storage.py
AI-Assisted Coding - Module 2 Prompt Library
Generate ONLY the route handler for POST /tasks.
Exact specification:
- Route: POST /tasks
- Status code: 201 Created using status.HTTP_201_CREATED
- Tags: ["tasks"]
- Request body: TaskCreate
- Response model: TaskResponse
- Behavior: call storage.add_task(payload) and return the result directly
- Error behavior:
 - missing, blank, or overlong title -> HTTP 422 through Pydantic
 - invalid status or priority -> HTTP 422 through Pydantic
 - unknown input field -> HTTP 422 through Pydantic
Imports to add at the top of app/main.py if missing:
from fastapi import status
from app.models import TaskCreate, TaskResponse
from app import storage
Exact decorator and signature:
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
 ...
DO NOT:
- DO NOT create a new FastAPI() instance.
- DO NOT generate UUIDs or timestamps in the route; storage handles that.
- DO NOT add manual request validation; rely on Pydantic.
- DO NOT add try/except around storage.add_task.
- DO NOT add any other route.
Output only the imports to add and the route function in one code block.
```

**Output applied:**
```python
from fastapi import status
from app.models import TaskCreate  # added to existing app.models import line


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return store.add_task(payload)
```

---

## 3. GET /tasks/{task_id} (fetch by id)

**Prompt:**
```
Add ONE route to my existing FastAPI app.
Context files:
@app/main.py
@app/models.py
@app/storage.py
Generate ONLY the GET /tasks/{task_id} route.
Exact specification:
- Route: GET /tasks/{task_id}
- Tags: ["tasks"]
- Response model: TaskResponse
- Behavior:
 - call storage.get_task_by_id(task_id)
 - if found, return the task
 - if missing, raise HTTPException with status_code=404 and detail="Task with id {task_id} not found"
Imports to add only if missing:
from fastapi import HTTPException
from app.models import TaskResponse
from app import store
DO NOT:
- DO NOT wrap the storage call in try/except.
- DO NOT return None for a missing task.
- DO NOT create a new FastAPI() instance.
- DO NOT modify other routes.
Output only the imports to add and the new route function in one code block
```

**Output applied:**
```python
from fastapi import HTTPException  # added to existing fastapi import line


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    task = store.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task
```

---

## 4. DELETE /tasks/{task_id}

**Prompt:**
```
Add ONE route to my existing FastAPI app.
Context files:
@app/main.py
@app/models.py
@app/storage.py
Generate ONLY the DELETE /tasks/{task_id} route.
Exact specification:
- Route: DELETE /tasks/{task_id}
- Decorator status_code: status.HTTP_204_NO_CONTENT
- Tags: ["tasks"]
- Behavior:
 - call storage.delete_task(task_id)
 - if True, return an empty 204 response
 - if False, raise HTTPException with status_code=404 and detail="Task with id {task_id} not found"
Imports to add only if missing:
from fastapi import HTTPException, status
from app import store
DO NOT:
- DO NOT return a JSON body on success.
- DO NOT call r.json() in verification for a 204 response.
- DO NOT modify other routes.
- DO NOT create a new FastAPI() instance.
Output only the imports to add and the new route function in one code block.
```

**Output applied:**
```python
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    deleted = store.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
```

---

## 5. PATCH /tasks/{task_id} — status-transition validation

**Prompt:**
```
Add status-transition validation to my existing PATCH /tasks/{task_id} route.
Context files:
@app/main.py
@app/models.py
@app/storage.py
Create a new module and modify only the existing PATCH route.
============================================================
FILE 1 - app/business_rules.py
============================================================
Use these imports:
from fastapi import HTTPException, status
from app.models import TaskStatus
Create this constant:
VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
 (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
 (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
 (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})
Create this function:
def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
 # Same -> same is invalid. Anything not in VALID_TRANSITIONS is invalid.
 if (current, new) not in VALID_TRANSITIONS:
 allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
 raise HTTPException(
 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
 detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
 )
============================================================
FILE 2 - app/main.py
============================================================
Modify the existing PATCH /tasks/{task_id} route only.
AI-Assisted Coding - Module 2 Prompt Library
Add this import if missing:
from app.business_rules import validate_status_transition
PATCH behavior:
1. If payload.status is None, skip transition validation and allow other partial updates.
2. If payload.status is provided:
 a. Get the existing task with storage.get_task_by_id(task_id).
 b. If it does not exist, raise the existing 404 behavior.
 c. Call validate_status_transition(existing.status, payload.status).
3. Then call storage.update_task(task_id, payload) and return the updated task.
DO NOT:
- DO NOT validate only whether the new status is a valid enum. The rule depends on the (current, new) pair.
- DO NOT allow ToDo -> Done, Done -> ToDo, or same -> same.
- DO NOT validate when payload.status is None.
- DO NOT inline the rules with if/elif chains; use the frozenset.
- DO NOT modify POST, GET, or DELETE routes.
Output two code blocks:
# FILE: app/business_rules.py
# PATCH ROUTE ONLY FROM app/main.py
```

**Note:** there was no pre-existing PATCH route in `app/main.py` at the time of this prompt — it was created fresh here (confirmed with the user before writing). Also added a `None` check after `store.update_task(...)` beyond the literal spec: without it, a partial update (no `status` field) against a nonexistent `task_id` would return `None` through `response_model=TaskResponse` and raise an uncontrolled 500 instead of a clean 404.

**Output applied:**
```python
# FILE: app/business_rules.py
from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    if (current, new) not in VALID_TRANSITIONS:
        allowed = sorted({f"{f.value}->{t.value}" for f, t in VALID_TRANSITIONS})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition from {current.value} to {new.value}. Allowed transitions: {allowed}",
        )
```

```python
# PATCH ROUTE ONLY FROM app/main.py
@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def patch_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    if payload.status is not None:
        existing = store.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing.status, payload.status)

    updated = store.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated
```
