"""Argon2id password hashing adapter."""

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError


class Argon2PasswordHasher:
    """Use a salted, adaptive Argon2id hash instead of storing passwords."""

    def __init__(self):
        self.hasher = PasswordHasher(
            time_cost=2,
            memory_cost=19_456,
            parallelism=1,
        )

    def hash(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self.hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError):
            return False
