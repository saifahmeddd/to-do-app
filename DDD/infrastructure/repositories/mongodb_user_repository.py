"""MongoDB adapter for local password accounts."""

from datetime import datetime
from uuid import uuid4

from application.dtos.auth_dto import UserCredentialDTO
from application.exceptions.user_already_exists import UserAlreadyExists


class MongoUserRepository:
    """Store accounts in the selected MongoDB database's users collection."""

    def __init__(self, uri: str, database_name: str = "todo"):
        from pymongo import MongoClient

        self.client = MongoClient(uri, tz_aware=True)
        self.collection = self.client[database_name]["users"]

    def create_user(
        self,
        email: str,
        email_key: str,
        password_hash: str,
        created_at: datetime,
    ) -> UserCredentialDTO:
        from pymongo.errors import DuplicateKeyError

        user = UserCredentialDTO(str(uuid4()), email, password_hash)
        try:
            self.collection.insert_one(
                {
                    "_id": email_key,
                    "user_id": user.user_id,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "created_at": created_at,
                    "last_login_at": created_at,
                }
            )
        except DuplicateKeyError as exc:
            raise UserAlreadyExists from exc
        return user

    def get_by_email_key(self, email_key: str) -> UserCredentialDTO | None:
        document = self.collection.find_one({"_id": email_key})
        if document is None:
            return None
        return UserCredentialDTO(
            user_id=document["user_id"],
            email=document["email"],
            password_hash=document["password_hash"],
        )

    def record_login(self, email_key: str, logged_in_at: datetime) -> None:
        self.collection.update_one(
            {"_id": email_key},
            {"$set": {"last_login_at": logged_in_at}},
        )
