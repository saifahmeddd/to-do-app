"""Send one-day-prior reminders for incomplete tasks."""

import logging
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bootstrap import build_task_repository, build_user_repository
from infrastructure.config.settings import Settings
from infrastructure.firebase.client import create_firestore_client
from infrastructure.messaging.resend_email_sender import ResendEmailSender


def run_reminders(settings: Settings, target_date: date | None = None, recipient_override: str | None = None, dry_run: bool = False) -> list[dict]:
    zone = ZoneInfo(settings.reminder_timezone)
    target_date = target_date or datetime.now(zone).date() + timedelta(days=1)
    start = datetime.combine(target_date, time.min, timezone.utc)
    end = start + timedelta(days=1)
    firestore = create_firestore_client(settings.firebase_project_id, settings.firebase_credentials_path) if settings.task_database == "firestore" else None
    tasks = build_task_repository(settings, firestore)
    users = build_user_repository(settings, firestore)
    sender = None
    if not dry_run:
        if not settings.resend_api_key or not settings.reminder_from_email:
            raise RuntimeError("RESEND_API_KEY and REMINDER_FROM_EMAIL are required.")
        sender = ResendEmailSender(settings.resend_api_key, settings.reminder_from_email)
    results = []
    for task in tasks.due_for_reminder(start, end):
        if task.completed_at or task.submission_date is None:
            continue
        if task.submission_date.date() != target_date:
            continue
        if task.reminder_sent_for and task.reminder_sent_for.date() == target_date:
            continue
        user = users.get_by_user_id(task.owner_id.value)
        if user is None:
            logging.warning("Skipping task %s: owner not found", task.id.value)
            continue
        recipient = recipient_override or user.email
        result = {
            "task_id": task.id.value,
            "title": task.title.value,
            "recipient": recipient,
            "submission_date": target_date.isoformat(),
        }
        if dry_run:
            results.append({**result, "dry_run": True})
            continue
        response = sender.send_task_reminder(recipient, task.title.value, target_date.isoformat())
        dispatch_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
        if not dispatch_id:
            raise RuntimeError(f"Resend did not return a dispatch ID for task {task.id.value}.")
        tasks.mark_reminded(task.id, start)
        results.append({**result, "dispatch_id": dispatch_id})
    return results


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_environment()
    results = run_reminders(settings)
    for result in results:
        logging.info("Reminder dispatched: task_id=%s dispatch_id=%s", result["task_id"], result["dispatch_id"])
    logging.info("Sent %d task reminder(s).", len(results))


if __name__ == "__main__":
    main()
