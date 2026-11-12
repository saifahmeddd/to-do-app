"""Application workflows for local password authentication and JWT sessions."""

from hashlib import sha256

from application.dtos.auth_dto import (
    AuthSessionDTO,
    LoginUserDTO,
    RegisterUserDTO,
)
from application.exceptions.identity_errors import LoginFailed, RegistrationFailed
from application.exceptions.user_already_exists import UserAlreadyExists
from application.interfaces.google_identity_verifier import GoogleIdentityVerifier
from application.interfaces.password_hasher import PasswordHasher
from application.interfaces.runtime import Clock
from application.interfaces.token_issuer import TokenIssuer
from application.interfaces.user_repository import UserRepository


class AuthService:
    """Coordinate local user storage, password verification, and JWT issuance."""

    def __init__(
        self,
        users: UserRepository,
        passwords: PasswordHasher,
        tokens: TokenIssuer,
        clock: Clock,
        google_identity: GoogleIdentityVerifier,
    ):
        self.users = users
        self.passwords = passwords
        self.tokens = tokens
        self.clock = clock
        self.google_identity = google_identity

    def register(self, command: RegisterUserDTO) -> AuthSessionDTO:
        email = command.email.strip().casefold()
        email_key = _email_key(email)
        try:
            user = self.users.create_user(
                email,
                email_key,
                self.passwords.hash(command.password),
                self.clock.now(),
            )
        except UserAlreadyExists as exc:
            raise RegistrationFailed(
                "An account with this email already exists in this database."
            ) from exc
        return self._session(user.user_id, user.email)

    def login(self, command: LoginUserDTO) -> AuthSessionDTO:
        email = command.email.strip().casefold()
        user = self.users.get_by_email_key(_email_key(email))
        if user is None or user.password_hash is None or not self.passwords.verify(
            user.password_hash,
            command.password,
        ):
            raise LoginFailed("Invalid email or password.")

        self.users.record_login(_email_key(email), self.clock.now())
        return self._session(user.user_id, user.email)

    def login_with_google(self, id_token: str) -> AuthSessionDTO:
        identity = self.google_identity.verify(id_token)
        email = identity.email.strip().casefold()
        email_key = _email_key(email)

        user = self.users.get_by_google_subject(identity.subject)
        if user is None:
            # Matching emails alone do not prove the user intended to link sign-in methods.
            if self.users.get_by_email_key(email_key) is not None:
                raise RegistrationFailed(
                    "This email already has a password account. Accounts are not linked automatically."
                )
            try:
                user = self.users.create_google_user(
                    email, email_key, identity.subject, self.clock.now()
                )
            except UserAlreadyExists as exc:
                # A simultaneous first sign-in may have created this Google user.
                user = self.users.get_by_google_subject(identity.subject)
                if user is None:
                    raise RegistrationFailed(
                        "An account with this email already exists in this database."
                    ) from exc

        self.users.record_login(_email_key(user.email), self.clock.now())
        return self._session(user.user_id, user.email)

    def _session(self, user_id: str, email: str) -> AuthSessionDTO:
        return AuthSessionDTO(
            user_id=user_id,
            email=email,
            database=self.tokens.database,
            access_token=self.tokens.issue(user_id, email),
            token_type="Bearer",
            expires_in=self.tokens.expires_in,
        )


def _email_key(email: str) -> str:
    """Create a stable lookup key without using an email as a document ID."""
    return sha256(email.encode("utf-8")).hexdigest()
