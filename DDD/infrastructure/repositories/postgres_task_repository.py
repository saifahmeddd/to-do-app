"""PostgreSQL persistence adapter for the application TaskRepository port."""

from datetime import datetime

from domain.entities.task import Task
from domain.value_objects.task_id import TaskId
from domain.value_objects.task_title import TaskTitle
from domain.value_objects.user_id import UserId


class PostgresTaskRepository:
    """Store tasks in PostgreSQL and enforce owner scope in each query."""

    def __init__(self, dsn: str):
        import psycopg

        self.dsn = dsn
        # Create the small task table on first use so a fresh database can run.
        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ,
                    owner_id TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS tasks_owner_id_idx ON tasks (owner_id)"
            )

    def save(self, task: Task) -> None:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                """
                INSERT INTO tasks (id, title, created_at, completed_at, owner_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    created_at = EXCLUDED.created_at,
                    completed_at = EXCLUDED.completed_at,
                    owner_id = EXCLUDED.owner_id
                """,
                (
                    task.id.value,
                    task.title.value,
                    task.created_at,
                    task.completed_at,
                    task.owner_id.value if task.owner_id else None,
                ),
            )

    def get(self, task_id: TaskId, owner_id: UserId) -> Task | None:
        row = self._fetch_one(
            "SELECT id, title, created_at, completed_at, owner_id "
            "FROM tasks WHERE id = %s AND owner_id = %s",
            (task_id.value, owner_id.value),
        )
        return _to_entity(row) if row else None

    def list_all(self, owner_id: UserId) -> list[Task]:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            rows = connection.execute(
                "SELECT id, title, created_at, completed_at, owner_id "
                "FROM tasks WHERE owner_id = %s",
                (owner_id.value,),
            ).fetchall()
        return [_to_entity(row) for row in rows]

    def delete(self, task_id: TaskId, owner_id: UserId) -> bool:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            cursor = connection.execute(
                "DELETE FROM tasks WHERE id = %s AND owner_id = %s",
                (task_id.value, owner_id.value),
            )
            return cursor.rowcount == 1

    def _fetch_one(self, query: str, parameters: tuple[str, ...]):
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            return connection.execute(query, parameters).fetchone()


def _to_entity(row: tuple) -> Task:
    task_id, title, created_at, completed_at, owner_id = row
    return Task(
        id=TaskId(task_id),
        title=TaskTitle(title),
        created_at=_as_datetime(created_at, "created_at"),
        completed_at=(
            _as_datetime(completed_at, "completed_at")
            if completed_at is not None
            else None
        ),
        owner_id=UserId(owner_id) if owner_id is not None else None,
    )


def _as_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    raise ValueError(f"PostgreSQL task field '{field_name}' must be a timestamp.")
