"""Service for processing semantic reduction operations."""

import logging
from datetime import datetime
from typing import Protocol

from psycopg import Connection

from shared.features.event_sourcing.enums import EventType
from shared.features.event_sourcing.models import RawEvent
from shared.features.semantic_reducer.models import SemanticEventCreate
from shared.features.semantic_reducer.note_versions.repository import (
    NoteVersionRepository,
)
from shared.features.semantic_reducer.repository import SemanticReducerRepository
from shared.infra import db

from .note_versions.reducer import NoteVersionReducer

logger = logging.getLogger(__name__)


class EventReducer(Protocol):
    """Protocol for event reducers."""

    reducer_version: str

    def reduce(
        self, raw_event: RawEvent, note_version_repo: NoteVersionRepository
    ) -> SemanticEventCreate:
        """Reduce a raw event into a SemanticEventCreate.
        
        Args:
            raw_event: The raw event to reduce
            note_version_repo: Repository for note version operations
                (may be None for other event types)
            
        Returns:
            SemanticEventCreate object ready to be inserted
        """
        ...


class SemanticReducerService:
    """Service for orchestrating semantic reduction operations."""

    def __init__(self) -> None:
        """Initialize the service."""
        # Initialize reducers for different event types
        self._reducers: dict[EventType, EventReducer] = {
            EventType.NOTE_VERSION_CREATED: NoteVersionReducer(),
        }

    def process_event(self, raw_event_id: int) -> None:
        """Process a raw event and create corresponding semantic event.
        
        This function is transaction-safe: all operations (create semantic_event,
        update ingested_at) are committed atomically, or the entire transaction
        is rolled back.
        
        Uses ON CONFLICT DO NOTHING for idempotency - no pre-checks needed.
        This provides race safety, retry safety, crash safety, and replay safety.
        
        Args:
            raw_event_id: ID of the raw event to process
        """
        with db.sync_connection() as conn:
            # Ensure we're in a transaction
            conn.autocommit = False

            try:
                repository = SemanticReducerRepository(conn)

                # Fetch the raw event
                raw_event = repository.get_raw_event_by_id(raw_event_id=raw_event_id)
                if raw_event is None:
                    raise ValueError(f"Raw event {raw_event_id} not found")

                # Route to appropriate reducer based on event type using match/case
                semantic_event_create = self._process_event(raw_event, conn)

                # If reducer returns None, skip processing
                if semantic_event_create is None:
                    logger.info(
                        f"Reducer returned None for raw_event {raw_event_id}, skipping"
                    )
                    conn.commit()
                    return

                # Create semantic event (idempotent via ON CONFLICT DO NOTHING)
                semantic_event_id = repository.create_semantic_event(semantic_event_create)

                # Update ingested_at on raw events (idempotent - safe to run multiple times)
                if semantic_event_id is not None:
                    # Only update if we actually inserted a new event
                    ingested_at = datetime.now()
                    repository.update_raw_events_ingested_at(
                        semantic_event_create.raw_event_ids, ingested_at
                    )
                    # Get event_type string for logging
                    event_type_str = (
                        raw_event.event_type.value
                        if hasattr(raw_event.event_type, "value")
                        else str(raw_event.event_type)
                    )
                    logger.info(
                        f"Created semantic event {semantic_event_id} for raw_event "
                        f"{raw_event_id} (event_type={event_type_str})"
                    )
                else:
                    # Event already existed (ON CONFLICT), but still update ingested_at
                    # This is idempotent and safe
                    ingested_at = datetime.now()
                    repository.update_raw_events_ingested_at(
                        semantic_event_create.raw_event_ids, ingested_at
                    )
                    logger.info(
                        f"Semantic event already exists for raw_event {raw_event_id} "
                        f"(unique_hash={semantic_event_create.unique_hash}), "
                        f"updated ingested_at"
                    )

                conn.commit()
            except Exception as e:
                # Any unhandled exception triggers rollback
                conn.rollback()
                logger.error(
                    f"Transaction failed and was rolled back for raw_event "
                    f"{raw_event_id}: {e}",
                    exc_info=True,
                )
                raise

    def _process_event(
        self, raw_event: RawEvent, connection: Connection
    ) -> SemanticEventCreate | None:
        """Process event based on event type using match/case statement.
        
        This method dispatches to the appropriate reducer based on event type.
        Acts as a router/dispatcher for different event types.
        
        Args:
            raw_event: The raw event to process
            connection: Database connection for creating event-specific repositories
            
        Returns:
            SemanticEventCreate object if event should be processed, None otherwise
        """
        match raw_event.event_type:
            case EventType.NOTE_VERSION_CREATED:
                reducer = self._reducers.get(EventType.NOTE_VERSION_CREATED)
                if reducer is None:
                    raise ValueError(
                        f"No reducer found for {EventType.NOTE_VERSION_CREATED.value}"
                    )
                # Create note version repository
                note_version_repo = NoteVersionRepository(connection)
                return reducer.reduce(raw_event, note_version_repo)

            case _:
                # Default: no reducer for this event type, return None
                logger.info(
                    f"No specific reducer for event_type {raw_event.event_type.value}, "
                    f"skipping"
                )
                return None
