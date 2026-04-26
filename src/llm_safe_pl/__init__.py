"""llm-safe-pl — reversible PII anonymization for Polish documents.

Public API surface is intentionally small. Anything not listed in ``__all__`` is an
implementation detail and may change without a major version bump.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from llm_safe_pl.models import AnonymizeResult, Mapping, Match, PIIType
from llm_safe_pl.shield import Shield

try:
    __version__ = _version("llm-safe-pl")
except PackageNotFoundError:
    # Bare-clone import (PYTHONPATH=src python -c "import llm_safe_pl") without
    # an editable install lacks distribution metadata. Use a sentinel so import
    # succeeds in dev workflows that haven't run `pip install -e .` yet.
    __version__ = "0.0.0+local"

__all__ = [
    "AnonymizeResult",
    "Mapping",
    "Match",
    "PIIType",
    "Shield",
]
