"""Email address detector.

Uses a practical subset regex rather than strict RFC 5322 — full RFC compliance
doubles the regex size for marginal gain on real-world documents.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType


class EmailDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "email"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
