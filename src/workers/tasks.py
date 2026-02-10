import logging

from shared.features.event_sourcing.service import EventSourcingService
from shared.features.semantic_reducer.service import SemanticReducerService
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def process_note_version_events() -> None:
    """Process new note versions and create corresponding raw events."""
    try:
        service = EventSourcingService()
        newly_created_event_ids = service.process_note_versions()

        # Enqueue newly created raw events to semantic_reducer queue
        # This happens AFTER transaction commit to ensure events are persisted
        if newly_created_event_ids:
            for event_id in newly_created_event_ids:
                try:
                    process_semantic_reduction.delay(event_id)  # type: ignore[attr-defined]
                    logger.info(
                        f"Enqueued raw event {event_id} to semantic_reducer queue"
                    )
                except Exception as e:
                    # Log error but don't fail the entire operation
                    # The event can be processed later via unprocessed events query
                    logger.error(
                        f"Failed to enqueue raw event {event_id} to "
                        f"semantic_reducer queue: {e}",
                        exc_info=True,
                    )
    except Exception as e:
        logger.error(f"Failed to process note version events: {e}", exc_info=True)
        raise


@celery_app.task
def process_semantic_reduction(raw_event_id: int) -> None:
    """Process a raw event through semantic reduction."""
    try:
        service = SemanticReducerService()
        service.process_event(raw_event_id)
    except Exception as e:
        logger.error(
            f"Failed to process semantic reduction for raw_event {raw_event_id}: {e}",
            exc_info=True,
        )
        raise


# Configure periodic task schedule
celery_app.conf.beat_schedule = {
    "process-note-version-events-every-minute": {
        "task": "workers.tasks.process_note_version_events",
        "schedule": 60.0,  # Run every 60 seconds (1 minute)
    },
}
