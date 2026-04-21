"""Tests for PhoneDetector."""

import pytest

from llm_safe_pl.detectors.phone import PhoneDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> PhoneDetector:
    return PhoneDetector()


class TestPhoneDetector:
    def test_metadata(self, detector: PhoneDetector) -> None:
        assert detector.name == "phone"
        assert detector.pii_type is PIIType.PHONE

    @pytest.mark.parametrize(
        "phone",
        [
            "600123456",
            "600 123 456",
            "600-123-456",
            "+48600123456",
            "+48 600 123 456",
            "+48-600-123-456",
        ],
    )
    def test_detects_common_formats(self, detector: PhoneDetector, phone: str) -> None:
        matches = list(detector.detect(phone))
        assert len(matches) == 1
        assert matches[0].value == phone

    def test_detects_in_context(self, detector: PhoneDetector) -> None:
        text = "Zadzwoń pod +48 600 123 456 lub napisz."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "+48 600 123 456"

    def test_rejects_embedded_in_longer_digit_run(self, detector: PhoneDetector) -> None:
        assert list(detector.detect("1234567890")) == []
        assert list(detector.detect("12345678901234567")) == []

    def test_rejects_too_short(self, detector: PhoneDetector) -> None:
        assert list(detector.detect("12345678")) == []

    def test_multiple_matches(self, detector: PhoneDetector) -> None:
        text = "Tel 600 123 456, drugi: +48 700 222 333"
        matches = list(detector.detect(text))
        assert len(matches) == 2
        assert "600 123 456" in matches[0].value
        assert "700 222 333" in matches[1].value

    def test_empty_text(self, detector: PhoneDetector) -> None:
        assert list(detector.detect("")) == []
