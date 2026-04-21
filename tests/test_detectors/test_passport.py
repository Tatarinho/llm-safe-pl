"""Tests for PassportDetector (2 letters + 7 digits)."""

import pytest

from llm_safe_pl.detectors.passport import PassportDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> PassportDetector:
    return PassportDetector()


class TestPassportDetector:
    def test_metadata(self, detector: PassportDetector) -> None:
        assert detector.name == "passport"
        assert detector.pii_type is PIIType.PASSPORT

    def test_detects_valid_shape(self, detector: PassportDetector) -> None:
        matches = list(detector.detect("AB1234567"))
        assert len(matches) == 1
        assert matches[0].value == "AB1234567"

    def test_detects_in_context(self, detector: PassportDetector) -> None:
        text = "Paszport AB1234567 wygasa."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "AB1234567"

    def test_rejects_lowercase(self, detector: PassportDetector) -> None:
        assert list(detector.detect("ab1234567")) == []

    def test_rejects_wrong_letter_count(self, detector: PassportDetector) -> None:
        assert list(detector.detect("A1234567")) == []
        assert list(detector.detect("ABC1234567")) == []

    def test_rejects_wrong_digit_count(self, detector: PassportDetector) -> None:
        assert list(detector.detect("AB123456")) == []
        assert list(detector.detect("AB12345678")) == []

    def test_multiple_matches(self, detector: PassportDetector) -> None:
        text = "Paszporty: AB1234567, CD9876543"
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["AB1234567", "CD9876543"]

    def test_empty_text(self, detector: PassportDetector) -> None:
        assert list(detector.detect("")) == []
