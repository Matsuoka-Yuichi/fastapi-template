"""Models for note version semantic reduction."""

from datetime import datetime

from pydantic import BaseModel


class EnrichedNoteVersionPayload(BaseModel):
    """Extended NoteVersion payload with diff information."""

    # Original NoteVersion fields
    id: int
    note_id: int
    version: int
    created_at: datetime
    title: str | None = None
    text: str
    workspace_id: int
    note_folder_id: int | None = None
    similarity: float | None = None

    # Enrichment fields
    diff: str  # Unified diff string comparing with prior version
