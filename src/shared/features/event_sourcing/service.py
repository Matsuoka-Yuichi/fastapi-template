"""Service for processing event sourcing operations."""

import logging

from shared.features.event_sourcing.enums import (
    EventType,
    SourceSystem,
    SourceType,
)
from shared.features.event_sourcing.models import NoteVersion, RawEventCreate, RawEventSourceUpdate
from shared.features.event_sourcing.repository import EventSourcingRepository
from shared.infra import db

logger = logging.getLogger(__name__)


class EventSourcingService:
    """Service for orchestrating event sourcing operations."""

    def process_note_versions(self) -> list[int]:
        """Process new note versions and create corresponding raw events.
        
        This function is transaction-safe: all events and checkpoint updates
        are committed atomically, or the entire transaction is rolled back.
        
        Returns:
            List of newly created raw event IDs
        """
        with db.sync_connection() as conn:
            # Ensure we're in a transaction (explicit autocommit=False for safety)
            conn.autocommit = False
            
            try:
                repository = EventSourcingRepository(conn)

                # get checkpoint to see where to start processing note versions from
                raw_event_source = repository.get_raw_event_source(
                    SourceType.COGNO_NOTE_VERSIONS, SourceSystem.COGNO
                )

                if raw_event_source is None:
                    raise RuntimeError(
                        f"Raw event source not found for {SourceType.COGNO_NOTE_VERSIONS.value} / "
                        f"{SourceSystem.COGNO.value}. "
                        "Raw event sources must be created via database migrations."
                    )

                source_id = raw_event_source.id
                last_event_id_str = raw_event_source.last_event_id
                last_event_id = int(last_event_id_str)

                # get new note versions to turn into raw events
                note_versions = repository.get_note_versions_since(last_event_id)

                if not note_versions:
                    logger.info("No new note versions to process")
                    return []

                # Process each note version with strict all-or-nothing semantics
                # Any exception will bubble up and trigger transaction rollback
                inserted_count = 0
                already_exists_count = 0
                newly_created_event_ids: list[int] = []

                for note_version in note_versions:
                    event = RawEventCreate[NoteVersion](
                        source_id=source_id,
                        workspace_id=note_version.workspace_id,
                        event_type=EventType.NOTE_VERSION_CREATED,
                        event_version=1,
                        payload=note_version,
                        occurred_at=note_version.created_at,
                        source_event_id=str(note_version.id),
                    )
                    event_id = repository.create_raw_event(event)

                    # If event_id is None, the event already existed (ON CONFLICT)
                    if event_id is None:
                        already_exists_count += 1
                        logger.debug(
                            f"Raw event already exists for note_version "
                            f"{note_version.id}, skipping"
                        )
                    else:
                        inserted_count += 1
                        newly_created_event_ids.append(event_id)
                        logger.debug(
                            f"Created raw event {event_id} for note_version "
                            f"{note_version.id}"
                        )

                # Since note_versions are ORDER BY id ASC, the last one has the max id
                last_note_version = note_versions[-1]
                max_event_id = last_note_version.id
                max_event_time = last_note_version.created_at

                # Update checkpoint
                # CRITICAL: Checkpoint update must succeed for transaction to commit
                # This ensures consistency - events are only committed if checkpoint is updated
                checkpoint_update = RawEventSourceUpdate(
                    last_event_id=str(max_event_id),
                    last_event_at=max_event_time,
                )
                repository.update_raw_event_source_checkpoint(
                    source_id,
                    checkpoint_update,
                )
                conn.commit()
                logger.info(
                    f"Processed {len(note_versions)} note versions "
                    f"(inserted={inserted_count}, duplicates={already_exists_count}). "
                    f"Updated checkpoint: last_event_id={max_event_id}, "
                    f"last_event_at={max_event_time}"
                )

                return newly_created_event_ids
            except Exception as e:
                # Any unhandled exception triggers rollback
                conn.rollback()
                logger.error(
                    f"Transaction failed and was rolled back: {e}",
                    exc_info=True,
                )
                raise
