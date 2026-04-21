"""llm-safe-pl — reversible PII anonymization for Polish documents.

Public API surface is intentionally small. Anything not listed in ``__all__`` is an
implementation detail and may change without a major version bump.
"""

from llm_safe_pl.models import AnonymizeResult, Mapping, Match, PIIType
from llm_safe_pl.shield import Shield

__version__ = "0.1.0"

__all__ = [
    "AnonymizeResult",
    "Mapping",
    "Match",
    "PIIType",
    "Shield",
]
