from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from .models import Task
from .repository import InMemoryTaskRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Dependency injection: create a singleton instance
_repository_instance: TaskRepository | None = None


def get_task_repository() -> TaskRepository:
    """Get the task repository instance (singleton)."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = InMemoryTaskRepository()
    return _repository_instance


@router.get("/")
async def get_tasks(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> list[Task]:
    """Get all tasks."""
    return await repository.get_all()


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> Task | None:
    """Get a task by ID."""
    return await repository.get_by_id(task_id)


@router.post("/")
async def create_task(
    user_id: UUID,
    title: str,
    description: str,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> Task:
    """Create a new task."""
    return await repository.create(user_id, title, description)


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
    title: str | None = None,
    description: str | None = None,
) -> Task | None:
    """Update a task."""
    return await repository.update(task_id, title, description)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> dict[str, bool]:
    """Delete a task."""
    deleted = await repository.delete(task_id)
    return {"deleted": deleted}
