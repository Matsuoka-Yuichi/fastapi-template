"""Repository for event sourcing database operations."""

import json
from datetime import datetime
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from shared.features.event_sourcing.enums import (
    SourceSystem,
    SourceType,
)
from shared.features.event_sourcing.models import (
    NoteVersion,
    RawEventCreate,
    RawEventSource,
    RawEventSourceUpdate,
)


class EventSourcingRepository:
    """Repository for event sourcing operations."""

    def __init__(self, connection: Connection) -> None:
        """Initialize repository with a database connection."""
        self.conn = connection

    def get_raw_event_source(
        self, source_type: SourceType, source_system: SourceSystem
    ) -> RawEventSource | None:
        """Get raw event source by source_type and source_system."""
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, source_type, source_system, last_event_id, 
                       last_event_at, updated_at
                FROM cognition.raw_event_sources
                WHERE source_type = %s AND source_system = %s
                """,
                (source_type.value, source_system.value),
            )
            result = cur.fetchone()
            if result:
                return RawEventSource(**dict(result))
            return None

    def get_note_versions_since(self, last_event_id: int) -> list[NoteVersion]:
        """Get note versions after last_event_id."""
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, note_id, version, created_at, title, text, 
                           workspace_id, note_folder_id, similarity
                    FROM public.note_versions
                    WHERE id > %s
                    ORDER BY id ASC
                    """,
                    (last_event_id,),
                )
            results = cur.fetchall()
            return [NoteVersion(**dict(row)) for row in results]

    def create_raw_event[PayloadT](self, event: RawEventCreate[PayloadT]) -> int | None:
        """Create a raw event, returning its id.
        
        Returns the id if the event was inserted, or None if it already existed
        (due to ON CONFLICT DO NOTHING).
        """
        with self.conn.cursor() as cur:
            payload_dict: dict[str, Any] = event.payload.model_dump(mode='json')  # type: ignore[attr-defined]
            
            # Always insert NULL for ingested_at; it will be set by a later procedure
            cur.execute(
                """
                INSERT INTO cognition.raw_events 
                    (occurred_at, ingested_at, source_id, workspace_id, 
                     event_type, event_version, payload, source_event_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id, source_event_id) DO NOTHING
                RETURNING id
                """,
                (
                    event.occurred_at,
                    None,  # ingested_at must be NULL it is set by a later procedure
                    event.source_id,
                    event.workspace_id,
                    event.event_type,
                    event.event_version,
                    json.dumps(payload_dict),
                    event.source_event_id,
                ),
            )
            result = cur.fetchone()
            if result:
                # result is a tuple, first element is the id (int)
                return int(result[0])
            # If result is None, the event already existed (ON CONFLICT DO NOTHING)
            return None

    def update_raw_event_source_checkpoint(
        self,
        source_id: int,
        update: RawEventSourceUpdate,
    ) -> None:
        """Update checkpoint fields in raw_event_source."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE cognition.raw_event_sources
                SET last_event_id = %s,
                    last_event_at = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    update.last_event_id,
                    update.last_event_at,
                    datetime.now(),
                    source_id,
                ),
            )
