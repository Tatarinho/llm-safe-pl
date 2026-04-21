"""Tests for the Shield facade."""

import pytest

from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import AnonymizeResult, Mapping, Match, PIIType
from llm_safe_pl.shield import Shield
from llm_safe_pl.strategies import Strategy


class TestShieldConstruction:
    def test_default_construction_allocates_fresh_mapping(self) -> None:
        shield = Shield()
        assert isinstance(shield.mapping, Mapping)
        assert len(shield.mapping) == 0

    def test_accepts_preloaded_mapping(self) -> None:
        m = Mapping()
        m.token_for("seed", PIIType.PERSON)
        shield = Shield(mapping=m)
        assert shield.mapping is m
        assert len(shield.mapping) == 1

    def test_accepts_custom_detector_list(self) -> None:
        shield = Shield(detectors=[PeselDetector()])
        result = shield.anonymize("Email jan@x.pl i PESEL 44051401359.")
        assert "jan@x.pl" in result.text
        assert "[PESEL_001]" in result.text

    def test_defaults_to_default_detectors(self) -> None:
        shield = Shield()
        result = shield.anonymize("Email jan@x.pl i PESEL 44051401359.")
        assert "jan@x.pl" not in result.text
        assert "44051401359" not in result.text

    def test_accepts_strategy_argument(self) -> None:
        shield = Shield(strategy=Strategy.TOKEN)
        assert shield.anonymize("44051401359").text == "[PESEL_001]"


class TestShieldAnonymize:
    def test_returns_anonymize_result(self) -> None:
        shield = Shield()
        result = shield.anonymize("PESEL 44051401359")
        assert isinstance(result, AnonymizeResult)

    def test_result_mapping_is_shield_mapping(self) -> None:
        shield = Shield()
        result = shield.anonymize("PESEL 44051401359")
        assert result.mapping is shield.mapping

    def test_consistent_tokens_across_calls(self) -> None:
        shield = Shield()
        r1 = shield.anonymize("PESEL 44051401359")
        r2 = shield.anonymize("Znów 44051401359")
        assert "[PESEL_001]" in r1.text
        assert "[PESEL_001]" in r2.text


class TestShieldDeanonymize:
    def test_uses_shield_mapping_by_default(self) -> None:
        shield = Shield()
        r = shield.anonymize("PESEL 44051401359")
        restored = shield.deanonymize(r.text)
        assert restored == "PESEL 44051401359"

    def test_accepts_explicit_mapping(self) -> None:
        shield1 = Shield()
        r = shield1.anonymize("PESEL 44051401359")
        shield2 = Shield()  # fresh mapping
        restored = shield2.deanonymize(r.text, r.mapping)
        assert restored == "PESEL 44051401359"

    def test_unknown_tokens_left_in_place(self) -> None:
        shield = Shield()
        shield.anonymize("PESEL 44051401359")
        restored = shield.deanonymize("[PESEL_001] i [PESEL_999]")
        assert "44051401359" in restored
        assert "[PESEL_999]" in restored


class TestShieldDetect:
    def test_returns_matches_as_tuple(self) -> None:
        shield = Shield()
        matches = shield.detect("PESEL 44051401359")
        assert isinstance(matches, tuple)
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].value == "44051401359"

    def test_does_not_allocate_tokens(self) -> None:
        shield = Shield()
        shield.detect("PESEL 44051401359")
        assert len(shield.mapping) == 0

    def test_matches_sorted_by_start(self) -> None:
        shield = Shield()
        text = "jan@a.pl 44051401359 anna@b.pl"
        matches = shield.detect(text)
        starts = [m.start for m in matches]
        assert starts == sorted(starts)

    def test_detect_then_anonymize_allocates_tokens_once(self) -> None:
        shield = Shield()
        shield.detect("PESEL 44051401359")
        assert len(shield.mapping) == 0
        shield.anonymize("PESEL 44051401359")
        assert len(shield.mapping) == 1

    def test_detect_on_empty_text(self) -> None:
        shield = Shield()
        assert shield.detect("") == ()

    def test_detect_finds_multiple_types(self) -> None:
        shield = Shield()
        matches = shield.detect("PESEL 44051401359 email jan@example.pl")
        types = {m.type for m in matches}
        assert PIIType.PESEL in types
        assert PIIType.EMAIL in types


class TestShieldRoundTrip:
    @pytest.mark.parametrize(
        "original",
        [
            "Jan ma PESEL 44051401359.",
            "Email jan@example.pl, NIP 526-000-12-46.",
            "Tel +48 600 123 456, karta 4532015112830366.",
            "Plain text with no PII at all.",
            "",
        ],
    )
    def test_roundtrip_matches_original(self, original: str) -> None:
        shield = Shield()
        r = shield.anonymize(original)
        restored = shield.deanonymize(r.text)
        assert restored == original
