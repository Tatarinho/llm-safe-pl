"""Shield — the library's main public-facing facade.

A Shield instance owns a single Mapping that accumulates tokens across every
``anonymize()`` call, so the same value always maps to the same token within
the lifetime of that Shield. Users wanting isolation between documents should
instantiate a new Shield per document, or call :meth:`Shield.reset` to drop
accumulated state. Custom detector lists and a preloaded Mapping can be
supplied to the constructor.

Thread safety: a single Shield is NOT thread-safe. ``Mapping.token_for``
mutates state without locking, so concurrent ``anonymize`` calls on the same
Shield can race. Use one Shield per request/thread, or serialize calls
externally.

Cross-document leakage: because the Mapping persists across calls, feeding
attacker-controlled text containing literal token shapes (e.g. ``[PESEL_001]``)
through ``deanonymize`` on a Shield that previously processed sensitive text
will substitute the attacker's token with the prior value. Always create a
fresh Shield (or call ``reset()``) before processing untrusted text.
"""

from __future__ import annotations

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.deanonymizer import Deanonymizer
from llm_safe_pl.detectors import DEFAULT_DETECTORS
from llm_safe_pl.detectors.base import Detector
from llm_safe_pl.errors import InputSizeError
from llm_safe_pl.models import AnonymizeResult, Mapping, Match
from llm_safe_pl.strategies import Strategy


class Shield:
    """Orchestrates the full anonymize/deanonymize round-trip.

    Args:
        detectors: Custom detector list (default: ``DEFAULT_DETECTORS``).
        mapping: Preloaded Mapping (default: empty Mapping).
        strategy: Anonymization strategy (only ``TOKEN`` in v0.1).
        max_input_bytes: If set, ``anonymize``/``detect`` raise
            :class:`~llm_safe_pl.errors.InputSizeError` for inputs whose UTF-8
            byte length exceeds this. ``InputSizeError`` subclasses
            ``ValueError`` so existing ``except ValueError`` code keeps
            catching it. Default ``None`` (unlimited). Recommended for
            hardened pipelines that ingest untrusted text — ``Shield.anonymize``
            allocates O(n) memory in input size, so an unbounded input is a
            DoS vector.
    """

    def __init__(
        self,
        detectors: list[Detector] | None = None,
        mapping: Mapping | None = None,
        strategy: Strategy = Strategy.TOKEN,
        max_input_bytes: int | None = None,
    ) -> None:
        self._mapping = mapping if mapping is not None else Mapping()
        self._detectors = list(detectors) if detectors is not None else list(DEFAULT_DETECTORS)
        self._anonymizer = Anonymizer(
            detectors=self._detectors,
            mapping=self._mapping,
            strategy=strategy,
        )
        self._deanonymizer = Deanonymizer()
        if max_input_bytes is not None and max_input_bytes < 0:
            raise ValueError(f"max_input_bytes must be non-negative, got {max_input_bytes}")
        self._max_input_bytes = max_input_bytes

    @property
    def mapping(self) -> Mapping:
        return self._mapping

    def reset(self) -> None:
        """Discard the accumulated Mapping; counters and entries reset to empty.

        Use between unrelated documents/users to prevent cross-document token
        leakage. Detector list and other Shield configuration are preserved.
        """
        self._mapping = Mapping()
        self._anonymizer = Anonymizer(
            detectors=self._detectors,
            mapping=self._mapping,
            strategy=self._anonymizer._strategy,
        )

    def _check_input_size(self, text: str) -> None:
        if self._max_input_bytes is None:
            return
        size = len(text.encode("utf-8"))
        if size > self._max_input_bytes:
            raise InputSizeError(f"input is {size} bytes; max_input_bytes={self._max_input_bytes}")

    def anonymize(self, text: str) -> AnonymizeResult:
        self._check_input_size(text)
        return self._anonymizer.anonymize(text)

    def deanonymize(self, text: str, mapping: Mapping | None = None) -> str:
        return self._deanonymizer.deanonymize(
            text, mapping if mapping is not None else self._mapping
        )

    def detect(self, text: str) -> tuple[Match, ...]:
        self._check_input_size(text)
        matches = self._anonymizer.detect(text)
        return tuple(sorted(matches, key=lambda m: m.start))
