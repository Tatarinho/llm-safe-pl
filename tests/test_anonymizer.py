"""Tests for the Anonymizer orchestrator."""

import re
from typing import ClassVar

import pytest

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.detectors.email import EmailDetector
from llm_safe_pl.detectors.nip import NipDetector
from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import AnonymizeResult, Mapping, PIIType
from llm_safe_pl.strategies import Strategy


class _XxxDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "xxx"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"XXX")


class _XxxAliasDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PESEL
    name: ClassVar[str] = "xxx_alias"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"XXX")


class _ShortAbcDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "short"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"ABC")


class _LongAbcdefDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PESEL
    name: ClassVar[str] = "long"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"ABCDEF")


class _AaaDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.EMAIL
    name: ClassVar[str] = "aaa"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"A+")


class _BbbDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PESEL
    name: ClassVar[str] = "bbb"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"B+")


class TestAnonymizerBasic:
    def test_empty_detector_list_passes_text_through(self) -> None:
        anon = Anonymizer(detectors=[], mapping=Mapping())
        result = anon.anonymize("hello world")
        assert result.text == "hello world"
        assert result.matches == ()

    def test_empty_text_returns_empty(self) -> None:
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize("")
        assert result.text == ""
        assert result.matches == ()

    def test_replaces_single_pesel(self) -> None:
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize("PESEL: 44051401359.")
        assert result.text == "PESEL: [PESEL_001]."
        assert len(result.matches) == 1
        assert result.matches[0].value == "44051401359"
        assert result.matches[0].type is PIIType.PESEL

    def test_replaces_multiple_types(self) -> None:
        anon = Anonymizer(
            detectors=[PeselDetector(), EmailDetector()],
            mapping=Mapping(),
        )
        result = anon.anonymize("PESEL 44051401359, email jan@example.pl.")
        assert "44051401359" not in result.text
        assert "jan@example.pl" not in result.text
        assert "[PESEL_001]" in result.text
        assert "[EMAIL_001]" in result.text

    def test_consistent_tokens_for_repeated_values_in_one_call(self) -> None:
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize("44051401359 pojawił się ponownie: 44051401359")
        assert result.text.count("[PESEL_001]") == 2
        assert len(result.matches) == 2

    def test_consistent_tokens_across_calls(self) -> None:
        mapping = Mapping()
        anon = Anonymizer(detectors=[PeselDetector()], mapping=mapping)
        first = anon.anonymize("PESEL 44051401359")
        second = anon.anonymize("Znów 44051401359")
        assert "[PESEL_001]" in first.text
        assert "[PESEL_001]" in second.text

    def test_different_values_get_different_tokens(self) -> None:
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize("Pierwszy 44051401359 i drugi 92010100003.")
        assert "[PESEL_001]" in result.text
        assert "[PESEL_002]" in result.text

    def test_unicode_passes_through(self) -> None:
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize("Ąćęłńóśźż 44051401359 ĄĆĘŁŃÓŚŹŻ")
        assert result.text == "Ąćęłńóśźż [PESEL_001] ĄĆĘŁŃÓŚŹŻ"

    def test_preserves_source_formatting_via_mapping(self) -> None:
        anon = Anonymizer(detectors=[NipDetector()], mapping=Mapping())
        result = anon.anonymize("NIP: 526-000-12-46.")
        assert result.text == "NIP: [NIP_001]."
        assert result.mapping.value_for("[NIP_001]") == "526-000-12-46"

    def test_returns_anonymize_result_shape(self) -> None:
        mapping = Mapping()
        anon = Anonymizer(detectors=[PeselDetector()], mapping=mapping)
        result = anon.anonymize("44051401359")
        assert isinstance(result, AnonymizeResult)
        assert isinstance(result.text, str)
        assert isinstance(result.matches, tuple)
        assert result.mapping is mapping

    def test_match_spans_refer_to_original_text(self) -> None:
        original = "Nowak ma PESEL 44051401359 i tyle."
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.anonymize(original)
        m = result.matches[0]
        assert original[m.start : m.end] == m.value

    def test_accepts_explicit_token_strategy(self) -> None:
        anon = Anonymizer(
            detectors=[PeselDetector()],
            mapping=Mapping(),
            strategy=Strategy.TOKEN,
        )
        assert anon.anonymize("44051401359").text == "[PESEL_001]"


class TestAnonymizerOverlapResolution:
    def test_same_span_priority_wins(self) -> None:
        # _XxxDetector appears first in the list -> higher priority.
        anon = Anonymizer(
            detectors=[_XxxDetector(), _XxxAliasDetector()],
            mapping=Mapping(),
        )
        result = anon.anonymize("XXX")
        assert len(result.matches) == 1
        assert result.matches[0].detector == "xxx"
        assert result.matches[0].type is PIIType.EMAIL

    def test_longer_match_wins_over_shorter(self) -> None:
        # _ShortAbcDetector matches "ABC", _LongAbcdefDetector matches "ABCDEF".
        # The longer one wins even though the short detector is first in priority.
        anon = Anonymizer(
            detectors=[_ShortAbcDetector(), _LongAbcdefDetector()],
            mapping=Mapping(),
        )
        result = anon.anonymize("ABCDEF")
        assert len(result.matches) == 1
        assert result.matches[0].detector == "long"
        assert result.matches[0].value == "ABCDEF"

    def test_non_overlapping_matches_all_kept(self) -> None:
        anon = Anonymizer(
            detectors=[_AaaDetector(), _BbbDetector()],
            mapping=Mapping(),
        )
        result = anon.anonymize("AAA BBB")
        assert len(result.matches) == 2
        values = {m.value for m in result.matches}
        assert values == {"AAA", "BBB"}

    def test_adjacent_matches_both_kept(self) -> None:
        anon = Anonymizer(
            detectors=[_AaaDetector(), _BbbDetector()],
            mapping=Mapping(),
        )
        result = anon.anonymize("AAABBB")
        assert len(result.matches) == 2
        # Order in the result is by start position.
        assert [(m.start, m.end) for m in result.matches] == [(0, 3), (3, 6)]


@pytest.fixture
def round_trip_mapping() -> Mapping:
    return Mapping()


class TestAnonymizerDetectMethod:
    def test_detect_returns_matches_without_allocating(self) -> None:
        mapping = Mapping()
        anon = Anonymizer(detectors=[PeselDetector()], mapping=mapping)
        matches = anon.detect("PESEL 44051401359")
        assert len(matches) == 1
        assert matches[0].value == "44051401359"
        assert len(mapping) == 0

    def test_detect_resolves_overlaps(self) -> None:
        anon = Anonymizer(
            detectors=[_ShortAbcDetector(), _LongAbcdefDetector()],
            mapping=Mapping(),
        )
        matches = anon.detect("ABCDEF")
        assert len(matches) == 1
        assert matches[0].value == "ABCDEF"


class TestAnonymizerIntegration:
    def test_multi_detector_replacement_order_is_by_start(
        self, round_trip_mapping: Mapping
    ) -> None:
        anon = Anonymizer(
            detectors=[PeselDetector(), EmailDetector(), NipDetector()],
            mapping=round_trip_mapping,
        )
        text = "NIP 526-000-12-46, PESEL 44051401359, email jan@example.pl."
        result = anon.anonymize(text)
        starts = [m.start for m in result.matches]
        assert starts == sorted(starts)
