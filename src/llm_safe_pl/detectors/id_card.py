"""Polish ID card (dowód osobisty) detector: 3 uppercase letters + 6 digits.

No checksum validation in v0.1 — the official dowód-osobisty checksum is a
weighted letter-to-number scheme that is not yet implemented in the validators
package. Adding it is a later enhancement.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType


class IdCardDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.ID_CARD
    name: ClassVar[str] = "id_card"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\b[A-Z]{3}\d{6}\b")
