"""Persistence port owned by the application layer."""

from typing import Protocol
from datetime import datetime

from domain.entities.task import Task
from domain.value_objects.task_id import TaskId
from domain.value_objects.user_id import UserId


class TaskRepository(Protocol):
    """Store and retrieve Task aggregates for application use cases."""

    def save(self, task: Task) -> None: ...

    def get(self, task_id: TaskId, owner_id: UserId) -> Task | None: ...

    def list_all(self, owner_id: UserId) -> list[Task]: ...

    def delete(self, task_id: TaskId, owner_id: UserId) -> bool: ...

    def due_for_reminder(self, start: datetime, end: datetime) -> list[Task]: ...

    def mark_reminded(self, task_id: TaskId, reminder_date: datetime) -> None: ...
