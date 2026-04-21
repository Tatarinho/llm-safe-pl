"""Polish IBAN detector: ``PL`` prefix, 28 total chars (bare or grouped-by-4).

Both bare (``PL61109010140000071219812874``) and spaced
(``PL61 1090 1014 0000 0712 1981 2874``) forms match. The Match.value
preserves whatever form was in the source text; the validator is called on
a whitespace-stripped view.
"""

from __future__ import annotations

import re
from typing import ClassVar

from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.models import PIIType
from llm_safe_pl.validators import is_valid_iban


class IbanDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.IBAN
    name: ClassVar[str] = "iban"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"\bPL\d{26}\b|\bPL\d{2}(?:\s\d{4}){6}\b")

    def _is_valid(self, candidate: str) -> bool:
        return is_valid_iban("".join(candidate.split()))
