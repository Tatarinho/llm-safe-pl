"""NIP detector: 10 digits with optional dash/space separators, checksum-validated.

Common Polish NIP formats in real documents:
    1234567890, 123-456-78-90, 123 456 78 90, 123-45-67-890

The regex matches any of these; ``Match.value`` preserves the original
formatting so deanonymization restores the source text exactly. The
validator is called on a digits-only view of the match.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators import is_valid_nip

_SEPARATOR = re.compile(r"[-\s]")


class NipDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.NIP
    name: ClassVar[str] = "nip"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}\b")

    def _is_valid(self, candidate: str) -> bool:
        return is_valid_nip(_SEPARATOR.sub("", candidate))
