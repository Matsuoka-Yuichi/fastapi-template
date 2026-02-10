"""Enums for note versions reducer."""

from enum import Enum


class NoteVersionReducerVersion(str, Enum):
    """Version identifiers for note version reducer logic."""

    V1_0_0 = "1.0.0"