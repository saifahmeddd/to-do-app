"""Environment-backed settings used only by the outer application boundary."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / ".secrets" / "firebase-service-account.json"


@dataclass(frozen=True)
class Settings:
    """Immutable database, JWT, and HTTP configuration for one process."""

    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    task_database: str = "firestore"
    task_collection: str = "tasks"
    user_collection: str = "users"
    mongodb_uri: str | None = None
    mongodb_database: str = "todo"
    postgres_dsn: str | None = None
    jwt_secret: str = ""
    jwt_expires_minutes: int = 60
    google_client_id: str | None = None
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load local .env settings without overriding exported variables."""
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        configured_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        task_database = os.getenv("TASK_DATABASE", "firestore").strip().lower()
        if task_database not in {"firestore", "mongodb", "postgres"}:
            raise ValueError(
                "TASK_DATABASE must be 'firestore', 'mongodb', or 'postgres'."
            )
        local_credentials = (
            str(DEFAULT_CREDENTIALS_PATH) if DEFAULT_CREDENTIALS_PATH.is_file() else None
        )
        return cls(
            firebase_project_id=os.getenv("FIREBASE_PROJECT_ID") or None,
            firebase_credentials_path=configured_credentials or local_credentials,
            task_database=task_database,
            task_collection=os.getenv("FIREBASE_TASK_COLLECTION", "tasks"),
            user_collection=os.getenv("FIREBASE_USER_COLLECTION", "users"),
            mongodb_uri=os.getenv("MONGODB_URI") or None,
            mongodb_database=os.getenv("MONGODB_DATABASE", "todo"),
            postgres_dsn=os.getenv("POSTGRES_DSN") or None,
            jwt_secret=os.getenv("JWT_SECRET", ""),
            jwt_expires_minutes=int(os.getenv("JWT_EXPIRES_MINUTES", "60")),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID") or None,
            host=os.getenv("TODO_HOST", "127.0.0.1"),
            port=int(os.getenv("TODO_PORT", "8000")),
        )
