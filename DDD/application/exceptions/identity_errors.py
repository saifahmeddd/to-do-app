"""Safe application failures for password-authentication use cases."""


class RegistrationFailed(Exception):
    """Registration conflicts with an account already in this database."""


class LoginFailed(Exception):
    """The account is missing or its password does not match."""
