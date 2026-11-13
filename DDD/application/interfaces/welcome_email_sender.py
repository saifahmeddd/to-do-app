"""Application port for sending a newly registered user a welcome email."""

from typing import Protocol


class WelcomeEmailSender(Protocol):
    def send_welcome_email(self, recipient: str) -> object: ...
