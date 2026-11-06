"""Registration conflict raised when an email already exists in this database."""


class UserAlreadyExists(Exception):
    """The selected database already contains an account for this email."""
