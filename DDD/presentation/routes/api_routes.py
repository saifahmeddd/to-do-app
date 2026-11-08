"""Top-level route composition for public auth and protected task requests."""

from application.exceptions.authentication_failed import AuthenticationFailed
from application.interfaces.authentication import AuthenticatedUser
from presentation.routes.auth_routes import AUTH_PATHS, AuthRoutes
from presentation.routes.task_routes import TaskRoutes


RUNTIME_PATH = "/runtime"


class ApiRoutes:
    """Select an auth or task route while preserving task authorization."""

    def __init__(
        self,
        auth_routes: AuthRoutes,
        task_routes: TaskRoutes,
        active_database: str = "firestore",
    ):
        self.auth_routes = auth_routes
        self.task_routes = task_routes
        self.active_database = active_database

    def requires_authentication(self, path: str) -> bool:
        """Keep only auth and runtime information routes public."""
        return path not in AUTH_PATHS and path != RUNTIME_PATH

    def dispatch(
        self,
        method: str,
        path: str,
        body: object,
        user: AuthenticatedUser | None,
    ) -> tuple[int, dict]:
        """Dispatch a request to its presentation route group."""
        if path == RUNTIME_PATH:
            if method == "GET":
                return 200, {"database": self.active_database}
            return 405, {"error": "Method not allowed."}
        if path in AUTH_PATHS:
            return self.auth_routes.dispatch(method, path, body)
        if user is None:
            raise AuthenticationFailed("A verified user is required.")
        return self.task_routes.dispatch(method, path, body, user)
