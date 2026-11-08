"""Application port for issuing signed access tokens."""

from typing import Protocol


class TokenIssuer(Protocol):
    @property
    def database(self) -> str: ...

    @property
    def expires_in(self) -> int: ...

    def issue(self, user_id: str, email: str) -> str: ...
