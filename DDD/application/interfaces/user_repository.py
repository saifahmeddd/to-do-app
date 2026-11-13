"""Application port for users stored in the selected database."""

from datetime import datetime
from typing import Protocol

from application.dtos.auth_dto import UserCredentialDTO


class UserRepository(Protocol):
    """Create and look up credentials without exposing database details."""

    def create_user(
        self,
        email: str,
        email_key: str,
        password_hash: str,
        created_at: datetime,
    ) -> UserCredentialDTO: ...

    def get_by_email_key(self, email_key: str) -> UserCredentialDTO | None: ...

    def create_google_user(
        self, email: str, email_key: str, google_subject: str, created_at: datetime
    ) -> UserCredentialDTO: ...

    def get_by_google_subject(self, subject: str) -> UserCredentialDTO | None: ...

    def get_by_user_id(self, user_id: str) -> UserCredentialDTO | None: ...

    def record_login(self, email_key: str, logged_in_at: datetime) -> None: ...
