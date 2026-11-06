"""Firestore adapter for local password accounts."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from google.api_core.exceptions import AlreadyExists

from application.dtos.auth_dto import UserCredentialDTO
from application.exceptions.user_already_exists import UserAlreadyExists

if TYPE_CHECKING:
    from google.cloud.firestore_v1.client import Client


class FirestoreUserRepository:
    """Store accounts in the selected Firestore users collection."""

    def __init__(self, client: "Client", collection_name: str = "users"):
        self.collection = client.collection(collection_name)

    def create_user(
        self,
        email: str,
        email_key: str,
        password_hash: str,
        created_at: datetime,
    ) -> UserCredentialDTO:
        user = UserCredentialDTO(str(uuid4()), email, password_hash)
        try:
            self.collection.document(email_key).create(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "created_at": created_at,
                    "last_login_at": created_at,
                }
            )
        except AlreadyExists as exc:
            raise UserAlreadyExists from exc
        return user

    def get_by_email_key(self, email_key: str) -> UserCredentialDTO | None:
        snapshot = self.collection.document(email_key).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        return UserCredentialDTO(
            user_id=data["user_id"],
            email=data["email"],
            password_hash=data["password_hash"],
        )

    def record_login(self, email_key: str, logged_in_at: datetime) -> None:
        self.collection.document(email_key).update({"last_login_at": logged_in_at})
