"""Data-only contracts used at the application boundary."""

from dataclasses import dataclass

from domain.entities.task import Task


@dataclass(frozen=True)
class CreateTaskDTO:
    """Input required by the create-task use case."""

    title: str
    submission_date: str | None = None


@dataclass(frozen=True)
class UpdateTaskDTO:
    """Editable data accepted by the update-task use case."""

    title: str


@dataclass(frozen=True)
class TaskDTO:
    """Primitive task data returned by application use cases."""

    id: str
    title: str
    created_at: str
    completed_at: str | None
    submission_date: str | None

    @classmethod
    def from_entity(cls, task: Task) -> "TaskDTO":
        """Map a domain entity without exposing value objects to presentation."""
        return cls(
            id=task.id.value,
            title=task.title.value,
            created_at=task.created_at.isoformat(),
            completed_at=(
                task.completed_at.isoformat() if task.completed_at else None
            ),
            submission_date=(task.submission_date.date().isoformat() if task.submission_date else None),
        )
