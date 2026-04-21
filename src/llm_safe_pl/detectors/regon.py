"""REGON detector: either 9 or 14 consecutive digits, checksum-validated.

The 14-digit alternative is tried first so a 14-digit REGON is captured whole
rather than being mistaken for a 9-digit prefix.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators import is_valid_regon


class RegonDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.REGON
    name: ClassVar[str] = "regon"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{14}\b|\b\d{9}\b")

    def _is_valid(self, candidate: str) -> bool:
        return is_valid_regon(candidate)
