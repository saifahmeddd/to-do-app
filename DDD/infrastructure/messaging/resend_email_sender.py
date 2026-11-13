"""Send task reminders through Resend."""

from datetime import datetime, timezone


class ResendEmailSender:
    def __init__(self, api_key: str, from_email: str):
        import resend
        resend.api_key = api_key
        self.resend = resend
        self.from_email = from_email

    def send_task_reminder(self, recipient: str, title: str, submission_date: str) -> None:
        return self.resend.Emails.send({
            "from": self.from_email,
            "to": [recipient],
            "subject": f"Task due tomorrow: {title}",
            "text": f"Reminder: {title} is due on {submission_date}.",
        })

    def schedule_task_due_reminder(
        self, recipient: str, title: str, due_at: datetime
    ) -> str:
        response = self.resend.Emails.send({
            "from": self.from_email,
            "to": [recipient],
            "subject": f"Task due now: {title}",
            "text": f"Your task, {title}, is due now ({due_at.astimezone(timezone.utc).isoformat()}).",
            "scheduled_at": due_at.astimezone(timezone.utc).isoformat(),
        })
        return _response_id(response)

    def cancel_task_due_reminder(self, reminder_id: str) -> None:
        response = self.resend.Emails.cancel(email_id=reminder_id)
        _raise_response_error(response)

    def send_welcome_email(self, recipient: str) -> object:
        return self.resend.Emails.send({
            "from": self.from_email,
            "to": [recipient],
            "subject": "Welcome!!",
            "text": "Welcome! Your account is ready. You can create tasks and set due dates and times to receive email reminders.",
        })


def _response_id(response: object) -> str:
    _raise_response_error(response)
    if isinstance(response, dict):
        payload = response.get("data", response)
        identifier = payload.get("id") if isinstance(payload, dict) else None
    else:
        identifier = getattr(response, "id", None)
        data = getattr(response, "data", None)
        if identifier is None and isinstance(data, dict):
            identifier = data.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise RuntimeError("Resend did not return a scheduled reminder ID.")
    return identifier


def _raise_response_error(response: object) -> None:
    if isinstance(response, dict):
        error = response.get("error")
        if error:
            raise RuntimeError(f"Resend reminder request failed: {error}")
        if response.get("name") and response.get("message"):
            raise RuntimeError(f"Resend reminder request failed: {response['message']}")
