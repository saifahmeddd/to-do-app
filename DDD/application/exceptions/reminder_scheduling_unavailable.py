"""Raised when exact-time email scheduling is not configured for the app."""


class ReminderSchedulingUnavailable(RuntimeError):
    pass
