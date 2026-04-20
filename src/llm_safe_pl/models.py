"""Data model placeholders. Real definitions land in Phase 1."""

from enum import Enum


class PIIType(Enum):
    """Placeholder enum. Real members are defined in Phase 1."""

    UNSPECIFIED = "unspecified"


class Match:
    """Placeholder. Real definition (type, value, span, ...) lands in Phase 1."""


class Mapping:
    """Placeholder. Real definition (bidirectional store, JSON IO) lands in Phase 1."""


class AnonymizeResult:
    """Placeholder. Real definition (text, mapping, matches) lands in Phase 1."""
