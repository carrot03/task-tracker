import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.business_rules import validate_status_transition
from app.models import TagCreate, TagResponse, TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app import store

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Task Tracker API",
    description=(
        "Module 1 learning project — in-memory task tracker REST API. "
        "No authentication, no persistence across restarts."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Report basic service liveness.

    Returns:
        dict[str, str]: A fixed "ok" status plus the current UTC
            timestamp in ISO 8601 format.

    Example:
        GET /health -> {"status": "ok", "timestamp": "2026-08-26T12:00:00+00:00"}
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    tag_id: str | None = None,
    overdue: bool | None = None,
) -> list[TaskResponse]:
    """List tasks, optionally filtered by status, priority, tag, or overdue state.

    Filters are combined with AND; any filter left as None is not
    applied. `overdue` only filters when explicitly True — passing
    `overdue=False` behaves the same as omitting it (no overdue
    filtering is applied; see `store.get_all_tasks`).

    Args:
        status: Only return tasks with this exact status.
        priority: Only return tasks with this exact priority.
        tag_id: Only return tasks that have a tag with this id.
        overdue: If True, only return tasks where
            `TaskResponse.is_overdue` is True.

    Returns:
        list[TaskResponse]: Tasks matching all provided filters.

    Example:
        GET /tasks?status=ToDo&priority=High
    """
    return store.get_all_tasks(status=status, priority=priority, tag_id=tag_id, overdue=overdue)


@app.get("/tags", response_model=list[TagResponse], tags=["tags"])
def list_tags() -> list[TagResponse]:
    """List all tags.

    Returns:
        list[TagResponse]: Every tag currently in storage.
    """
    return store.get_all_tags()


@app.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED, tags=["tags"])
def create_tag(payload: TagCreate) -> TagResponse:
    """Create a new tag.

    Args:
        payload: The tag to create. `name` is validated by `TagCreate`
            (must be non-blank after stripping, and at most 50
            characters).

    Returns:
        TagResponse: The newly created tag, with a generated `id`.

    Raises:
        HTTPException: 409 Conflict if a tag with the same `name`
            already exists (case-insensitive comparison).
    """
    tag = store.add_tag(payload)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Tag with name {payload.name!r} already exists")
    return tag


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a new task.

    Args:
        payload: The task to create. `tag_ids` must reference existing,
            non-duplicated tags.

    Returns:
        TaskResponse: The newly created task, with a generated `id`,
            `created_at`/`updated_at` timestamps, and `tag_ids` expanded
            into full `TagResponse` objects.

    Raises:
        HTTPException: 422 Unprocessable Entity if `tag_ids` contains an
            id that doesn't exist, or contains a duplicate id.
    """
    if store.get_tags_by_ids(payload.tag_ids) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more tag_ids are invalid or duplicated")
    return store.add_task(payload)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    """Retrieve a single task by id.

    Args:
        task_id: The task's id.

    Returns:
        TaskResponse: The matching task.

    Raises:
        HTTPException: 404 Not Found if no task with `task_id` exists.
    """
    task = store.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    """Delete a task by id.

    Args:
        task_id: The task's id.

    Returns:
        None: Responds with 204 No Content on success.

    Raises:
        HTTPException: 404 Not Found if no task with `task_id` exists.
    """
    deleted = store.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    tags=["tasks"],
)
def patch_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Only fields explicitly set on `payload` are applied; omitted fields
    are left unchanged. If `payload.status` is set, it is validated
    against the allowed transition graph (see
    `validate_status_transition`) before being applied. If
    `payload.tag_ids` is set, it must reference existing, non-duplicated
    tags.

    Args:
        task_id: The task's id.
        payload: The fields to update (see `TaskUpdate`).

    Returns:
        TaskResponse: The updated task.

    Raises:
        HTTPException: 404 Not Found if no task with `task_id` exists.
        HTTPException: 422 Unprocessable Entity if `payload.status` is
            not a valid transition from the task's current status, or if
            `payload.tag_ids` contains an id that doesn't exist or a
            duplicate id.
    """
    if payload.status is not None:
        existing = store.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing.status, payload.status)

    if payload.tag_ids is not None and store.get_tags_by_ids(payload.tag_ids) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more tag_ids are invalid or duplicated")

    updated = store.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated


# Mount this last so the API routes above always take precedence.  Serving the
# board from the same origin removes the need for a separate frontend server.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
