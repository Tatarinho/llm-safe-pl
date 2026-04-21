"""Tests for CreditCardDetector (Luhn-validated, multiple formats)."""

import pytest

from llm_safe_pl.detectors.credit_card import CreditCardDetector
from llm_safe_pl.models import PIIType


@pytest.fixture
def detector() -> CreditCardDetector:
    return CreditCardDetector()


class TestCreditCardDetector:
    def test_metadata(self, detector: CreditCardDetector) -> None:
        assert detector.name == "credit_card"
        assert detector.pii_type is PIIType.CREDIT_CARD

    def test_detects_bare_visa(self, detector: CreditCardDetector) -> None:
        matches = list(detector.detect("4532015112830366"))
        assert len(matches) == 1
        assert matches[0].value == "4532015112830366"

    def test_detects_dashed_visa(self, detector: CreditCardDetector) -> None:
        matches = list(detector.detect("4532-0151-1283-0366"))
        assert len(matches) == 1
        assert matches[0].value == "4532-0151-1283-0366"

    def test_detects_spaced_visa(self, detector: CreditCardDetector) -> None:
        matches = list(detector.detect("4532 0151 1283 0366"))
        assert len(matches) == 1
        assert matches[0].value == "4532 0151 1283 0366"

    def test_detects_amex_bare(self, detector: CreditCardDetector) -> None:
        matches = list(detector.detect("378282246310005"))
        assert len(matches) == 1
        assert matches[0].value == "378282246310005"

    def test_detects_amex_spaced(self, detector: CreditCardDetector) -> None:
        matches = list(detector.detect("3782 822463 10005"))
        assert len(matches) == 1
        assert matches[0].value == "3782 822463 10005"

    def test_detects_in_context(self, detector: CreditCardDetector) -> None:
        text = "Karta: 4532 0151 1283 0366 ważna do 2030."
        matches = list(detector.detect(text))
        assert len(matches) == 1
        assert matches[0].value == "4532 0151 1283 0366"

    def test_rejects_invalid_luhn(self, detector: CreditCardDetector) -> None:
        assert list(detector.detect("4532015112830367")) == []
        assert list(detector.detect("4532-0151-1283-0367")) == []

    def test_rejects_too_short(self, detector: CreditCardDetector) -> None:
        assert list(detector.detect("123456789012")) == []  # 12 digits

    def test_rejects_too_long(self, detector: CreditCardDetector) -> None:
        assert list(detector.detect("12345678901234567890")) == []  # 20 digits

    def test_empty_text(self, detector: CreditCardDetector) -> None:
        assert list(detector.detect("")) == []
