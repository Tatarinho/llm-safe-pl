"""Abstract base classes for PII detectors.

``Detector`` defines the contract: given a text blob, produce zero or more
``Match`` objects. ``RegexDetector`` is a concrete helper for the common case
where detection is a regex scan followed by an optional checksum check.
Concrete detectors declare ``pii_type``, ``name``, and ``pattern`` as class
attributes, then optionally override ``_is_valid`` to plug in a validator from
``llm_safe_pl.validators``.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, ClassVar

from llm_safe_pl.models import Match, PIIType


class Detector(ABC):
    """Abstract base: detectors emit Match objects for PII in raw text."""

    pii_type: ClassVar[PIIType]
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Subclasses must declare ``pii_type`` and ``name``. ABC's
        # ``@abstractmethod`` only enforces missing methods, not missing
        # class variables — without this check, a subclass that forgets
        # ``name`` would instantiate fine and crash at first ``detect``
        # call. Caught at class-definition time instead.
        if cls.__name__ in {"RegexDetector"}:
            return  # the abstract regex helper isn't a concrete detector
        for required in ("pii_type", "name"):
            if not hasattr(cls, required):
                raise TypeError(f"{cls.__name__} must define class variable {required!r}")

    @abstractmethod
    def detect(self, text: str) -> Iterator[Match]:
        """Yield every PII occurrence found in ``text``."""


class RegexDetector(Detector):
    """Detector driven by a regex plus an optional checksum hook.

    Subclasses must set ``pii_type``, ``name``, and ``pattern``. They may
    override ``_is_valid`` to reject candidates that the regex accepted but
    that fail a checksum (e.g. PESEL weighted-sum). The default hook accepts
    every regex match.
    """

    pattern: ClassVar[re.Pattern[str]]

    def detect(self, text: str) -> Iterator[Match]:
        for m in self.pattern.finditer(text):
            candidate = m.group(0)
            if self._is_valid(candidate):
                yield Match(
                    type=self.pii_type,
                    value=candidate,
                    start=m.start(),
                    end=m.end(),
                    detector=self.name,
                )

    def _is_valid(self, candidate: str) -> bool:
        return True
