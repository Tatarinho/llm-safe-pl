"""Orchestrator: run detectors, resolve overlaps, replace PII with tokens.

The overlap policy is "longest match wins, priority tiebreaks": when two
detectors produce overlapping spans, the longer one is kept; on identical
spans the detector that appears earlier in the ``detectors`` list wins. This
matches user intuition (capture more PII, not less) and lets Shield carry a
stable priority via ``DEFAULT_DETECTORS`` order.
"""

from __future__ import annotations

from llm_safe_pl.detectors.base import Detector
from llm_safe_pl.models import AnonymizeResult, Mapping, Match
from llm_safe_pl.strategies import Strategy


class Anonymizer:
    """Replace detected PII in text with Mapping-allocated tokens."""

    def __init__(
        self,
        detectors: list[Detector],
        mapping: Mapping,
        strategy: Strategy = Strategy.TOKEN,
    ) -> None:
        self._detectors = detectors
        self._mapping = mapping

    def detect(self, text: str) -> list[Match]:
        """Find all PII matches with overlaps resolved, without mutating Mapping."""
        all_matches: list[Match] = []
        for detector in self._detectors:
            all_matches.extend(detector.detect(text))
        return self._resolve_overlaps(all_matches)

    def anonymize(self, text: str) -> AnonymizeResult:
        selected = self.detect(text)
        selected.sort(key=lambda m: m.start)

        parts: list[str] = []
        cursor = 0
        for m in selected:
            parts.append(text[cursor : m.start])
            parts.append(self._mapping.token_for(m.value, m.type))
            cursor = m.end
        parts.append(text[cursor:])

        return AnonymizeResult(
            text="".join(parts),
            mapping=self._mapping,
            matches=tuple(selected),
        )

    def _resolve_overlaps(self, matches: list[Match]) -> list[Match]:
        priority = {d.name: i for i, d in enumerate(self._detectors)}
        fallback = len(priority)

        def sort_key(m: Match) -> tuple[int, int, int]:
            length = m.end - m.start
            return (-length, m.start, priority.get(m.detector, fallback))

        taken: list[Match] = []
        for m in sorted(matches, key=sort_key):
            if not any(_overlaps(m, t) for t in taken):
                taken.append(m)
        return taken


def _overlaps(a: Match, b: Match) -> bool:
    return a.start < b.end and b.start < a.end
