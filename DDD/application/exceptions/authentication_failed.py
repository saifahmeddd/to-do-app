"""Authentication failures safe for mapping to an HTTP 401 response."""


class AuthenticationFailed(Exception):
    """The request did not contain a valid, unexpired access token."""
