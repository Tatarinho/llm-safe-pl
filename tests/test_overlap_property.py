"""Property test: bisect-based ``_resolve_overlaps`` matches the naive O(n^2) reference.

The fast and slow algorithms must produce the same set of retained matches
for any input. Hypothesis generates random Match objects (varied spans,
varied detector names — i.e. varied priorities) and asserts equivalence.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import Mapping, Match, PIIType


def _naive_resolve(matches: list[Match], detectors: list) -> list[Match]:
    priority = {d.name: i for i, d in enumerate(detectors)}
    fallback = len(priority)

    def sort_key(m: Match) -> tuple[int, int, int]:
        return (-(m.end - m.start), m.start, priority.get(m.detector, fallback))

    def overlaps(a: Match, b: Match) -> bool:
        return a.start < b.end and b.start < a.end

    taken: list[Match] = []
    for m in sorted(matches, key=sort_key):
        if not any(overlaps(m, t) for t in taken):
            taken.append(m)
    return taken


_match_strategy = st.builds(
    lambda start, length, detector_idx: Match(
        type=PIIType.PESEL,
        value="x" * length,
        start=start,
        end=start + length,
        detector=f"d{detector_idx}",
    ),
    start=st.integers(min_value=0, max_value=200),
    length=st.integers(min_value=1, max_value=20),
    detector_idx=st.integers(min_value=0, max_value=4),
)


@given(st.lists(_match_strategy, max_size=80))
@settings(max_examples=200)
def test_bisect_matches_naive_on_arbitrary_match_sets(matches: list[Match]) -> None:
    detectors = [PeselDetector()]
    anon = Anonymizer(detectors=detectors, mapping=Mapping())

    actual = anon._resolve_overlaps(list(matches))
    expected = _naive_resolve(list(matches), detectors)

    actual_keys = sorted((m.start, m.end, m.detector) for m in actual)
    expected_keys = sorted((m.start, m.end, m.detector) for m in expected)
    assert actual_keys == expected_keys
