"""Pydantic models for semantic reducer domain entities."""

import hashlib
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from shared.features.event_sourcing.enums import EventType


class SemanticEvent(BaseModel):
    """Model for semantic_events table."""

    id: int
    event_type: EventType
    workspace_id: int
    occurred_at: datetime
    created_at: datetime
    reducer_version: str
    raw_event_ids: list[int]
    payload: dict[str, Any]
    unique_hash: str

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SemanticEventCreate(BaseModel):
    """Model for creating a semantic event."""

    event_type: EventType
    workspace_id: int
    occurred_at: datetime
    reducer_version: str
    raw_event_ids: list[int]
    payload: dict[str, Any]
    unique_hash: str

    class Config:
        """Pydantic config."""

        use_enum_values = True


def compute_unique_hash(
    event_type: EventType | str,
    workspace_id: int,
    raw_event_ids: list[int],
    payload: dict[str, Any],
) -> str:
    """Compute unique hash for idempotency.
    
    The hash includes:
    - event_type (to prevent collisions across event types)
    - workspace_id (to scope uniqueness per workspace)
    - sorted raw_event_ids (the core identifier)
    - hash of payload content (to detect payload changes)
    
    Args:
        event_type: The type of event (EventType enum or string)
        workspace_id: The workspace ID
        raw_event_ids: List of raw event IDs (will be sorted)
        payload: The event payload dictionary
        
    Returns:
        SHA256 hex digest of combined components
    """
    # Get event_type as string (handle both enum and string)
    if isinstance(event_type, EventType):
        event_type_str = event_type.value
    else:
        event_type_str = str(event_type)
    
    # Sort raw_event_ids for consistent hashing
    sorted_ids = sorted(raw_event_ids)
    ids_str = ",".join(str(id) for id in sorted_ids)
    
    # Hash the payload content for change detection
    # Use sorted keys and json.dumps to ensure consistent serialization
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    
    # Combine all components
    combined = f"{event_type_str}|{workspace_id}|{ids_str}|{payload_hash}"
    
    # Return final hash
    return hashlib.sha256(combined.encode()).hexdigest()
