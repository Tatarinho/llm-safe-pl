"""llm-safe-pl — DEPRECATED. Use pii-veil + pii-core instead.

This package is end-of-life. The 0.2.1 release is a deprecation tombstone:
the API still works as it did in 0.2.0, but no further development or fixes
will be released. The successor is the pii-toolkit family on PyPI:

* pii-veil      — reversible anonymization for LLM workflows (Shield successor)
* pii-core      — multi-language detection and checksum validation
* pii-presidio  — Microsoft Presidio plugin

See MIGRATION.md for the full symbol map.
"""

import warnings
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from llm_safe_pl.errors import DetectorError, InputSizeError, LlmSafeError, MappingError
from llm_safe_pl.models import AnonymizeResult, Mapping, Match, PIIType
from llm_safe_pl.shield import Shield

warnings.warn(
    "llm-safe-pl is deprecated and will receive no further updates. "
    "Migrate to pii-veil (`pip install pii-veil`) for reversible anonymization "
    "and pii-core (`pip install pii-core`) for detectors. "
    "See https://github.com/Tatarinho/llm-safe-pl/blob/main/MIGRATION.md",
    DeprecationWarning,
    stacklevel=2,
)

try:
    __version__ = _version("llm-safe-pl")
except PackageNotFoundError:
    # Bare-clone import (PYTHONPATH=src python -c "import llm_safe_pl") without
    # an editable install lacks distribution metadata. Use a sentinel so import
    # succeeds in dev workflows that haven't run `pip install -e .` yet.
    __version__ = "0.0.0+local"

__all__ = [
    "AnonymizeResult",
    "DetectorError",
    "InputSizeError",
    "LlmSafeError",
    "Mapping",
    "MappingError",
    "Match",
    "PIIType",
    "Shield",
]
