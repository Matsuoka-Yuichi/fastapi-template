"""Repository for semantic reducer database operations."""

import json
from datetime import datetime

from psycopg import Connection
from psycopg.rows import dict_row

from shared.features.event_sourcing.models import RawEvent  # cross feature import !!
from shared.features.semantic_reducer.models import SemanticEventCreate


class SemanticReducerRepository:
    """Repository for semantic reducer operations."""

    def __init__(self, connection: Connection) -> None:
        """Initialize repository with a database connection."""
        self.conn = connection

    def get_raw_event_by_id(self, raw_event_id: int) -> RawEvent | None:
        """Get a raw event by its ID."""
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, occurred_at, ingested_at, source_id, workspace_id,
                       event_type, event_version, payload, source_event_id
                FROM cognition.raw_events
                WHERE id = %s
                """,
                (raw_event_id,),
            )
            result = cur.fetchone()
            if result:
                return RawEvent(**dict(result))
            return None

    def get_raw_events_by_ids(self, raw_event_ids: list[int]) -> list[RawEvent]:
        """Get multiple raw events by their IDs."""
        if not raw_event_ids:
            return []
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, occurred_at, ingested_at, source_id, workspace_id,
                       event_type, event_version, payload, source_event_id
                FROM cognition.raw_events
                WHERE id = ANY(%s)
                """,
                (raw_event_ids,),
            )
            results = cur.fetchall()
            return [RawEvent(**dict(row)) for row in results]

    def get_unprocessed_raw_events(self, limit: int = 100) -> list[RawEvent]:
        """Get raw events that haven't been processed yet (ingested_at IS NULL)."""
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, occurred_at, ingested_at, source_id, workspace_id,
                       event_type, event_version, payload, source_event_id
                FROM cognition.raw_events
                WHERE ingested_at IS NULL
                ORDER BY id ASC
                LIMIT %s
                """,
                (limit,),
            )
            results = cur.fetchall()
            return [RawEvent(**dict(row)) for row in results]

    def create_semantic_event(
        self, event: SemanticEventCreate
    ) -> int | None:
        """Create a semantic event, returning its id.
        
        Uses ON CONFLICT DO NOTHING for idempotency. Returns None if the event
        already exists (conflict on unique_hash).
        
        Args:
            event: The semantic event to create
            
        Returns:
            ID (int) of the created event, or None if it already existed
        """
        # Get event_type as string (handle both enum and string)
        from shared.features.event_sourcing.enums import EventType
        
        if isinstance(event.event_type, EventType):
            event_type_str = event.event_type.value
        else:
            event_type_str = str(event.event_type)
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cognition.semantic_events
                    (event_type, workspace_id, occurred_at, reducer_version,
                     raw_event_ids, payload, unique_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (unique_hash) DO NOTHING
                RETURNING id
                """,
                (
                    event_type_str,
                    event.workspace_id,
                    event.occurred_at,
                    event.reducer_version,
                    event.raw_event_ids,
                    json.dumps(event.payload),
                    event.unique_hash,
                ),
            )
            result = cur.fetchone()
            if result:
                # result[0] is the integer ID from PostgreSQL
                return int(result[0])
            # If result is None, the event already existed (ON CONFLICT DO NOTHING)
            return None

    def update_raw_events_ingested_at(
        self, raw_event_ids: list[int], ingested_at: datetime
    ) -> None:
        """Update ingested_at timestamp for multiple raw events."""
        if not raw_event_ids:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE cognition.raw_events
                SET ingested_at = %s
                WHERE id = ANY(%s)
                """,
                (ingested_at, raw_event_ids),
            )
