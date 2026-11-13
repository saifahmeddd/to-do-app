"""MongoDB persistence adapter for the application TaskRepository port."""

from datetime import datetime
from typing import Mapping

from domain.entities.task import Task
from domain.value_objects.task_id import TaskId
from domain.value_objects.task_title import TaskTitle
from domain.value_objects.user_id import UserId


class MongoTaskRepository:
    """Store tasks as MongoDB documents while enforcing owner-scoped access."""

    def __init__(self, uri: str, database_name: str = "todo"):
        from pymongo import MongoClient

        self.client = MongoClient(uri, tz_aware=True)
        self.collection = self.client[database_name]["tasks"]
        self.collection.create_index("owner_id")

    def save(self, task: Task) -> None:
        self.collection.replace_one(
            {"_id": task.id.value}, _to_document(task), upsert=True
        )

    def get(self, task_id: TaskId, owner_id: UserId) -> Task | None:
        document = self.collection.find_one(
            {"_id": task_id.value, "owner_id": owner_id.value}
        )
        return _to_entity(document) if document else None

    def list_all(self, owner_id: UserId) -> list[Task]:
        return [
            _to_entity(document)
            for document in self.collection.find({"owner_id": owner_id.value})
        ]

    def delete(self, task_id: TaskId, owner_id: UserId) -> bool:
        result = self.collection.delete_one(
            {"_id": task_id.value, "owner_id": owner_id.value}
        )
        return result.deleted_count == 1

    def due_for_reminder(self, start: datetime, end: datetime) -> list[Task]:
        return [_to_entity(row) for row in self.collection.find({"submission_date": {"$gte": start, "$lt": end}, "completed_at": None})]

    def mark_reminded(self, task_id: TaskId, reminder_date: datetime) -> None:
        self.collection.update_one({"_id": task_id.value}, {"$set": {"reminder_sent_for": reminder_date}})


def _to_document(task: Task) -> dict:
    return {
        "_id": task.id.value,
        "title": task.title.value,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "submission_date": task.submission_date,
        "reminder_sent_for": task.reminder_sent_for,
        "owner_id": task.owner_id.value if task.owner_id else None,
    }


def _to_entity(document: Mapping[str, object]) -> Task:
    completed_at = document.get("completed_at")
    owner_id = document.get("owner_id")
    return Task(
        id=TaskId(document["_id"]),
        title=TaskTitle(document.get("title")),
        created_at=_as_datetime(document.get("created_at"), "created_at"),
        completed_at=(
            _as_datetime(completed_at, "completed_at")
            if completed_at is not None
            else None
        ),
        submission_date=(
            _as_datetime(document["submission_date"], "submission_date")
            if document.get("submission_date") is not None else None
        ),
        owner_id=UserId(owner_id) if owner_id is not None else None,
        reminder_sent_for=(
            _as_datetime(document["reminder_sent_for"], "reminder_sent_for")
            if document.get("reminder_sent_for") is not None else None
        ),
    )


def _as_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    raise ValueError(f"MongoDB task field '{field_name}' must be a timestamp.")
