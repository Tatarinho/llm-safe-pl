"""Polish mobile phone number detector.

Matches 9-digit phone numbers with an optional ``+48`` country prefix and
optional dash/space separators between 3-digit groups. Lookbehind and
lookahead prevent matching a 9-digit subsequence inside a longer digit run.

Scope note: v0.1 targets mobile numbers. Landlines written with area-code
parentheses (e.g. ``(22) 123-45-67``) are out of scope for this regex.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType


class PhoneDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PHONE
    name: ClassVar[str] = "phone"
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<!\d)(?:\+48[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{3}(?!\d)"
    )
