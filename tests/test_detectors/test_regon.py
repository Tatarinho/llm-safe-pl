"""Tests for RegonDetector (9- and 14-digit forms)."""

import pytest

from llm_safe_pl.detectors.regon import RegonDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> RegonDetector:
    return RegonDetector()


class TestRegonDetector:
    def test_metadata(self, detector: RegonDetector) -> None:
        assert detector.name == "regon"
        assert detector.pii_type is PIIType.REGON

    def test_detects_valid_9_digit(self, detector: RegonDetector) -> None:
        matches = list(detector.detect("123456785"))
        assert len(matches) == 1
        assert matches[0].value == "123456785"

    def test_detects_9_digit_in_context(self, detector: RegonDetector) -> None:
        text = "REGON 123456785 w rejestrze."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "123456785"

    def test_rejects_invalid_9_digit(self, detector: RegonDetector) -> None:
        assert list(detector.detect("123456784")) == []

    def test_rejects_wrong_length(self, detector: RegonDetector) -> None:
        assert list(detector.detect("12345678")) == []  # 8
        assert list(detector.detect("1234567890")) == []  # 10
        assert list(detector.detect("1234567890123")) == []  # 13
        assert list(detector.detect("123456789012345")) == []  # 15

    def test_detects_valid_14_digit(self, detector: RegonDetector) -> None:
        # Build a valid 14-digit REGON from a valid 9-digit prefix.
        from llm_safe_pl.validators.checksum import _REGON_14_WEIGHTS

        body13 = "1234567850000"
        digits = [int(c) for c in body13]
        check = sum(d * w for d, w in zip(digits, _REGON_14_WEIGHTS, strict=True)) % 11
        if check == 10:
            check = 0
        full = body13 + str(check)
        assert len(full) == 14
        matches = list(detector.detect(full))
        assert len(matches) == 1
        assert matches[0].value == full

    def test_rejects_invalid_14_digit(self, detector: RegonDetector) -> None:
        assert list(detector.detect("12345678400000")) == []

    def test_multiple_matches(self, detector: RegonDetector) -> None:
        text = "REGONs: 123456785 oraz 987654326"
        matches = list(detector.detect(text))
        assert [m.value for m in matches] == ["123456785", "987654326"]

    def test_empty_text(self, detector: RegonDetector) -> None:
        assert list(detector.detect("")) == []
