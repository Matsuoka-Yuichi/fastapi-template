"""Reducer for processing note version events."""

import difflib
import logging

from shared.features.event_sourcing.models import NoteVersion, RawEvent
from shared.features.semantic_reducer.models import SemanticEventCreate, compute_unique_hash
from shared.features.semantic_reducer.note_versions.enums import NoteVersionReducerVersion
from shared.features.semantic_reducer.note_versions.models import (
    EnrichedNoteVersionPayload,
)
from shared.features.semantic_reducer.note_versions.repository import (
    NoteVersionRepository,
)

logger = logging.getLogger(__name__)


class NoteVersionReducer:
    """Reducer for NOTE_VERSION_CREATED events."""

    reducer_version: str = NoteVersionReducerVersion.V1_0_0.value

    def reduce(
        self, raw_event: RawEvent, note_version_repo: NoteVersionRepository
    ) -> SemanticEventCreate:
        """Reduce a NOTE_VERSION_CREATED event into a SemanticEventCreate.
        
        Args:
            raw_event: The raw event containing NoteVersion payload
            note_version_repo: Repository for note version operations
            
        Returns:
            SemanticEventCreate object ready to be inserted
        """
        # Parse the NoteVersion from payload
        note_version = NoteVersion(**raw_event.payload)

        # Fetch prior version
        prior_version = note_version_repo.get_prior_note_version(
            note_version.note_id, note_version.version
        )

        # Compute diff
        if prior_version is not None:
            diff = self._compute_diff(prior_version.text, note_version.text)
        else:
            # First version - no prior version to compare
            diff = ""

        # Create enriched payload
        enriched = EnrichedNoteVersionPayload(
            id=note_version.id,
            note_id=note_version.note_id,
            version=note_version.version,
            created_at=note_version.created_at,
            title=note_version.title,
            text=note_version.text,
            workspace_id=note_version.workspace_id,
            note_folder_id=note_version.note_folder_id,
            similarity=note_version.similarity,
            diff=diff,
        )

        enriched_payload = enriched.model_dump(mode="json")

        # Compute unique hash
        raw_event_ids = [raw_event.id]
        unique_hash = compute_unique_hash(
            raw_event.event_type,
            raw_event.workspace_id,
            raw_event_ids,
            enriched_payload,
        )

        # Create and return SemanticEventCreate
        return SemanticEventCreate(
            event_type=raw_event.event_type,
            workspace_id=raw_event.workspace_id,
            occurred_at=raw_event.occurred_at,
            reducer_version=self.reducer_version,
            raw_event_ids=raw_event_ids,
            payload=enriched_payload,
            unique_hash=unique_hash,
        )

    def _compute_diff(self, prior_text: str, current_text: str) -> str:
        """Compute unified diff between prior and current text.
        
        Args:
            prior_text: The previous version text
            current_text: The current version text
            
        Returns:
            Unified diff string in GitHub-like format
        """
        prior_lines = prior_text.splitlines(keepends=True)
        current_lines = current_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            prior_lines,
            current_lines,
            fromfile="previous",
            tofile="current",
            lineterm="",
            n=3,  # Context lines
        )

        return "".join(diff)
