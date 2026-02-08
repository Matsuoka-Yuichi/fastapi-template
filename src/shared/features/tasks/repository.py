from abc import ABC, abstractmethod
from uuid import UUID

from .models import Task


class TaskRepository(ABC):
    """Abstract interface for task repository."""

    @abstractmethod
    async def create(self, user_id: UUID, title: str, description: str) -> Task:
        """Create a new task."""
        ...

    @abstractmethod
    async def get_by_id(self, task_id: int) -> Task | None:
        """Get a task by its ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[Task]:
        """Get all tasks."""
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Task]:
        """Get all tasks for a specific user."""
        ...

    @abstractmethod
    async def update(
        self, task_id: int, title: str | None = None, description: str | None = None
    ) -> Task | None:
        """Update a task by its ID."""
        ...

    @abstractmethod
    async def delete(self, task_id: int) -> bool:
        """Delete a task by its ID. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    async def delete_all(self) -> None:
        """Delete all tasks."""
        ...


class InMemoryTaskRepository(TaskRepository):
    """In-memory implementation of TaskRepository."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._next_id: int = 1

    async def create(self, user_id: UUID, title: str, description: str) -> Task:
        """Create a new task."""
        task = Task(
            id=self._next_id,
            user_id=user_id,
            title=title,
            description=description,
        )
        self._tasks.append(task)
        self._next_id += 1
        return task

    async def get_by_id(self, task_id: int) -> Task | None:
        """Get a task by its ID."""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    async def get_all(self) -> list[Task]:
        """Get all tasks."""
        return self._tasks.copy()

    async def get_by_user_id(self, user_id: UUID) -> list[Task]:
        """Get all tasks for a specific user."""
        return [task for task in self._tasks if task.user_id == user_id]

    async def update(
        self, task_id: int, title: str | None = None, description: str | None = None
    ) -> Task | None:
        """Update a task by its ID."""
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description

        return task

    async def delete(self, task_id: int) -> bool:
        """Delete a task by its ID. Returns True if deleted, False if not found."""
        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                self._tasks.pop(i)
                return True
        return False

    async def delete_all(self) -> None:
        """Delete all tasks."""
        self._tasks.clear()
        self._next_id = 1
