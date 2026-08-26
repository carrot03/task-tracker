from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Validate that a task status change is allowed.

    Same-status "transitions" are always allowed (treated as a no-op).
    Otherwise, `(current, new)` must be one of the allowed edges in
    `VALID_TRANSITIONS`: ToDo -> InProgress, InProgress -> Done, or
    Done -> InProgress.

    Args:
        current: The task's current status.
        new: The requested new status.

    Returns:
        None.

    Raises:
        HTTPException: 422 Unprocessable Entity if `current != new` and
            `(current, new)` is not in `VALID_TRANSITIONS`.
    """
    if current == new:
        return

    if (current, new) not in VALID_TRANSITIONS:
        allowed_transitions = [
            f"{src.value}->{dst.value}"
            for src, dst in VALID_TRANSITIONS
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid status transition from {current.value} to {new.value}. "
                f"Allowed transitions: {allowed_transitions}"
            ),
        )