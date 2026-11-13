"""Application service implementing authenticated task CRUD use cases."""

from datetime import date, datetime, time, timedelta, timezone
import logging

from application.dtos.task_dto import CreateTaskDTO, TaskDTO, UpdateTaskDTO
from application.exceptions.task_not_found import TaskNotFound
from application.exceptions.reminder_scheduling_unavailable import ReminderSchedulingUnavailable
from application.interfaces.runtime import Clock, EventPublisher, IdGenerator
from application.interfaces.task_repository import TaskRepository
from application.interfaces.task_reminder_scheduler import TaskReminderScheduler
from application.interfaces.user_repository import UserRepository
from domain.domain_services.task_ordering import TaskOrdering
from domain.entities.task import Task
from domain.exceptions.task_errors import InvalidTask
from domain.value_objects.task_id import TaskId
from domain.value_objects.task_title import TaskTitle
from domain.value_objects.user_id import UserId


class TaskService:
    """Coordinate owner-scoped use cases, ports, and domain behavior."""

    def __init__(
        self,
        repository: TaskRepository,
        clock: Clock,
        ids: IdGenerator,
        events: EventPublisher,
        ordering: TaskOrdering,
        users: UserRepository | None = None,
        reminder_scheduler: TaskReminderScheduler | None = None,
    ):
        self.repository = repository
        self.clock = clock
        self.ids = ids
        self.events = events
        self.ordering = ordering
        self.users = users
        self.reminder_scheduler = reminder_scheduler

    def create(self, command: CreateTaskDTO, owner_id: UserId) -> TaskDTO:
        """Create and persist a valid task owned by the authenticated user."""
        submission_at = (
            _parse_submission_at(command.submission_at)
            if command.submission_at
            else None
        )
        if submission_at is not None:
            self._validate_scheduled_time(submission_at)
        task = Task(
            id=self.ids.new_id(),
            title=TaskTitle(command.title),
            created_at=self.clock.now(),
            submission_date=(
                datetime.combine(
                    date.fromisoformat(command.submission_date), time.min, timezone.utc
                )
                if command.submission_date
                else None
            ),
            submission_at=submission_at,
            owner_id=owner_id,
        )
        if submission_at is not None:
            task.scheduled_reminder_id = self._schedule(task, submission_at)
        try:
            self.repository.save(task)
        except Exception:
            self._cancel(task.scheduled_reminder_id)
            raise
        return TaskDTO.from_entity(task)

    def list_tasks(self, owner_id: UserId) -> list[TaskDTO]:
        """Return only the authenticated user's canonically ordered tasks."""
        owned_tasks = self.repository.list_all(owner_id)
        ordered_tasks = self.ordering.order(owned_tasks)
        return [TaskDTO.from_entity(task) for task in ordered_tasks]

    def get(self, raw_id: str, owner_id: UserId) -> TaskDTO:
        """Return one owned task without revealing another user's task."""
        return TaskDTO.from_entity(self._get_owned_task(raw_id, owner_id))

    def update(
        self,
        raw_id: str,
        command: UpdateTaskDTO,
        owner_id: UserId,
    ) -> TaskDTO:
        """Rename an owned task and persist the validated domain state."""
        task = self._get_owned_task(raw_id, owner_id)
        previous_reminder_id = task.scheduled_reminder_id
        task.rename(TaskTitle(command.title))
        if command.submission_at_provided:
            task.submission_at = (
                _parse_submission_at(command.submission_at)
                if command.submission_at
                else None
            )
        if task.submission_at is not None:
            self._validate_scheduled_time(task.submission_at)
        task.scheduled_reminder_id = (
            self._schedule(task, task.submission_at) if task.submission_at else None
        )
        try:
            self.repository.save(task)
        except Exception:
            self._cancel(task.scheduled_reminder_id)
            raise
        self._cancel(previous_reminder_id)
        return TaskDTO.from_entity(task)

    def complete(self, raw_id: str, owner_id: UserId) -> TaskDTO:
        """Complete an owned task and publish its event exactly once."""
        task = self._get_owned_task(raw_id, owner_id)
        event = task.complete(self.clock.now())
        if event is not None:
            previous_reminder_id = task.scheduled_reminder_id
            task.scheduled_reminder_id = None
            self.repository.save(task)
            self._cancel(previous_reminder_id)
            self.events.publish(event)
        return TaskDTO.from_entity(task)

    def delete(self, raw_id: str, owner_id: UserId) -> None:
        """Delete one owned task or report the same not-found result as reads."""
        task_id = TaskId(raw_id)
        task = self.repository.get(task_id, owner_id)
        if task is None or not self.repository.delete(task_id, owner_id):
            raise TaskNotFound("Task not found.")
        self._cancel(task.scheduled_reminder_id)

    def _get_owned_task(self, raw_id: str, owner_id: UserId) -> Task:
        """Centralize owner-scoped lookup and avoid resource-existence leaks."""
        task = self.repository.get(TaskId(raw_id), owner_id)
        if task is None:
            raise TaskNotFound("Task not found.")
        return task

    def _schedule(self, task: Task, due_at: datetime) -> str:
        if self.reminder_scheduler is None or self.users is None:
            raise ReminderSchedulingUnavailable(
                "Timed email reminders are not configured. Set RESEND_API_KEY and a reminder sender."
            )
        user = self.users.get_by_user_id(task.owner_id.value)
        if user is None:
            raise ReminderSchedulingUnavailable(
                "Could not find the task owner email for its reminder."
            )
        return self.reminder_scheduler.schedule_task_due_reminder(
            user.email, task.title.value, due_at
        )

    def _cancel(self, reminder_id: str | None) -> None:
        if reminder_id and self.reminder_scheduler:
            try:
                self.reminder_scheduler.cancel_task_due_reminder(reminder_id)
            except Exception:
                logging.getLogger(__name__).exception(
                    "Could not cancel scheduled reminder %s", reminder_id
                )

    def _validate_scheduled_time(self, due_at: datetime) -> None:
        now = self.clock.now()
        if due_at <= now:
            raise InvalidTask("Due date and time must be in the future.")
        if due_at > now + timedelta(days=30):
            raise InvalidTask("Resend can schedule task reminders up to 30 days ahead.")


def _parse_submission_at(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Due date and time must include a timezone.")
    return parsed.astimezone(timezone.utc)

