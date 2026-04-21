"""Tests for IdCardDetector (3 letters + 6 digits)."""

import pytest

from llm_safe_pl.detectors.id_card import IdCardDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> IdCardDetector:
    return IdCardDetector()


class TestIdCardDetector:
    def test_metadata(self, detector: IdCardDetector) -> None:
        assert detector.name == "id_card"
        assert detector.pii_type is PIIType.ID_CARD

    def test_detects_valid_shape(self, detector: IdCardDetector) -> None:
        matches = list(detector.detect("ABC123456"))
        assert len(matches) == 1
        assert matches[0].value == "ABC123456"
        assert (matches[0].start, matches[0].end) == (0, 9)

    def test_detects_in_context(self, detector: IdCardDetector) -> None:
        text = "Dowód: ABC123456 wydany 2020."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "ABC123456"

    def test_rejects_lowercase_letters(self, detector: IdCardDetector) -> None:
        assert list(detector.detect("abc123456")) == []

    def test_rejects_wrong_letter_count(self, detector: IdCardDetector) -> None:
        assert list(detector.detect("AB123456")) == []  # 2 letters
        assert list(detector.detect("ABCD123456")) == []  # 4 letters

    def test_rejects_wrong_digit_count(self, detector: IdCardDetector) -> None:
        assert list(detector.detect("ABC12345")) == []
        assert list(detector.detect("ABC1234567")) == []

    def test_multiple_matches(self, detector: IdCardDetector) -> None:
        text = "Dokumenty: ABC123456 i XYZ987654."
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["ABC123456", "XYZ987654"]

    def test_empty_text(self, detector: IdCardDetector) -> None:
        assert list(detector.detect("")) == []
