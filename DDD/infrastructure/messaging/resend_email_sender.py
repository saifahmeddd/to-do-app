"""Send task reminders through Resend."""

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

    def send_welcome_email(self, recipient: str) -> object:
        return self.resend.Emails.send({
            "from": self.from_email,
            "to": [recipient],
            "subject": "Welcome!!",
            "text": "Welcome! Your account is ready. You can now create tasks and set submission dates to receive reminders.",
        })
