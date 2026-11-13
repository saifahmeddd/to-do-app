"""Data-only contracts for registration and login use cases."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserDTO:
    """Email/password data entering the register-user use case."""

    email: str
    password: str


@dataclass(frozen=True)
class LoginUserDTO:
    """Email/password data entering the login-user use case."""

    email: str
    password: str


@dataclass(frozen=True)
class GoogleIdentityDTO:
    """Identity details returned only after Google's ID token is verified."""

    subject: str
    email: str


@dataclass(frozen=True)
class GitHubIdentityDTO:
    """Account identity resolved from GitHub's authenticated user API."""

    subject: str
    email: str


@dataclass(frozen=True)
class AuthSessionDTO:
    """Backend-issued access token returned after a successful login."""

    user_id: str
    email: str
    database: str
    access_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class UserCredentialDTO:
    """User data required internally to verify a login password."""

    user_id: str
    email: str
    password_hash: str | None
