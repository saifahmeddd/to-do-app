"""Application port for scheduling and canceling exact-time task emails."""

from datetime import datetime
from typing import Protocol


class TaskReminderScheduler(Protocol):
    def schedule_task_due_reminder(
        self, recipient: str, title: str, due_at: datetime
    ) -> str: ...

    def cancel_task_due_reminder(self, reminder_id: str) -> None: ...
