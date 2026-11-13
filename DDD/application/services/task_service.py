"""Application service implementing authenticated task CRUD use cases."""

from application.dtos.task_dto import CreateTaskDTO, TaskDTO, UpdateTaskDTO
from datetime import date, datetime, time, timezone
from application.exceptions.task_not_found import TaskNotFound
from application.interfaces.runtime import Clock, EventPublisher, IdGenerator
from application.interfaces.task_repository import TaskRepository
from domain.domain_services.task_ordering import TaskOrdering
from domain.entities.task import Task
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
    ):
        self.repository = repository
        self.clock = clock
        self.ids = ids
        self.events = events
        self.ordering = ordering

    def create(self, command: CreateTaskDTO, owner_id: UserId) -> TaskDTO:
        """Create and persist a valid task owned by the authenticated user."""
        task = Task(
            id=self.ids.new_id(),
            title=TaskTitle(command.title),
            created_at=self.clock.now(),
            submission_date=(datetime.combine(date.fromisoformat(command.submission_date), time.min, timezone.utc) if command.submission_date else None),
            owner_id=owner_id,
        )
        self.repository.save(task)
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
        task.rename(TaskTitle(command.title))
        self.repository.save(task)
        return TaskDTO.from_entity(task)

    def complete(self, raw_id: str, owner_id: UserId) -> TaskDTO:
        """Complete an owned task and publish its event exactly once."""
        task = self._get_owned_task(raw_id, owner_id)
        event = task.complete(self.clock.now())
        if event is not None:
            self.repository.save(task)
            self.events.publish(event)
        return TaskDTO.from_entity(task)

    def delete(self, raw_id: str, owner_id: UserId) -> None:
        """Delete one owned task or report the same not-found result as reads."""
        task_id = TaskId(raw_id)
        if not self.repository.delete(task_id, owner_id):
            raise TaskNotFound("Task not found.")

    def _get_owned_task(self, raw_id: str, owner_id: UserId) -> Task:
        """Centralize owner-scoped lookup and avoid resource-existence leaks."""
        task = self.repository.get(TaskId(raw_id), owner_id)
        if task is None:
            raise TaskNotFound("Task not found.")
        return task

