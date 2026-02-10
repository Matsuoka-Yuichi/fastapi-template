"""Type-safe enums for event sourcing."""

from enum import Enum


class ScopeType(str, Enum):
    """Scope types for event sourcing checkpoints."""

    NOTE_VERSION = "note_version"


class SourceType(str, Enum):
    """Source types for raw event sources."""

    COGNO_NOTE_VERSIONS = "cogno.note_versions"


class SourceSystem(str, Enum):
    """Source systems for raw event sources."""

    COGNO = "cogno"


class EventType(str, Enum):
    """Event types for raw events."""

    NOTE_VERSION_CREATED = "note_version.created"
