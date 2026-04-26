"""Typed exception hierarchy for llm-safe-pl.

All library errors descend from :class:`LlmSafeError`. Specific subclasses also
inherit from a relevant builtin (``ValueError`` for input/data errors,
``RuntimeError`` for dispatch failures) so legacy ``except ValueError`` code
keeps catching them.

:class:`DetectorError` deliberately does NOT accept the original text or an
exception cause — both can carry PII. The class signature is exactly
``(detector_name)``; raise it via ``raise DetectorError(name) from None`` to
suppress the implicit cause chain.
"""

from __future__ import annotations


class LlmSafeError(Exception):
    """Base class for all llm-safe-pl errors."""


class MappingError(LlmSafeError, ValueError):
    """Raised when a Mapping fails validation (e.g. ``Mapping.from_dict``)."""


class InputSizeError(LlmSafeError, ValueError):
    """Raised when input exceeds ``Shield(max_input_bytes=...)``."""


class DetectorError(LlmSafeError, RuntimeError):
    """Raised when a detector fails. Original text and cause are not attached."""

    def __init__(self, detector_name: str) -> None:
        super().__init__(f"detector {detector_name!r} failed")
        self.detector_name = detector_name
