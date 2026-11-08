"""End-to-end HTTP adapter tests using fake outer dependencies."""

import http.client
import json
import threading
import unittest
from datetime import datetime, timezone

from application.dtos.auth_dto import UserCredentialDTO
from application.interfaces.authentication import AuthenticatedUser
from application.services.auth_service import AuthService
from application.services.task_service import TaskService
from domain.domain_services.task_ordering import TaskOrdering
from domain.value_objects.user_id import UserId
from infrastructure.providers.system_runtime import UUIDGenerator
from infrastructure.repositories.firestore_task_repository import FirestoreTaskRepository
from presentation.controllers.auth_controller import AuthController
from presentation.controllers.task_controller import TaskController
from presentation.http_server import make_server
from presentation.routes.api_routes import ApiRoutes
from presentation.routes.auth_routes import AuthRoutes
from presentation.routes.task_routes import TaskRoutes
from tests.fake_firestore import FakeFirestoreClient


class FixedClock:
    """Return a stable UTC timestamp for HTTP response assertions."""

    def now(self):
        return datetime(2026, 1, 1, tzinfo=timezone.utc)


class NullPublisher:
    """Accept domain events without creating an external side effect."""

    def publish(self, event):
        pass


class TestTokenVerifier:
    """Treat one predictable token as a verified user for HTTP tests."""

    def verify(self, token: str) -> AuthenticatedUser:
        return AuthenticatedUser(UserId(f"user-{token}"))


class FakeUserRepository:
    """Keep test accounts in memory behind the application repository port."""

    def __init__(self):
        self.users = {}

    def create_user(self, email, email_key, password_hash, created_at):
        user = UserCredentialDTO("local-user-1", email, password_hash)
        self.users[email_key] = user
        return user

    def get_by_email_key(self, email_key):
        return self.users.get(email_key)

    def record_login(self, email_key, logged_in_at):
        pass


class FakePasswordHasher:
    def hash(self, password):
        return f"hashed:{password}"

    def verify(self, password_hash, password):
        return password_hash == f"hashed:{password}"


class FakeTokenIssuer:
    database = "firestore"
    expires_in = 3600

    def issue(self, user_id, email):
        return f"token-for-{user_id}"


class HttpServerTests(unittest.TestCase):
    """Prove HTTP parsing, authentication, routing, and JSON responses together."""

    def setUp(self):
        self.user_repository = FakeUserRepository()
        auth_service = AuthService(
            self.user_repository,
            FakePasswordHasher(),
            FakeTokenIssuer(),
            FixedClock(),
        )
        service = TaskService(
            FirestoreTaskRepository(FakeFirestoreClient()),
            FixedClock(),
            UUIDGenerator(),
            NullPublisher(),
            TaskOrdering(),
        )
        routes = ApiRoutes(
            AuthRoutes(AuthController(auth_service)),
            TaskRoutes(TaskController(service)),
        )
        self.server = make_server("127.0.0.1", 0, routes, TestTokenVerifier())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method: str, path: str, body=None, token="one"):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        encoded = None
        if body is not None:
            encoded = json.dumps(body)
            headers["Content-Type"] = "application/json"
        connection = http.client.HTTPConnection(*self.server.server_address)
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def test_http_crud_and_owner_isolation(self):
        status, created = self.request("POST", "/tasks", {"title": "HTTP task"})
        self.assertEqual(status, 201)
        task_path = f"/tasks/{created['id']}"

        self.assertEqual(self.request("GET", task_path)[1], created)
        self.assertEqual(
            self.request("PATCH", task_path, {"title": "Updated over HTTP"})[1]["title"],
            "Updated over HTTP",
        )
        self.assertEqual(self.request("GET", "/tasks", token="two"), (200, {"tasks": []}))
        self.assertEqual(self.request("GET", task_path, token="two")[0], 404)
        self.assertEqual(self.request("DELETE", task_path)[0], 200)
        self.assertEqual(self.request("GET", task_path)[0], 404)

    def test_missing_bearer_token_returns_401(self):
        status, payload = self.request("GET", "/tasks", token=None)
        self.assertEqual(status, 401)
        self.assertIn("Bearer", payload["error"])

    def test_register_and_login_are_public_use_cases(self):
        credentials = {"email": "demo@example.com", "password": "Secret123!"}

        register_status, registered = self.request(
            "POST", "/auth/register", credentials, token=None
        )
        self.assertEqual(register_status, 201)
        self.assertEqual(registered["database"], "firestore")
        self.assertEqual(registered["access_token"], "token-for-local-user-1")
        self.assertIn(
            "demo@example.com",
            [user.email for user in self.user_repository.users.values()],
        )

        login_status, logged_in = self.request(
            "POST", "/auth/login", credentials, token=None
        )
        self.assertEqual(login_status, 200)
        self.assertEqual(logged_in["access_token"], "token-for-local-user-1")

    def test_auth_input_validation_runs_without_a_bearer_token(self):
        status, payload = self.request(
            "POST", "/auth/login", {"email": "demo@example.com"}, token=None
        )
        self.assertEqual(status, 400)
        self.assertIn("email and password", payload["error"])


if __name__ == "__main__":
    unittest.main()
