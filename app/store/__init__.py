"""In-memory task storage (module-level dictionary)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models import (
    TagCreate,
    TagResponse,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)

_tasks: dict[str, TaskResponse] = {}
_tags: dict[str, TagResponse] = {}


def add_tag(payload: TagCreate) -> Optional[TagResponse]:
    """Create and store a new tag.

    Args:
        payload: The tag to create.

    Returns:
        Optional[TagResponse]: The newly stored tag, or None if a tag
            with the same `name` (case-insensitive) already exists.
    """
    if any(tag.name.casefold() == payload.name.casefold() for tag in _tags.values()):
        return None

    tag = TagResponse(id=str(uuid4()), name=payload.name)
    _tags[tag.id] = tag
    return tag


def get_all_tags() -> list[TagResponse]:
    """Return every stored tag.

    Returns:
        list[TagResponse]: All tags currently in storage, in dict
            iteration (insertion) order.
    """
    return list(_tags.values())


def get_tags_by_ids(tag_ids: list[str]) -> Optional[list[TagResponse]]:
    """Resolve a list of tag ids to their stored tags.

    Args:
        tag_ids: The tag ids to resolve.

    Returns:
        Optional[list[TagResponse]]: The resolved tags in the same order
            as `tag_ids`, or None if `tag_ids` contains a duplicate or
            any id that doesn't exist in storage.
    """
    if len(tag_ids) != len(set(tag_ids)):
        return None
    tags = [_tags.get(tag_id) for tag_id in tag_ids]
    if any(tag is None for tag in tags):
        return None
    return [tag for tag in tags if tag is not None]


def add_task(payload: TaskCreate) -> TaskResponse:
    """Create and store a new task.

    Generates a new id and sets `created_at`/`updated_at` to the current
    UTC time. `payload.tag_ids` is resolved to full `TagResponse`
    objects via `get_tags_by_ids`; if resolution fails (an unknown or
    duplicate id), the task is stored with an empty tag list rather than
    raising — callers (e.g. `main.create_task`) are expected to validate
    `tag_ids` via `get_tags_by_ids` beforehand and reject the request
    themselves.

    Args:
        payload: The task to create.

    Returns:
        TaskResponse: The newly created and stored task.
    """
    task_id = str(uuid4())
    now = datetime.now(timezone.utc)
    task = TaskResponse(
        id=task_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        tags=get_tags_by_ids(payload.tag_ids) or [],
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task
    return task


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    tag_id: Optional[str] = None,
    overdue: Optional[bool] = None,
) -> list[TaskResponse]:
    """Return stored tasks, optionally filtered.

    Filters are applied cumulatively (AND'd together); any filter left
    as None is not applied. `overdue` only filters when explicitly
    True — `overdue=False` behaves the same as `overdue=None` (no
    overdue filtering is applied).

    Args:
        status: Only include tasks with this exact status.
        priority: Only include tasks with this exact priority.
        tag_id: Only include tasks that have a tag with this id.
        overdue: If True, only include tasks where
            `TaskResponse.is_overdue` is True.

    Returns:
        list[TaskResponse]: Tasks matching all provided filters.
    """
    tasks = list(_tasks.values())
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    if tag_id is not None:
        tasks = [t for t in tasks if any(tag.id == tag_id for tag in t.tags)]
    if overdue is True:
        tasks = [t for t in tasks if t.is_overdue]
    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up a single task by id.

    Args:
        task_id: The task's id.

    Returns:
        Optional[TaskResponse]: The matching task, or None if no task
            with `task_id` exists.
    """
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a stored task.

    Only fields explicitly set on `payload` are applied (via
    `model_dump(exclude_unset=True)`). A `tag_ids` update is resolved to
    full `TagResponse` objects via `get_tags_by_ids` first. If no fields
    were set, the task is returned unchanged and `updated_at` is left
    untouched.

    Args:
        task_id: The id of the task to update.
        payload: The fields to update.

    Returns:
        Optional[TaskResponse]: The updated task, or None if no task
            with `task_id` exists.
    """
    task = _tasks.get(task_id)
    if task is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if "tag_ids" in updates:
        tag_ids = updates.pop("tag_ids")
        updates["tags"] = get_tags_by_ids(tag_ids) or []
    if not updates:
        return task

    updated = task.model_copy(update=updates)
    updated.updated_at = datetime.now(timezone.utc)
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    """Remove a task from storage.

    Args:
        task_id: The id of the task to delete.

    Returns:
        bool: True if a task was deleted, False if no task with
            `task_id` existed.
    """
    return _tasks.pop(task_id, None) is not None


def _reset() -> None:
    _tasks.clear()
    _tags.clear()
