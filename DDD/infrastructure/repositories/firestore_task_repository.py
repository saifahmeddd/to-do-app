"""Firestore persistence adapter for Task aggregates."""

from datetime import datetime
from typing import TYPE_CHECKING, Mapping, TypedDict

from google.cloud.firestore_v1.base_query import FieldFilter

from domain.entities.task import Task
from domain.value_objects.task_id import TaskId
from domain.value_objects.task_title import TaskTitle
from domain.value_objects.user_id import UserId

if TYPE_CHECKING:
    from google.cloud.firestore_v1.client import Client


class TaskDocument(TypedDict):
    """Complete field contract written for every Firestore task document."""

    title: str
    created_at: datetime
    completed_at: datetime | None
    submission_date: datetime | None
    reminder_sent_for: datetime | None
    submission_at: datetime | None
    scheduled_reminder_id: str | None
    owner_id: str | None


TASK_DOCUMENT_FIELDS = frozenset(TaskDocument.__required_keys__)


class FirestoreTaskRepository:
    """Implement the application repository port with Cloud Firestore."""

    def __init__(self, client: "Client", collection_name: str = "tasks"):
        self.collection = client.collection(collection_name)

    def save(self, task: Task) -> None:
        """Replace one document with the complete canonical task field set."""
        self.collection.document(task.id.value).set(_to_document(task))

    def get(self, task_id: TaskId, owner_id: UserId) -> Task | None:
        """Return a task only when it exists and belongs to the given user."""
        snapshot = self.collection.document(task_id.value).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        if data.get("owner_id") != owner_id.value:
            return None
        return _to_entity(snapshot.id, data)

    def list_all(self, owner_id: UserId) -> list[Task]:
        """Reconstruct only documents owned by the authenticated user."""
        return [
            _to_entity(snapshot.id, snapshot.to_dict() or {})
            for snapshot in self.collection.where(
                filter=FieldFilter("owner_id", "==", owner_id.value)
            ).stream()
        ]

    def delete(self, task_id: TaskId, owner_id: UserId) -> bool:
        """Delete an owned task and hide whether another user's task exists."""
        reference = self.collection.document(task_id.value)
        snapshot = reference.get()
        if not snapshot.exists:
            return False
        data = snapshot.to_dict() or {}
        if data.get("owner_id") != owner_id.value:
            return False
        reference.delete()
        return True

    def due_for_reminder(self, start: datetime, end: datetime) -> list[Task]:
        return [_to_entity(snapshot.id, snapshot.to_dict() or {}) for snapshot in self.collection.where(filter=FieldFilter("submission_date", ">=", start)).where(filter=FieldFilter("submission_date", "<", end)).stream()]

    def mark_reminded(self, task_id: TaskId, reminder_date: datetime) -> None:
        self.collection.document(task_id.value).update({"reminder_sent_for": reminder_date})


def _to_document(task: Task) -> TaskDocument:
    """Serialize every task with the same fields, preserving unavailable values."""
    document: TaskDocument = {
        "title": task.title.value,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "submission_date": task.submission_date,
        "reminder_sent_for": task.reminder_sent_for,
        "submission_at": task.submission_at,
        "scheduled_reminder_id": task.scheduled_reminder_id,
        "owner_id": task.owner_id.value if task.owner_id else None,
    }
    return document


def _to_entity(document_id: str, data: Mapping[str, object]) -> Task:
    """Rebuild a domain entity while treating absent completion as pending."""
    completed_at = data.get("completed_at")
    return Task(
        id=TaskId(document_id),
        title=TaskTitle(data.get("title")),
        created_at=_as_datetime(data.get("created_at"), "created_at"),
        completed_at=(
            _as_datetime(completed_at, "completed_at")
            if completed_at is not None
            else None
        ),
        submission_date=(
            _as_datetime(data["submission_date"], "submission_date")
            if data.get("submission_date") is not None else None
        ),
        owner_id=UserId(data["owner_id"]),
        reminder_sent_for=(
            _as_datetime(data["reminder_sent_for"], "reminder_sent_for")
            if data.get("reminder_sent_for") is not None else None
        ),
        submission_at=(
            _as_datetime(data["submission_at"], "submission_at")
            if data.get("submission_at") is not None else None
        ),
        scheduled_reminder_id=data.get("scheduled_reminder_id"),
    )


def _as_datetime(value: object, field_name: str) -> datetime:
    """Accept native Firestore timestamps and legacy ISO timestamp strings."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise ValueError(
        f"Firestore task field '{field_name}' must be a timestamp or ISO string."
    )
