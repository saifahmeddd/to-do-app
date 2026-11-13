"""Firestore adapter for local password accounts."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore_v1.base_query import FieldFilter

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
                    "email_key": email_key,
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

    def create_google_user(
        self, email: str, email_key: str, google_subject: str, created_at: datetime
    ) -> UserCredentialDTO:
        user = UserCredentialDTO(str(uuid4()), email, None)
        try:
            self.collection.document(email_key).create(
                {
                    "user_id": user.user_id,
                    "email": email,
                    "email_key": email_key,
                    "google_subject": google_subject,
                    "password_hash": None,
                    "created_at": created_at,
                    "last_login_at": created_at,
                }
            )
        except AlreadyExists as exc:
            raise UserAlreadyExists from exc
        return user

    def get_by_google_subject(self, subject: str) -> UserCredentialDTO | None:
        matches = self.collection.where(
            filter=FieldFilter("google_subject", "==", subject)
        ).limit(1).stream()
        for snapshot in matches:
            data = snapshot.to_dict() or {}
            return UserCredentialDTO(
                user_id=data["user_id"],
                email=data["email"],
                password_hash=data.get("password_hash"),
            )
        return None

    def record_login(self, email_key: str, logged_in_at: datetime) -> None:
        reference = self.collection.document(email_key)
        snapshot = reference.get()
        if snapshot.exists:
            reference.update({"last_login_at": logged_in_at})
            return
        matches = self.collection.where("email_key", "==", email_key).limit(1).stream()
        for match in matches:
            match.reference.update({"last_login_at": logged_in_at})
            return

    def get_by_user_id(self, user_id: str) -> UserCredentialDTO | None:
        matches = self.collection.where(filter=FieldFilter("user_id", "==", user_id)).limit(1).stream()
        for match in matches:
            data = match.to_dict() or {}
            return UserCredentialDTO(user_id, data["email"], data.get("password_hash"))
        return None
