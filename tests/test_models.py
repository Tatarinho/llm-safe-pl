"""Unit tests for the core data types."""

import json
from dataclasses import FrozenInstanceError

import pytest

from llm_safe_pl.models import AnonymizeResult, Mapping, Match, PIIType


class TestPIIType:
    def test_has_all_expected_members(self) -> None:
        expected = {
            "PESEL",
            "NIP",
            "REGON",
            "ID_CARD",
            "PASSPORT",
            "PHONE",
            "EMAIL",
            "IBAN",
            "CREDIT_CARD",
            "PERSON",
            "ORGANIZATION",
            "LOCATION",
        }
        assert {m.name for m in PIIType} == expected

    def test_values_are_lowercase_snake_case(self) -> None:
        for member in PIIType:
            assert member.value == member.name.lower()

    def test_is_str_subclass(self) -> None:
        assert isinstance(PIIType.PESEL, str)
        assert PIIType.PESEL == "pesel"


class TestMatch:
    def test_fields(self) -> None:
        m = Match(type=PIIType.PESEL, value="44051401359", start=0, end=11, detector="pesel")
        assert m.type is PIIType.PESEL
        assert m.value == "44051401359"
        assert m.start == 0
        assert m.end == 11
        assert m.detector == "pesel"

    def test_is_frozen(self) -> None:
        m = Match(type=PIIType.EMAIL, value="a@b.pl", start=0, end=6, detector="email")
        with pytest.raises(FrozenInstanceError):
            m.value = "other"  # type: ignore[misc]

    def test_is_hashable_and_equal_by_value(self) -> None:
        m1 = Match(type=PIIType.NIP, value="1234567890", start=0, end=10, detector="nip")
        m2 = Match(type=PIIType.NIP, value="1234567890", start=0, end=10, detector="nip")
        assert m1 == m2
        assert hash(m1) == hash(m2)
        assert {m1, m2} == {m1}


class TestMapping:
    def test_empty_on_construction(self) -> None:
        assert len(Mapping()) == 0

    def test_token_for_new_value_allocates_counter(self) -> None:
        m = Mapping()
        assert m.token_for("Jan Kowalski", PIIType.PERSON) == "[PERSON_001]"
        assert m.token_for("Anna Nowak", PIIType.PERSON) == "[PERSON_002]"

    def test_token_for_same_value_returns_same_token(self) -> None:
        m = Mapping()
        first = m.token_for("44051401359", PIIType.PESEL)
        second = m.token_for("44051401359", PIIType.PESEL)
        assert first == second == "[PESEL_001]"
        assert len(m) == 1

    def test_counters_are_independent_per_type(self) -> None:
        m = Mapping()
        assert m.token_for("jan@example.pl", PIIType.EMAIL) == "[EMAIL_001]"
        assert m.token_for("44051401359", PIIType.PESEL) == "[PESEL_001]"

    def test_same_value_different_type_gets_different_token(self) -> None:
        m = Mapping()
        t1 = m.token_for("123", PIIType.PESEL)
        t2 = m.token_for("123", PIIType.NIP)
        assert t1 != t2

    def test_value_for_returns_original(self) -> None:
        m = Mapping()
        m.token_for("44051401359", PIIType.PESEL)
        assert m.value_for("[PESEL_001]") == "44051401359"

    def test_value_for_unknown_token_returns_none(self) -> None:
        assert Mapping().value_for("[PESEL_999]") is None

    def test_counter_padding_three_digits(self) -> None:
        m = Mapping()
        for i in range(1, 12):
            m.token_for(f"v{i}", PIIType.PESEL)
        assert m.value_for("[PESEL_009]") == "v9"
        assert m.value_for("[PESEL_011]") == "v11"

    def test_counter_grows_past_three_digits(self) -> None:
        m = Mapping()
        for i in range(1, 1002):
            m.token_for(f"v{i}", PIIType.PESEL)
        assert m.value_for("[PESEL_1000]") == "v1000"
        assert m.value_for("[PESEL_1001]") == "v1001"

    def test_dict_round_trip_preserves_tokens_and_counters(self) -> None:
        m = Mapping()
        m.token_for("Jan", PIIType.PERSON)
        m.token_for("44051401359", PIIType.PESEL)
        restored = Mapping.from_dict(m.to_dict())
        assert restored.value_for("[PERSON_001]") == "Jan"
        assert restored.value_for("[PESEL_001]") == "44051401359"
        assert restored.token_for("Anna", PIIType.PERSON) == "[PERSON_002]"

    def test_json_round_trip_preserves_unicode(self) -> None:
        m = Mapping()
        m.token_for("Żółć", PIIType.PERSON)
        restored = Mapping.from_json(m.to_json())
        assert restored.value_for("[PERSON_001]") == "Żółć"

    def test_from_dict_rejects_unknown_schema_version(self) -> None:
        with pytest.raises(ValueError, match="schema version"):
            Mapping.from_dict({"schema_version": 999, "entries": [], "counters": {}})

    def test_from_dict_rejects_missing_schema_version(self) -> None:
        with pytest.raises(ValueError, match="schema version"):
            Mapping.from_dict({"entries": [], "counters": {}})

    def test_to_dict_includes_schema_version(self) -> None:
        assert Mapping().to_dict()["schema_version"] == Mapping.SCHEMA_VERSION

    def test_to_json_is_parseable(self) -> None:
        m = Mapping()
        m.token_for("Jan", PIIType.PERSON)
        parsed = json.loads(m.to_json())
        assert parsed["entries"][0]["value"] == "Jan"
        assert parsed["entries"][0]["token"] == "[PERSON_001]"


class TestAnonymizeResult:
    def test_fields(self) -> None:
        mapping = Mapping()
        mapping.token_for("Jan", PIIType.PERSON)
        match = Match(type=PIIType.PERSON, value="Jan", start=0, end=3, detector="ner")
        result = AnonymizeResult(text="[PERSON_001]", mapping=mapping, matches=(match,))
        assert result.text == "[PERSON_001]"
        assert result.mapping is mapping
        assert result.matches == (match,)

    def test_is_frozen(self) -> None:
        result = AnonymizeResult(text="x", mapping=Mapping(), matches=())
        with pytest.raises(FrozenInstanceError):
            result.text = "y"  # type: ignore[misc]

    def test_matches_is_tuple(self) -> None:
        result = AnonymizeResult(text="x", mapping=Mapping(), matches=())
        assert isinstance(result.matches, tuple)
