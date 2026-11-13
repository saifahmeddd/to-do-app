"""HTTP-facing controller that adapts requests to application use cases."""

from application.dtos.task_dto import CreateTaskDTO, UpdateTaskDTO
from application.interfaces.authentication import AuthenticatedUser
from application.services.task_service import TaskService
from presentation.validators.task_validator import validate_create, validate_update, validate_submission_date
from presentation.views.task_view import deleted_view, task_view, tasks_view


class TaskController:
    """Translate task actions between presentation and application objects."""

    def __init__(self, service: TaskService):
        self.service = service

    def create(self, body: object, user: AuthenticatedUser) -> tuple[int, dict]:
        """Validate create input and return the created task representation."""
        title = validate_create(body)
        command = CreateTaskDTO(title, validate_submission_date(body))
        created_task = self.service.create(command, user.id)
        return 201, task_view(created_task)

    def list_tasks(self, user: AuthenticatedUser) -> tuple[int, dict]:
        """Return the JSON-ready representation of every ordered task."""
        return 200, tasks_view(self.service.list_tasks(user.id))

    def get(self, task_id: str, user: AuthenticatedUser) -> tuple[int, dict]:
        """Return one task selected by its URL identifier."""
        return 200, task_view(self.service.get(task_id, user.id))

    def update(
        self, task_id: str, body: object, user: AuthenticatedUser
    ) -> tuple[int, dict]:
        """Validate and rename one task selected by its URL identifier."""
        title = validate_update(body)
        command = UpdateTaskDTO(title)
        updated_task = self.service.update(task_id, command, user.id)
        return 200, task_view(updated_task)

    def complete(self, task_id: str, user: AuthenticatedUser) -> tuple[int, dict]:
        """Complete one task selected by its URL identifier."""
        return 200, task_view(self.service.complete(task_id, user.id))

    def delete(self, task_id: str, user: AuthenticatedUser) -> tuple[int, dict]:
        """Delete one task selected by its URL identifier."""
        self.service.delete(task_id, user.id)
        return 200, deleted_view(task_id)
