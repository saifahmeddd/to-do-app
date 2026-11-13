"""Application port for exchanging a GitHub authorization code for identity."""

from typing import Protocol

from application.dtos.auth_dto import GitHubIdentityDTO


class GitHubIdentityVerifier(Protocol):
    def verify(self, authorization_code: str) -> GitHubIdentityDTO: ...
