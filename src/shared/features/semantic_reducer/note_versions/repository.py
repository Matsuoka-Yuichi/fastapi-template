"""Repository for note version reducer database operations."""

from psycopg import Connection
from psycopg.rows import dict_row

from shared.features.event_sourcing.models import NoteVersion


class NoteVersionRepository:
    """Repository for note version reducer operations."""

    def __init__(self, connection: Connection) -> None:
        """Initialize repository with a database connection."""
        self.conn = connection

    def get_prior_note_version(
        self, note_id: int, current_version: int
    ) -> NoteVersion | None:
        """Get the prior note version for a given note_id and current version.
        
        Returns the version immediately before current_version, or None if
        current_version is the first version.
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, note_id, version, created_at, title, text,
                       workspace_id, note_folder_id, similarity
                FROM public.note_versions
                WHERE note_id = %s AND version < %s
                ORDER BY version DESC
                LIMIT 1
                """,
                (note_id, current_version),
            )
            result = cur.fetchone()
            if result:
                return NoteVersion(**dict(result))
            return None
