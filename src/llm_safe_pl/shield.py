"""Shield — the library's main public-facing facade.

A Shield instance owns a single Mapping that accumulates tokens across every
``anonymize()`` call, so the same value always maps to the same token within
the lifetime of that Shield. Users wanting isolation between documents should
instantiate a new Shield per document. Custom detector lists and a
preloaded Mapping can be supplied to the constructor.
"""

from __future__ import annotations

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.deanonymizer import Deanonymizer
from llm_safe_pl.detectors import DEFAULT_DETECTORS
from llm_safe_pl.detectors.base import Detector
from llm_safe_pl.models import AnonymizeResult, Mapping, Match
from llm_safe_pl.strategies import Strategy


class Shield:
    """Orchestrates the full anonymize/deanonymize round-trip."""

    def __init__(
        self,
        detectors: list[Detector] | None = None,
        mapping: Mapping | None = None,
        strategy: Strategy = Strategy.TOKEN,
    ) -> None:
        self._mapping = mapping if mapping is not None else Mapping()
        self._detectors = list(detectors) if detectors is not None else list(DEFAULT_DETECTORS)
        self._anonymizer = Anonymizer(
            detectors=self._detectors,
            mapping=self._mapping,
            strategy=strategy,
        )
        self._deanonymizer = Deanonymizer()

    @property
    def mapping(self) -> Mapping:
        return self._mapping

    def anonymize(self, text: str) -> AnonymizeResult:
        return self._anonymizer.anonymize(text)

    def deanonymize(self, text: str, mapping: Mapping | None = None) -> str:
        return self._deanonymizer.deanonymize(
            text, mapping if mapping is not None else self._mapping
        )

    def detect(self, text: str) -> tuple[Match, ...]:
        matches = self._anonymizer.detect(text)
        return tuple(sorted(matches, key=lambda m: m.start))
