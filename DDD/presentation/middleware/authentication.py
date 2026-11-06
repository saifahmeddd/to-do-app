"""Bearer-token authentication at the HTTP presentation boundary."""

from typing import Mapping

from application.exceptions.authentication_failed import AuthenticationFailed
from application.interfaces.authentication import AuthenticatedUser, TokenVerifier


def authenticate(
    headers: Mapping[str, str], verifier: TokenVerifier
) -> AuthenticatedUser:
    """Verify an Authorization bearer token before a protected route runs."""
    authorization = headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationFailed(
            "A valid Authorization: Bearer <access token> header is required."
        )
    return verifier.verify(token.strip())
