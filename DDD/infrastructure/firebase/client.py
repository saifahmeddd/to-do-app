"""Firebase Admin SDK initialization for the infrastructure layer."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud.firestore_v1.client import Client


def create_firestore_client(
    project_id: str | None = None,
    credentials_path: str | None = None,
) -> "Client":
    """Initialize Firebase once and return its Cloud Firestore client.

    Production can use Application Default Credentials. Local development may
    supply an explicit service-account path from the outer configuration layer.
    """
    from firebase_admin import firestore

    app = initialize_firebase_app(project_id, credentials_path)
    return firestore.client(app=app)


def initialize_firebase_app(
    project_id: str | None = None,
    credentials_path: str | None = None,
):
    """Initialize Firebase Admin even when Firestore is not the task database."""
    import firebase_admin
    from firebase_admin import credentials

    # Reuse the process-wide default app because Firebase rejects duplicate
    # initialization with the same name.
    try:
        app = firebase_admin.get_app()
    except ValueError:
        credential = (
            credentials.Certificate(credentials_path) if credentials_path else None
        )
        options = {"projectId": project_id} if project_id else None
        app = firebase_admin.initialize_app(credential, options=options)
    return app
