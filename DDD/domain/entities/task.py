"""Task aggregate and the business behavior that changes its state."""

from dataclasses import dataclass
from datetime import datetime

from domain.domain_events.task_completed import TaskCompleted
from domain.value_objects.task_id import TaskId
from domain.value_objects.task_title import TaskTitle
from domain.value_objects.user_id import UserId


@dataclass
class Task:
    """Aggregate root: completion behavior and state belong together."""

    id: TaskId
    title: TaskTitle
    created_at: datetime
    submission_date: datetime | None = None
    completed_at: datetime | None = None
    owner_id: UserId | None = None
    reminder_sent_for: datetime | None = None
    submission_at: datetime | None = None
    scheduled_reminder_id: str | None = None

    def complete(self, now: datetime) -> TaskCompleted | None:
        """Complete once and return the event created by the state change."""
        if self.completed_at is not None:
            return None
        self.completed_at = now
        return TaskCompleted(self.id, now)

    def rename(self, title: TaskTitle) -> None:
        """Replace the title with another already-validated value object."""
        self.title = title
