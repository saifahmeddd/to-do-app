"""Application workflows for local password authentication and JWT sessions."""

from hashlib import sha256
import logging

from application.dtos.auth_dto import (
    AuthSessionDTO,
    LoginUserDTO,
    RegisterUserDTO,
)
from application.exceptions.identity_errors import LoginFailed, RegistrationFailed
from application.exceptions.user_already_exists import UserAlreadyExists
from application.interfaces.google_identity_verifier import GoogleIdentityVerifier
from application.interfaces.github_identity_verifier import GitHubIdentityVerifier
from application.interfaces.password_hasher import PasswordHasher
from application.interfaces.runtime import Clock
from application.interfaces.token_issuer import TokenIssuer
from application.interfaces.user_repository import UserRepository
from application.interfaces.welcome_email_sender import WelcomeEmailSender


class AuthService:
    """Coordinate local user storage, password verification, and JWT issuance."""

    def __init__(
        self,
        users: UserRepository,
        passwords: PasswordHasher,
        tokens: TokenIssuer,
        clock: Clock,
        google_identity: GoogleIdentityVerifier,
        welcome_email: WelcomeEmailSender | None = None,
        github_identity: GitHubIdentityVerifier | None = None,
    ):
        self.users = users
        self.passwords = passwords
        self.tokens = tokens
        self.clock = clock
        self.google_identity = google_identity
        self.welcome_email = welcome_email
        self.github_identity = github_identity

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
        self._send_welcome_email(user.email)
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
        created_user = False
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
                created_user = True
            except UserAlreadyExists as exc:
                # A simultaneous first sign-in may have created this Google user.
                user = self.users.get_by_google_subject(identity.subject)
                if user is None:
                    raise RegistrationFailed(
                        "An account with this email already exists in this database."
                    ) from exc

        if created_user:
            self._send_welcome_email(user.email)

        self.users.record_login(_email_key(user.email), self.clock.now())
        return self._session(user.user_id, user.email)

    def _send_welcome_email(self, recipient: str) -> None:
        if self.welcome_email is None:
            return
        try:
            response = self.welcome_email.send_welcome_email(recipient)
            error = response.get("message") if isinstance(response, dict) and response.get("name") else None
            if error:
                logging.getLogger(__name__).error("Welcome email failed for a new account: %s", error)
        except Exception:
            logging.getLogger(__name__).exception("Welcome email failed for a new account.")

    def login_with_github(self, authorization_code: str) -> AuthSessionDTO:
        if self.github_identity is None:
            raise LoginFailed("GitHub sign-in is not configured.")
        identity = self.github_identity.verify(authorization_code)
        email = identity.email.strip().casefold()
        email_key = _email_key(email)
        user = self.users.get_by_github_subject(identity.subject)
        created_user = False
        if user is None:
            if self.users.get_by_email_key(email_key) is not None:
                raise RegistrationFailed(
                    "This email already belongs to another sign-in method. Accounts are not linked automatically."
                )
            try:
                user = self.users.create_github_user(
                    email, email_key, identity.subject, self.clock.now()
                )
                created_user = True
            except UserAlreadyExists as exc:
                user = self.users.get_by_github_subject(identity.subject)
                if user is None:
                    raise RegistrationFailed(
                        "An account with this email already exists in this database."
                    ) from exc
        if created_user:
            self._send_welcome_email(user.email)
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
