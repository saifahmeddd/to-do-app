"""Public HTTP route table for credential-based authentication use cases."""

from presentation.controllers.auth_controller import AuthController


REGISTER_PATH = "/auth/register"
LOGIN_PATH = "/auth/login"
GOOGLE_LOGIN_PATH = "/auth/google"
AUTH_PATHS = frozenset({REGISTER_PATH, LOGIN_PATH, GOOGLE_LOGIN_PATH})


class AuthRoutes:
    """Dispatch the two public authentication endpoints to their controller."""

    def __init__(self, controller: AuthController):
        self.controller = controller

    def dispatch(self, method: str, path: str, body: object) -> tuple[int, dict]:
        """Return the selected auth action or an HTTP route-level response."""
        if path == REGISTER_PATH:
            if method == "POST":
                return self.controller.register(body)
            return 405, {"error": "Method not allowed."}
        if path == LOGIN_PATH:
            if method == "POST":
                return self.controller.login(body)
            return 405, {"error": "Method not allowed."}
        if path == GOOGLE_LOGIN_PATH:
            if method == "POST":
                return self.controller.login_with_google(body)
            return 405, {"error": "Method not allowed."}
        return 404, {"error": "Route not found."}
