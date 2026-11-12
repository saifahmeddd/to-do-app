"""Infrastructure adapter for verifying Google OpenID Connect ID tokens."""

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from application.dtos.auth_dto import GoogleIdentityDTO
from application.exceptions.authentication_failed import AuthenticationFailed
from application.interfaces.google_identity_verifier import GoogleIdentityVerifier


class GoogleIdentityTokenVerifier(GoogleIdentityVerifier):
    """Verify signature, issuer, audience, and expiry before trusting claims."""

    def __init__(self, client_id: str | None):
        self.client_id = client_id

    def verify(self, token: str) -> GoogleIdentityDTO:
        if not self.client_id:
            raise AuthenticationFailed("Google sign-in is not configured.")

        try:
            claims = id_token.verify_oauth2_token(
                token, Request(), audience=self.client_id
            )
        except (GoogleAuthError, ValueError, TypeError) as exc:
            raise AuthenticationFailed(
                "The Google sign-in token is invalid or expired."
            ) from exc

        subject = claims.get("sub")
        email = claims.get("email")
        if (
            not isinstance(subject, str)
            or not subject
            or not isinstance(email, str)
            or not email
            or claims.get("email_verified") is not True
        ):
            raise AuthenticationFailed("Google must provide a verified email address.")

        return GoogleIdentityDTO(subject=subject, email=email)
