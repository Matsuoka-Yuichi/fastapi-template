import logging

from shared.features.event_sourcing.service import EventSourcingService
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def process_note_version_events() -> None:
    """Process new note versions and create corresponding raw events."""
    try:
        service = EventSourcingService()
        service.process_note_versions()
    except Exception as e:
        logger.error(f"Failed to process note version events: {e}", exc_info=True)
        raise


# Configure periodic task schedule
celery_app.conf.beat_schedule = {
    "process-note-version-events-every-minute": {
        "task": "workers.tasks.process_note_version_events",
        "schedule": 60.0,  # Run every 60 seconds (1 minute)
    },
}
