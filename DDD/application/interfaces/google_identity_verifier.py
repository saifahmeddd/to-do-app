from typing import Protocol

from application.dtos.auth_dto import GoogleIdentityDTO


class GoogleIdentityVerifier(Protocol):
    """Verify Google's ID token and return its trusted account identity."""

    def verify(self, id_token: str) -> GoogleIdentityDTO: ...
