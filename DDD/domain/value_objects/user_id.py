"""Validated authenticated user identity used to scope task ownership."""

from dataclasses import dataclass

from domain.exceptions.task_errors import InvalidUserId


@dataclass(frozen=True)
class UserId:
    """Immutable non-empty ID from the selected database's user collection."""

    value: str

    def __post_init__(self) -> None:
        """Reject missing or malformed identity values before domain use."""
        if not isinstance(self.value, str):
            raise InvalidUserId("User ID must be text.")
        normalized = self.value.strip()
        if not 1 <= len(normalized) <= 128:
            raise InvalidUserId("User ID must contain 1–128 characters.")
        object.__setattr__(self, "value", normalized)
