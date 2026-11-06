"""Issue and verify short-lived access tokens for the selected database."""

from datetime import datetime, timedelta, timezone

import jwt

from application.exceptions.authentication_failed import AuthenticationFailed
from application.interfaces.authentication import AuthenticatedUser
from domain.exceptions.task_errors import InvalidUserId
from domain.value_objects.user_id import UserId


class JwtTokenService:
    """Sign JWTs and verify their signature, expiry, issuer, and database."""

    issuer = "prac-todo-api"

    def __init__(self, secret: str, database: str, expires_minutes: int = 60):
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes.")
        if expires_minutes < 1:
            raise ValueError("JWT_EXPIRES_MINUTES must be at least 1.")

        self.secret = secret
        self.database = database
        self.expires_minutes = expires_minutes

    @property
    def expires_in(self) -> int:
        return self.expires_minutes * 60

    def issue(self, user_id: str, email: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": user_id,
                "email": email,
                "iat": now,
                "exp": now + timedelta(minutes=self.expires_minutes),
                "iss": self.issuer,
                "aud": f"tasks:{self.database}",
            },
            self.secret,
            algorithm="HS256",
        )

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                issuer=self.issuer,
                audience=f"tasks:{self.database}",
                options={"require": ["sub", "email", "iat", "exp", "iss", "aud"]},
            )
            if not isinstance(claims.get("email"), str):
                raise AuthenticationFailed("The access token is invalid or expired.")
            return AuthenticatedUser(
                id=UserId(claims["sub"]),
                email=claims["email"],
            )
        except (jwt.InvalidTokenError, InvalidUserId, ValueError, TypeError) as exc:
            raise AuthenticationFailed("The access token is invalid or expired.") from exc
