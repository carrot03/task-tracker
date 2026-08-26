import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.business_rules import validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app import store

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

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
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[TaskResponse]:
    return store.get_all_tasks(status=status, priority=priority)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return store.add_task(payload)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    task = store.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
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
    if payload.status is not None:
        existing = store.get_task_by_id(task_id)
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing.status, payload.status)

    updated = store.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated