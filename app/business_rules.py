from fastapi import HTTPException, status

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset({
    (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
    (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
    (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
})


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
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