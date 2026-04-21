"""Polish passport detector: 2 uppercase letters + 7 digits.

As with ID card, the official checksum (weighted letter-to-number) is not
implemented in v0.1 — the detector is regex-only for now.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType


class PassportDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PASSPORT
    name: ClassVar[str] = "passport"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b[A-Z]{2}\d{7}\b")
