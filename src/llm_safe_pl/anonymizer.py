"""Orchestrator: run detectors, resolve overlaps, replace PII with tokens.

The overlap policy is "longest match wins, priority tiebreaks": when two
detectors produce overlapping spans, the longer one is kept; on identical
spans the detector that appears earlier in the ``detectors`` list wins. This
matches user intuition (capture more PII, not less) and lets Shield carry a
stable priority via ``DEFAULT_DETECTORS`` order.
"""

from __future__ import annotations

from bisect import bisect_left

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
        # Detector names participate in the overlap-resolution priority dict
        # below; duplicates would silently overwrite, breaking determinism.
        seen_names: set[str] = set()
        for d in detectors:
            if d.name in seen_names:
                raise ValueError(f"Duplicate detector name: {d.name!r}")
            seen_names.add(d.name)
        self._detectors = detectors
        self._mapping = mapping
        # Strategy is stored ready for future MASK/FAKE dispatch. v0.1 only
        # implements TOKEN; passing anything else is reserved for future use
        # rather than silently dropped.
        if strategy is not Strategy.TOKEN:
            raise ValueError(f"Strategy {strategy!r} not implemented in v0.1")
        self._strategy = strategy
        # Cached once at construction — detectors are immutable for the
        # Anonymizer's lifetime, so the priority map is too.
        self._priority: dict[str, int] = {d.name: i for i, d in enumerate(detectors)}
        self._priority_fallback = len(self._priority)

    def detect(self, text: str) -> list[Match]:
        """Find all PII matches with overlaps resolved, without mutating Mapping.

        Returns a fresh ``list[Match]`` for performance — internal callers can
        sort in place. The public-facing immutable view is ``Shield.detect``,
        which wraps this result in a tuple. Treat the returned list as
        read-only unless you own the Anonymizer instance.
        """
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
        priority = self._priority
        fallback = self._priority_fallback

        def sort_key(m: Match) -> tuple[int, int, int]:
            length = m.end - m.start
            return (-length, m.start, priority.get(m.detector, fallback))

        # Invariant: ``taken`` stays sorted by start and pairwise non-overlapping.
        # A new candidate can only overlap its left or right neighbor in start order,
        # so a single bisect lookup checks both. Replaces an O(n^2) linear scan that
        # dominated runtime on documents with thousands of PII items.
        taken: list[Match] = []
        starts: list[int] = []
        for m in sorted(matches, key=sort_key):
            i = bisect_left(starts, m.start)
            if i > 0 and taken[i - 1].end > m.start:
                continue
            if i < len(taken) and taken[i].start < m.end:
                continue
            starts.insert(i, m.start)
            taken.insert(i, m)
        return taken


def _overlaps(a: Match, b: Match) -> bool:
    return a.start < b.end and b.start < a.end
