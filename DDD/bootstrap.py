"""Composition root that connects concrete adapters to application ports."""

from typing import TYPE_CHECKING

from application.interfaces.task_repository import TaskRepository
from application.interfaces.user_repository import UserRepository
from application.services.auth_service import AuthService
from application.services.task_service import TaskService
from domain.domain_services.task_ordering import TaskOrdering
from infrastructure.config.settings import Settings
from infrastructure.authentication.argon2_password_hasher import Argon2PasswordHasher
from infrastructure.authentication.jwt_token_service import JwtTokenService
from infrastructure.firebase.client import create_firestore_client
from infrastructure.messaging.log_event_publisher import LogEventPublisher
from infrastructure.providers.system_runtime import SystemClock, UUIDGenerator
from infrastructure.repositories.firestore_task_repository import FirestoreTaskRepository
from infrastructure.repositories.firestore_user_repository import FirestoreUserRepository
from infrastructure.repositories.mongodb_task_repository import MongoTaskRepository
from infrastructure.repositories.mongodb_user_repository import MongoUserRepository
from infrastructure.repositories.postgres_task_repository import PostgresTaskRepository
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from presentation.controllers.auth_controller import AuthController
from presentation.controllers.task_controller import TaskController
from presentation.routes.api_routes import ApiRoutes
from presentation.routes.auth_routes import AuthRoutes
from presentation.routes.task_routes import TaskRoutes

if TYPE_CHECKING:
    from google.cloud.firestore_v1.client import Client


def build_routes(
    settings: Settings,
    firestore_client: "Client | None" = None,
    jwt_service: JwtTokenService | None = None,
) -> ApiRoutes:
    """Build the fully wired request handler used by the HTTP server."""
    if settings.task_database == "firestore" and firestore_client is None:
        firestore_client = create_firestore_client(
            settings.firebase_project_id,
            settings.firebase_credentials_path,
        )
    repository = build_task_repository(settings, firestore_client)
    service = TaskService(
        repository,
        SystemClock(),
        UUIDGenerator(),
        LogEventPublisher(),
        TaskOrdering(),
    )
    task_routes = TaskRoutes(TaskController(service))

    user_repository = build_user_repository(settings, firestore_client)
    token_service = jwt_service or JwtTokenService(
        settings.jwt_secret,
        settings.task_database,
        settings.jwt_expires_minutes,
    )
    auth_service = AuthService(
        user_repository,
        Argon2PasswordHasher(),
        token_service,
        SystemClock(),
    )
    auth_routes = AuthRoutes(AuthController(auth_service))
    return ApiRoutes(auth_routes, task_routes)


def build_user_repository(
    settings: Settings,
    firestore_client: "Client | None" = None,
) -> UserRepository:
    """Use the same database choice for user accounts and task storage."""
    if settings.task_database == "mongodb":
        if not settings.mongodb_uri:
            raise ValueError("MONGODB_URI is required when TASK_DATABASE=mongodb.")
        return MongoUserRepository(settings.mongodb_uri, settings.mongodb_database)

    if settings.task_database == "postgres":
        if not settings.postgres_dsn:
            raise ValueError("POSTGRES_DSN is required when TASK_DATABASE=postgres.")
        return PostgresUserRepository(settings.postgres_dsn)

    if settings.task_database != "firestore":
        raise ValueError("TASK_DATABASE must be 'firestore', 'mongodb', or 'postgres'.")

    client = firestore_client or create_firestore_client(
        settings.firebase_project_id,
        settings.firebase_credentials_path,
    )
    return FirestoreUserRepository(client, settings.user_collection)


def build_task_repository(
    settings: Settings,
    firestore_client: "Client | None" = None,
) -> TaskRepository:
    """Choose one database adapter at startup; task use cases stay unchanged."""
    if settings.task_database == "mongodb":
        if not settings.mongodb_uri:
            raise ValueError("MONGODB_URI is required when TASK_DATABASE=mongodb.")
        return MongoTaskRepository(settings.mongodb_uri, settings.mongodb_database)

    if settings.task_database == "postgres":
        if not settings.postgres_dsn:
            raise ValueError("POSTGRES_DSN is required when TASK_DATABASE=postgres.")
        return PostgresTaskRepository(settings.postgres_dsn)

    if settings.task_database != "firestore":
        raise ValueError("TASK_DATABASE must be 'firestore', 'mongodb', or 'postgres'.")

    client = firestore_client or create_firestore_client(
        settings.firebase_project_id,
        settings.firebase_credentials_path,
    )
    return FirestoreTaskRepository(client, settings.task_collection)
