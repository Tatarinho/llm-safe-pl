"""Credit card number detector (Luhn-validated).

Matches three shapes:
- Bare 13-19 digit runs (covers Visa/MC 16, Amex 15 bare, Diners 14 bare).
- 4-4-4-N grouping with dash or space separators (standard Visa/MC layout).
- 4-6-5 grouping (Amex layout).

Match.value keeps the source formatting; the Luhn validator is called on a
digits-only view so deanonymization reproduces the original spacing.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators import is_valid_luhn

_NON_DIGIT = re.compile(r"\D")


class CreditCardDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.CREDIT_CARD
    name: ClassVar[str] = "credit_card"
    pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:"
        r"\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{1,7}"
        r"|\d{4}[-\s]\d{6}[-\s]\d{5}"
        r"|\d{13,19}"
        r")\b"
    )

    def _is_valid(self, candidate: str) -> bool:
        return is_valid_luhn(_NON_DIGIT.sub("", candidate))
