"""Validation at the HTTP boundary for credential request bodies."""

from presentation.validators.task_validator import InvalidRequest


def validate_google_token(body: object) -> str:
    """Accept only the Google ID token needed by the sign-in use case."""
    if not isinstance(body, dict) or set(body) != {"id_token"}:
        raise InvalidRequest("Body must contain only id_token.")
    token = body["id_token"]
    if not isinstance(token, str) or not token or len(token) > 16_384:
        raise InvalidRequest("A valid Google ID token is required.")
    return token


def validate_github_code(body: object) -> str:
    if not isinstance(body, dict) or set(body) != {"code"}:
        raise InvalidRequest("Body must contain only code.")
    code = body["code"]
    if not isinstance(code, str) or not code or len(code) > 2048:
        raise InvalidRequest("A valid GitHub authorization code is required.")
    return code


def validate_credentials(body: object) -> tuple[str, str]:
    """Return normalized credentials from an exact email/password JSON object."""
    if not isinstance(body, dict):
        raise InvalidRequest("Body must be a JSON object.")
    if set(body) != {"email", "password"}:
        raise InvalidRequest("Body must contain only email and password.")

    email = body["email"]
    password = body["password"]
    if not isinstance(email, str) or not email.strip():
        raise InvalidRequest("Enter a valid email address.")
    email = email.strip()
    local, separator, domain = email.partition("@")
    if (
        not separator
        or not local
        or not domain
        or "." not in domain
        or any(character.isspace() for character in email)
        or len(email) > 254
    ):
        raise InvalidRequest("Enter a valid email address.")
    if not isinstance(password, str):
        raise InvalidRequest("Password must be text.")
    if len(password) < 8:
        raise InvalidRequest("Password must contain at least 8 characters.")
    if len(password) > 128:
        raise InvalidRequest("Password must contain no more than 128 characters.")

    # Email surrounding whitespace is accidental input. Password bytes are kept
    # exactly as supplied because whitespace may be part of a valid password.
    return email, password
