"""Focused tests for the JWT authentication boundary."""

import unittest

from application.exceptions.authentication_failed import AuthenticationFailed
from application.interfaces.authentication import AuthenticatedUser
from domain.value_objects.user_id import UserId
from infrastructure.authentication.jwt_token_service import JwtTokenService
from presentation.middleware.authentication import authenticate


class StubVerifier:
    """Return a known identity while recording the received bearer token."""

    def __init__(self):
        self.token = None

    def verify(self, token: str) -> AuthenticatedUser:
        self.token = token
        return AuthenticatedUser(UserId("verified-user"), "user@example.com")


class AuthenticationTests(unittest.TestCase):
    """Prove bearer parsing and database-scoped JWT verification."""

    def test_bearer_header_is_required_and_parsed(self):
        verifier = StubVerifier()
        user = authenticate({"Authorization": "Bearer token-value"}, verifier)
        self.assertEqual(user.id.value, "verified-user")
        self.assertEqual(verifier.token, "token-value")

        for headers in [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer "}]:
            with self.subTest(headers=headers):
                with self.assertRaises(AuthenticationFailed):
                    authenticate(headers, verifier)

    def test_jwt_claims_become_authenticated_user(self):
        tokens = JwtTokenService("s" * 32, "postgres")
        token = tokens.issue("local-user", "owner@example.com")
        user = tokens.verify(token)
        self.assertEqual(user.id.value, "local-user")
        self.assertEqual(user.email, "owner@example.com")

    def test_token_for_another_database_is_rejected(self):
        token = JwtTokenService("s" * 32, "postgres").issue(
            "local-user", "owner@example.com"
        )
        with self.assertRaises(AuthenticationFailed):
            JwtTokenService("s" * 32, "firestore").verify(token)


if __name__ == "__main__":
    unittest.main()
