"""Pydantic models for event sourcing domain entities."""

from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from shared.features.event_sourcing.enums import (
    EventType,
    SourceSystem,
    SourceType,
)

# Type variable for payload types - constrained to BaseModel subclasses
PayloadT = TypeVar("PayloadT", bound=BaseModel)


class RawEventSource(BaseModel):
    """Model for raw event source checkpoint."""

    id: int
    source_type: SourceType
    source_system: SourceSystem
    last_event_id: str = Field(default="")
    last_event_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class RawEventSourceUpdate(BaseModel):
    """Model for updating a raw event source checkpoint."""

    last_event_id: str
    last_event_at: datetime

    class Config:
        """Pydantic config."""

        use_enum_values = True


class RawEvent(BaseModel):
    """Model for raw event."""

    id: int
    occurred_at: datetime
    ingested_at: datetime | None = None
    source_id: int
    workspace_id: int
    event_type: EventType
    event_version: int
    payload: dict[str, Any]
    source_event_id: str

    class Config:
        """Pydantic config."""

        use_enum_values = True


class RawEventCreate[PayloadT](BaseModel):
    """Generic model for creating a raw event with type-safe payload.

    Usage:
        # Type-safe version
        event = RawEventCreate[NoteVersionCreatedPayload](
            event_type=EventType.NOTE_VERSION_CREATED,
            payload=NoteVersionCreatedPayload(...),
            source_event_id="unique-id-from-source",
            ...
        )

        # Or use type alias
        event: NoteVersionCreatedEvent = NoteVersionCreatedEvent(...)
    """

    source_id: int
    workspace_id: int
    event_type: EventType
    event_version: int
    payload: PayloadT
    occurred_at: datetime
    source_event_id: str
    ingested_at: datetime | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class NoteVersion(BaseModel):
    """Model for note version from source system."""

    id: int
    note_id: int
    version: int
    created_at: datetime
    title: str | None = None
    text: str
    workspace_id: int
    note_folder_id: int | None = None
    similarity: float | None = None
