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
    if any(tag.name.casefold() == payload.name.casefold() for tag in _tags.values()):
        return None

    tag = TagResponse(id=str(uuid4()), name=payload.name)
    _tags[tag.id] = tag
    return tag


def get_all_tags() -> list[TagResponse]:
    return list(_tags.values())


def get_tags_by_ids(tag_ids: list[str]) -> Optional[list[TagResponse]]:
    if len(tag_ids) != len(set(tag_ids)):
        return None
    tags = [_tags.get(tag_id) for tag_id in tag_ids]
    if any(tag is None for tag in tags):
        return None
    return [tag for tag in tags if tag is not None]


def add_task(payload: TaskCreate) -> TaskResponse:
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
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
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
    return _tasks.pop(task_id, None) is not None


def _reset() -> None:
    _tasks.clear()
    _tags.clear()
