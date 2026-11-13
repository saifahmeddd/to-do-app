"""Transport validation for task request payloads."""


from datetime import date, datetime


class InvalidRequest(ValueError):
    """Malformed transport input, independent of business invariants."""


def validate_create(body: object) -> str:
    """Return the title when the create body has exactly the expected shape."""
    allowed = {"title", "submission_date", "submission_at"}
    if not isinstance(body, dict) or "title" not in body or set(body) - allowed:
        raise InvalidRequest("Expected title and an optional due date and time.")
    if "submission_date" in body and "submission_at" in body:
        raise InvalidRequest("Provide either a date-only submission_date or submission_at.")
    if not isinstance(body["title"], str):
        raise InvalidRequest("Title must be a string.")
    submission_date = body.get("submission_date")
    if submission_date is not None:
        if not isinstance(submission_date, str):
            raise InvalidRequest("Submission date must be an ISO date.")
        try:
            date.fromisoformat(submission_date)
        except ValueError:
            raise InvalidRequest("Submission date must be an ISO date.") from None
    if "submission_at" in body and body["submission_at"] is not None:
        validate_submission_at_value(body["submission_at"])
    return body["title"]


def validate_submission_date(body: object) -> str | None:
    return body.get("submission_date")


def validate_submission_at(body: object) -> str | None:
    return body.get("submission_at")


def validate_submission_at_value(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidRequest("Due date and time must be an ISO timestamp with a timezone.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise InvalidRequest("Due date and time must be an ISO timestamp with a timezone.") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidRequest("Due date and time must include a timezone.")
    return value


def validate_update(body: object) -> str:
    """Return the title when the update body has exactly the expected shape."""
    if not isinstance(body, dict) or "title" not in body or set(body) - {"title", "submission_at"}:
        raise InvalidRequest("Expected title and an optional due date and time.")
    if not isinstance(body["title"], str):
        raise InvalidRequest("Title must be a string.")
    if "submission_at" in body and body["submission_at"] is not None:
        validate_submission_at_value(body["submission_at"])
    return body["title"]
