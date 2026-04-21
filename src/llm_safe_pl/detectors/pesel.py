"""PESEL detector: 11 digits, word-bounded, checksum-validated."""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators import is_valid_pesel


class PeselDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PESEL
    name: ClassVar[str] = "pesel"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{11}\b")

    def _is_valid(self, candidate: str) -> bool:
        return is_valid_pesel(candidate)
