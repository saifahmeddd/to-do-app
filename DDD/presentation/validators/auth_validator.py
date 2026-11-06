"""Validation at the HTTP boundary for credential request bodies."""

from presentation.validators.task_validator import InvalidRequest


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
