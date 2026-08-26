"""Pydantic models for request/response validation."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            for member in cls:
                if member.value.lower() == normalized:
                    return member
        return None


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            for member in cls:
                if member.value.lower() == normalized:
                    return member
        return None


def _validate_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("title must not be blank")
    if len(value) > 200:
        raise ValueError("title must be at most 200 characters")
    return value


def _normalize_assignee(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _validate_tag_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("name must not be blank")
    if len(value) > 50:
        raise ValueError("name must be at most 50 characters")
    return value


def _validate_comment_author(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("author must not be blank")
    if len(value) > 100:
        raise ValueError("author must be at most 100 characters")
    return value


def _validate_comment_body(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("body must not be blank")
    if len(value) > 2000:
        raise ValueError("body must be at most 2000 characters")
    return value


class TagCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_tag_name(v)


class TagResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    author: str
    body: str

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        return _validate_comment_author(v)

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        return _validate_comment_body(v)


class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    task_id: str
    author: str
    body: str
    created_at: datetime


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = Field("", max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = Field(None, max_length=100)
    tag_ids: list[str] = Field(default_factory=list)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return _validate_title(v)

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_assignee(v)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = Field(None, max_length=100)
    tag_ids: Optional[list[str]] = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_title(v)

    @field_validator("assignee")
    @classmethod
    def validate_assignee(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_assignee(v)


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    tags: list[TagResponse]
    due_date: date | None
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=bool)
    @property
    def is_overdue(self) -> bool:
        """Whether this task is overdue.

        Computed at read time from `due_date`/`status` rather than
        stored, so it never goes stale.

        Returns:
            bool: True if `due_date` is set, is strictly before today,
                and `status` is not Done. False otherwise.
        """
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and self.status != TaskStatus.DONE
        )
