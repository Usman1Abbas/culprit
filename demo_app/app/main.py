"""Minimal FastAPI 'patient' service that wires the three buggy modules.

This is intentionally small: the star of the show is the triage engine, not this app.
Run standalone with:  uvicorn demo_app.app.main:app --reload
"""
from fastapi import FastAPI
from pydantic import BaseModel

from .pagination import paginate
from .parsing import parse_user
from .tasks import process_task

app = FastAPI(title="Patient Service (has planted bugs)")

_TASKS = [{"id": i, "title": f"task-{i}"} for i in range(1, 101)]


@app.get("/tasks")
def list_tasks(page: int = 1, per_page: int = 10):
    return {"page": page, "items": paginate(_TASKS, page, per_page)}


class UserIn(BaseModel):
    name: str
    email: str | None = None


@app.post("/users")
def create_user(payload: UserIn):
    return parse_user(payload.model_dump())


@app.post("/tasks/{task_id}/process")
async def process(task_id: int):
    return await process_task({"id": task_id, "title": f"task-{task_id}"})
