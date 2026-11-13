"""Standard-library HTTP adapter for the task presentation layer."""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from application.exceptions.authentication_failed import AuthenticationFailed
from application.exceptions.identity_errors import (
    LoginFailed,
    RegistrationFailed,
)
from application.exceptions.identity_provider_error import IdentityProviderError
from application.exceptions.task_not_found import TaskNotFound
from application.interfaces.authentication import TokenVerifier
from domain.exceptions.task_errors import InvalidTask
from presentation.middleware.authentication import authenticate
from presentation.middleware.request_logging import begin_request
from presentation.routes.api_routes import ApiRoutes
from presentation.validators.task_validator import InvalidRequest
from presentation.views.task_view import error_view


MAX_REQUEST_BODY_BYTES = 16 * 1024
BODY_METHODS = frozenset({"POST", "PUT", "PATCH"})


def make_server(
    host: str,
    port: int,
    routes: ApiRoutes,
    token_verifier: TokenVerifier,
) -> HTTPServer:
    """Create an HTTP server whose handler delegates routing to ApiRoutes."""

    class Handler(BaseHTTPRequestHandler):
        """Convert HTTP messages to and from the presentation-layer contract."""

        def handle_request(self) -> None:
            """Process one request and convert known failures to HTTP responses."""
            path = urlsplit(self.path).path
            request_id = begin_request(self.command, path)

            try:
                user = None
                if routes.requires_authentication(path):
                    user = authenticate(self.headers, token_verifier)
                body = self._read_json_body()
                status, payload = routes.dispatch(self.command, path, body, user)
            except AuthenticationFailed as exc:
                status, payload = 401, error_view(str(exc))
            except LoginFailed as exc:
                status, payload = 401, error_view(str(exc))
            except IdentityProviderError as exc:
                status, payload = 401, error_view(str(exc))
            except RegistrationFailed as exc:
                status, payload = 409, error_view(str(exc))
            except (
                InvalidRequest,
                InvalidTask,
                json.JSONDecodeError,
                UnicodeDecodeError,
            ) as exc:
                status, payload = 400, error_view(str(exc))
            except TaskNotFound as exc:
                status, payload = 404, error_view(str(exc))
            except Exception:
                # Log the detailed failure server-side without exposing it to clients.
                logging.getLogger(__name__).exception(
                    "request_id=%s failed", request_id
                )
                status, payload = 500, error_view("Internal server error.")

            self._write_json_response(status, payload, request_id)

        def _read_json_body(self) -> object:
            """Read a bounded JSON body for methods that can carry one."""
            if self.command not in BODY_METHODS:
                return None

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise InvalidRequest("Invalid Content-Length.") from None

            if not 0 <= content_length <= MAX_REQUEST_BODY_BYTES:
                raise InvalidRequest(
                    f"Body must be at most {MAX_REQUEST_BODY_BYTES // 1024} KiB."
                )
            if content_length == 0:
                return None
            if self.headers.get_content_type() != "application/json":
                raise InvalidRequest("Use Content-Type: application/json.")

            return json.loads(self.rfile.read(content_length))

        def _write_json_response(
            self,
            status: int,
            payload: dict,
            request_id: str,
        ) -> None:
            """Serialize a response body and add consistent HTTP headers."""
            encoded_payload = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded_payload)))
            self.send_header("X-Request-ID", request_id)
            self.end_headers()
            self.wfile.write(encoded_payload)

        do_GET = handle_request
        do_POST = handle_request
        do_PUT = handle_request
        do_PATCH = handle_request
        do_DELETE = handle_request

    return HTTPServer((host, port), Handler)
