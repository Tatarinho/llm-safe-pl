"""Tests covering the security/hardening changes from focused-review.md.

Groups: Mapping.from_dict validation, Shield input-size guard and reset,
Anonymizer detector-name collision and strategy rejection, Detector
subclass enforcement.
"""

from __future__ import annotations

import re
from typing import ClassVar

import pytest

from llm_safe_pl.anonymizer import Anonymizer
from llm_safe_pl.detectors.base import RegexDetector
from llm_safe_pl.detectors.pesel import PeselDetector
from llm_safe_pl.models import Mapping, PIIType
from llm_safe_pl.shield import Shield
from llm_safe_pl.strategies import Strategy

# ---- Mapping.from_dict validation ------------------------------------------


def _baseline() -> dict:
    return {
        "schema_version": 1,
        "counters": {"pesel": 1},
        "entries": [{"token": "[PESEL_001]", "type": "pesel", "value": "44051401359"}],
    }


class TestMappingFromDictValidation:
    def test_baseline_round_trips(self) -> None:
        m = Mapping.from_dict(_baseline())
        assert m.value_for("[PESEL_001]") == "44051401359"

    def test_rejects_non_dict(self) -> None:
        with pytest.raises(ValueError, match="expected a dict"):
            Mapping.from_dict([])  # type: ignore[arg-type]

    def test_rejects_wrong_schema_version(self) -> None:
        data = _baseline()
        data["schema_version"] = 2
        with pytest.raises(ValueError, match="schema version"):
            Mapping.from_dict(data)

    def test_rejects_missing_entries_field(self) -> None:
        data = _baseline()
        del data["entries"]
        with pytest.raises(ValueError, match="entries"):
            Mapping.from_dict(data)

    def test_rejects_token_with_wrong_shape(self) -> None:
        data = _baseline()
        data["entries"][0]["token"] = "garbage"
        with pytest.raises(ValueError, match="shape"):
            Mapping.from_dict(data)

    def test_rejects_token_prefix_type_mismatch(self) -> None:
        data = _baseline()
        data["entries"][0]["token"] = "[NIP_001]"  # token says NIP but type says pesel
        with pytest.raises(ValueError, match="prefix does not match"):
            Mapping.from_dict(data)

    def test_rejects_counter_below_observed_max(self) -> None:
        data = _baseline()
        data["counters"]["pesel"] = 0  # but [PESEL_001] is in entries
        with pytest.raises(ValueError, match="counter"):
            Mapping.from_dict(data)

    def test_rejects_negative_counter(self) -> None:
        data = _baseline()
        data["counters"]["pesel"] = -1
        with pytest.raises(ValueError, match="non-negative"):
            Mapping.from_dict(data)

    def test_rejects_string_counter(self) -> None:
        data = _baseline()
        data["counters"]["pesel"] = "1"  # type: ignore[assignment]
        with pytest.raises(ValueError, match="non-negative int"):
            Mapping.from_dict(data)

    def test_rejects_unknown_pii_type(self) -> None:
        data = _baseline()
        data["entries"][0]["type"] = "ssn"
        with pytest.raises(ValueError):
            Mapping.from_dict(data)

    def test_rejects_non_string_value(self) -> None:
        data = _baseline()
        data["entries"][0]["value"] = 12345  # type: ignore[assignment]
        with pytest.raises(ValueError, match="must be strings"):
            Mapping.from_dict(data)


# ---- Anonymizer constructor enforcement -----------------------------------


class _DupADetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.PESEL
    name: ClassVar[str] = "dup"
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"AAA")


class _DupBDetector(RegexDetector):
    pii_type: ClassVar[PIIType] = PIIType.NIP
    name: ClassVar[str] = "dup"  # same name as the one above
    pattern: ClassVar[re.Pattern[str]] = re.compile(r"BBB")


class TestAnonymizerConstructor:
    def test_rejects_duplicate_detector_names(self) -> None:
        with pytest.raises(ValueError, match="Duplicate detector name"):
            Anonymizer(
                detectors=[_DupADetector(), _DupBDetector()],
                mapping=Mapping(),
            )

    def test_rejects_unimplemented_strategy(self) -> None:
        # Forge an enum-like value that isn't TOKEN.
        with pytest.raises(ValueError, match="not implemented"):

            class _Fake:
                pass

            Anonymizer(
                detectors=[PeselDetector()],
                mapping=Mapping(),
                strategy=_Fake(),  # type: ignore[arg-type]
            )

    def test_accepts_token_strategy_explicitly(self) -> None:
        # Should not raise.
        Anonymizer(
            detectors=[PeselDetector()],
            mapping=Mapping(),
            strategy=Strategy.TOKEN,
        )

    def test_detect_returns_list(self) -> None:
        # Anonymizer is the internal/mutable-list path; Shield.detect is the
        # public-immutable-tuple path. Both must remain in their roles.
        anon = Anonymizer(detectors=[PeselDetector()], mapping=Mapping())
        result = anon.detect("PESEL 44051401359")
        assert isinstance(result, list)


# ---- Shield input-size guard + reset() -------------------------------------


class TestShieldHardening:
    def test_anonymize_respects_max_input_bytes(self) -> None:
        shield = Shield(max_input_bytes=10)
        with pytest.raises(ValueError, match="max_input_bytes"):
            shield.anonymize("This is far longer than 10 bytes of text")

    def test_detect_respects_max_input_bytes(self) -> None:
        shield = Shield(max_input_bytes=10)
        with pytest.raises(ValueError, match="max_input_bytes"):
            shield.detect("This is far longer than 10 bytes of text")

    def test_no_guard_by_default(self) -> None:
        shield = Shield()
        # Should not raise on a 10 KiB input.
        shield.anonymize("x" * 10240)

    def test_negative_max_input_bytes_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            Shield(max_input_bytes=-1)

    def test_reset_clears_mapping(self) -> None:
        shield = Shield()
        shield.anonymize("PESEL 44051401359")
        assert len(shield.mapping) == 1
        shield.reset()
        assert len(shield.mapping) == 0

    def test_reset_preserves_detector_list(self) -> None:
        shield = Shield(detectors=[PeselDetector()])
        result_a = shield.anonymize("PESEL 44051401359 i email jan@example.pl")
        # Email is NOT in the custom detector list, so it should not be touched.
        assert "jan@example.pl" in result_a.text
        shield.reset()
        result_b = shield.anonymize("PESEL 44051401359 i email jan@example.pl")
        assert "jan@example.pl" in result_b.text  # still no email detector


# ---- Detector __init_subclass__ enforcement -------------------------------


class TestDetectorInitSubclass:
    def test_concrete_detector_without_pii_type_rejected(self) -> None:
        with pytest.raises(TypeError, match="pii_type"):

            class _Bad(RegexDetector):
                # Missing pii_type intentionally
                name: ClassVar[str] = "bad"
                pattern: ClassVar[re.Pattern[str]] = re.compile(r"x")

    def test_concrete_detector_without_name_rejected(self) -> None:
        with pytest.raises(TypeError, match="name"):

            class _Bad(RegexDetector):
                pii_type: ClassVar[PIIType] = PIIType.PESEL
                # Missing name intentionally
                pattern: ClassVar[re.Pattern[str]] = re.compile(r"x")

    def test_regex_detector_helper_class_passes(self) -> None:
        # Re-importing the abstract helper must not raise.
        assert RegexDetector.__name__ == "RegexDetector"
