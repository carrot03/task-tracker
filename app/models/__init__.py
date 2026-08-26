"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = Field("", max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = Field(None, max_length=100)

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
    created_at: datetime
    updated_at: datetime
