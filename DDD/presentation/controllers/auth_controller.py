"""HTTP-facing controller for registration and login use cases."""

from application.dtos.auth_dto import LoginUserDTO, RegisterUserDTO
from application.services.auth_service import AuthService
from presentation.validators.auth_validator import (
    validate_credentials,
    validate_github_code,
    validate_google_token,
)
from presentation.views.auth_view import auth_session_view


class AuthController:
    """Translate credential requests into application DTOs and JSON responses."""

    def __init__(self, service: AuthService):
        self.service = service

    def register(self, body: object) -> tuple[int, dict]:
        """Validate input, run registration, and return the issued session."""
        email, password = validate_credentials(body)
        command = RegisterUserDTO(email=email, password=password)
        session = self.service.register(command)
        return 201, auth_session_view(session)

    def login(self, body: object) -> tuple[int, dict]:
        """Validate input, run login, and return the issued session."""
        email, password = validate_credentials(body)
        command = LoginUserDTO(email=email, password=password)
        session = self.service.login(command)
        return 200, auth_session_view(session)

    def login_with_google(self, body: object) -> tuple[int, dict]:
        id_token = validate_google_token(body)
        session = self.service.login_with_google(id_token)
        return 200, auth_session_view(session)

    def login_with_github(self, body: object) -> tuple[int, dict]:
        code = validate_github_code(body)
        session = self.service.login_with_github(code)
        return 200, auth_session_view(session)
