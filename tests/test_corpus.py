"""Regression tests against the labeled PII corpus under ``tests/corpora/``.

The corpus is the ground truth for detector precision/recall as detector
coverage grows. Adding more samples to ``pl_pii_positive/`` and
``pl_pii_negative/`` strengthens regression coverage without changing test
code: the fixtures in this module discover ``.txt``/``.json`` pairs at
collection time.

Format:

- ``pl_pii_positive/<name>.txt`` — source text
- ``pl_pii_positive/<name>.json`` — list of ``{type, start, end, value}``
  objects covering the labeled spans (must not overlap)
- ``pl_pii_negative/<name>.txt`` — source text
- ``pl_pii_negative/<name>.json`` — empty list (or omit the file)

The loader is kept inline rather than in a separate module to avoid the
sys.path gymnastics of cross-test imports; if a future test needs to reuse
the loader, lift it to a shared package then.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import pytest

from llm_safe_pl import Shield

_CORPORA_ROOT = Path(__file__).parent / "corpora"


@dataclass(frozen=True)
class ExpectedSpan:
    type: str
    start: int
    end: int
    value: str


@dataclass(frozen=True)
class CorpusSample:
    name: str
    text: str
    spans: tuple[ExpectedSpan, ...]


def _check_no_overlap(spans: tuple[ExpectedSpan, ...], *, sample: str) -> None:
    sorted_spans = sorted(spans, key=lambda s: s.start)
    for a, b in pairwise(sorted_spans):
        if a.end > b.start:
            raise ValueError(
                f"corpus sample {sample!r}: labels overlap "
                f"({a.type}@{a.start}-{a.end} vs {b.type}@{b.start}-{b.end})"
            )


def _load_directory(name: str) -> Iterator[CorpusSample]:
    directory = _CORPORA_ROOT / name
    if not directory.is_dir():
        raise FileNotFoundError(f"corpus directory not found: {directory}")
    for txt_path in sorted(directory.glob("*.txt")):
        text = txt_path.read_text(encoding="utf-8")
        json_path = txt_path.with_suffix(".json")
        if json_path.is_file():
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            spans = tuple(
                ExpectedSpan(type=e["type"], start=e["start"], end=e["end"], value=e["value"])
                for e in raw
            )
            _check_no_overlap(spans, sample=txt_path.name)
        else:
            spans = ()
        yield CorpusSample(name=txt_path.stem, text=text, spans=spans)


_POSITIVE_SAMPLES = list(_load_directory("pl_pii_positive"))
_NEGATIVE_SAMPLES = list(_load_directory("pl_pii_negative"))


class TestLoader:
    def test_positive_corpus_not_empty(self) -> None:
        assert len(_POSITIVE_SAMPLES) >= 1, "positive corpus must not be empty"

    def test_negative_corpus_not_empty(self) -> None:
        assert len(_NEGATIVE_SAMPLES) >= 1, "negative corpus must not be empty"

    def test_positive_samples_have_text(self) -> None:
        for s in _POSITIVE_SAMPLES:
            assert s.text, f"sample {s.name} has empty text"

    def test_positive_samples_have_spans(self) -> None:
        for s in _POSITIVE_SAMPLES:
            assert s.spans, f"positive sample {s.name} has no labeled spans"

    def test_overlap_detection_rejects_overlapping_labels(self) -> None:
        spans = (
            ExpectedSpan(type="T", start=0, end=3, value="abc"),
            ExpectedSpan(type="T", start=2, end=5, value="cde"),
        )
        with pytest.raises(ValueError, match="overlap"):
            _check_no_overlap(spans, sample="x.txt")

    def test_overlap_detection_allows_adjacent_labels(self) -> None:
        spans = (
            ExpectedSpan(type="T", start=0, end=3, value="abc"),
            ExpectedSpan(type="T", start=3, end=6, value="def"),
        )
        # Adjacent (a.end == b.start) is fine.
        _check_no_overlap(spans, sample="x.txt")

    def test_label_values_match_text_substrings(self) -> None:
        for s in _POSITIVE_SAMPLES:
            for span in s.spans:
                assert s.text[span.start : span.end] == span.value, (
                    f"sample {s.name}: label {span} does not match "
                    f"text[{span.start}:{span.end}]={s.text[span.start : span.end]!r}"
                )


class TestPositiveCorpus:
    @pytest.mark.parametrize(
        "sample",
        _POSITIVE_SAMPLES,
        ids=lambda s: s.name,
    )
    def test_default_shield_finds_labeled_spans(self, sample: CorpusSample) -> None:
        shield = Shield()
        result = shield.detect(sample.text)
        actual = {(m.start, m.end, m.type.value) for m in result}
        expected = {(s.start, s.end, s.type) for s in sample.spans}
        assert expected.issubset(actual), (
            f"sample {sample.name}: missing labeled spans {expected - actual}; got {actual}"
        )


class TestNegativeCorpus:
    @pytest.mark.parametrize(
        "sample",
        _NEGATIVE_SAMPLES,
        ids=lambda s: s.name,
    )
    def test_default_shield_finds_no_matches(self, sample: CorpusSample) -> None:
        shield = Shield()
        result = shield.detect(sample.text)
        assert len(result) == 0, (
            f"sample {sample.name}: expected zero matches, got "
            f"{[(m.start, m.end, m.type.value, m.value) for m in result]}"
        )
