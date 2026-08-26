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
    return store.get_all_tasks(status=status, priority=priority, tag_id=tag_id, overdue=overdue)


@app.get("/tags", response_model=list[TagResponse], tags=["tags"])
def list_tags() -> list[TagResponse]:
    return store.get_all_tags()


@app.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED, tags=["tags"])
def create_tag(payload: TagCreate) -> TagResponse:
    tag = store.add_tag(payload)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Tag with name {payload.name!r} already exists")
    return tag


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    if store.get_tags_by_ids(payload.tag_ids) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more tag_ids are invalid or duplicated")
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

    if payload.tag_ids is not None and store.get_tags_by_ids(payload.tag_ids) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more tag_ids are invalid or duplicated")

    updated = store.update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated


# Mount this last so the API routes above always take precedence.  Serving the
# board from the same origin removes the need for a separate frontend server.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
