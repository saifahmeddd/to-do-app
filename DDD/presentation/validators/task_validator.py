"""Transport validation for task request payloads."""


from datetime import date


class InvalidRequest(ValueError):
    """Malformed transport input, independent of business invariants."""


def validate_create(body: object) -> str:
    """Return the title when the create body has exactly the expected shape."""
    if not isinstance(body, dict) or set(body) not in ({"title"}, {"title", "submission_date"}):
        raise InvalidRequest("Expected title and an optional submission_date.")
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
    return body["title"]


def validate_submission_date(body: object) -> str | None:
    return body.get("submission_date")


def validate_update(body: object) -> str:
    """Return the title when the update body has exactly the expected shape."""
    if not isinstance(body, dict) or set(body) != {"title"}:
        raise InvalidRequest("Expected a JSON object containing only title.")
    if not isinstance(body["title"], str):
        raise InvalidRequest("Title must be a string.")
    return body["title"]
